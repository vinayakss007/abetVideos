"""Video assembly service using MoviePy and FFmpeg."""

import asyncio
import logging
import os
import shutil
import uuid
from pathlib import Path
from typing import Optional

from moviepy import (
    AudioFileClip,
    ColorClip,
    CompositeVideoClip,
    ImageClip,
    VideoFileClip,
    concatenate_videoclips,
)
from PIL import Image

from app.config import settings
from app.models.schemas import (
    AssembleVideoRequest,
    BitratePreset,
    CodecPreset,
    FPSOption,
    MediaItem,
    MediaType,
    OutputFormat,
    Resolution,
    SceneMedia,
    TTSResult,
    VideoFormat,
    VideoQualitySettings,
    VideoResult,
    VideoScript,
)

logger = logging.getLogger(__name__)

# Resolution presets
RESOLUTIONS = {
    VideoFormat.shorts: (1080, 1920),  # Vertical 9:16
    VideoFormat.landscape: (1920, 1080),  # Horizontal 16:9
}

# Resolution enum to pixel dimensions (landscape orientation)
RESOLUTION_MAP = {
    Resolution.res_480p: (854, 480),
    Resolution.res_720p: (1280, 720),
    Resolution.res_1080p: (1920, 1080),
    Resolution.res_4k: (3840, 2160),
}

# Bitrate preset to actual bitrate string
BITRATE_MAP = {
    BitratePreset.low: "1M",
    BitratePreset.medium: "4M",
    BitratePreset.high: "8M",
}

# FPS enum to integer
FPS_MAP = {
    FPSOption.fps_24: 24,
    FPSOption.fps_30: 30,
    FPSOption.fps_60: 60,
}


def _get_resolution(
    format: VideoFormat,
    quality_settings: Optional["VideoQualitySettings"] = None,
) -> tuple[int, int]:
    """Get width, height for a video format, optionally using quality settings."""
    if quality_settings is not None:
        w, h = RESOLUTION_MAP[quality_settings.resolution]
        # Swap width/height for shorts (vertical) format
        if format == VideoFormat.shorts:
            return (h, w)
        return (w, h)
    return RESOLUTIONS[format]


def _create_background_clip(
    duration: float, width: int, height: int
) -> ColorClip:
    """Create a black background clip."""
    return ColorClip(size=(width, height), color=(0, 0, 0), duration=duration)


def _loop_clip(clip, target_duration: float):
    """Loop a clip to match target duration by concatenating copies."""
    if clip.duration >= target_duration:
        return clip.subclipped(0, target_duration)

    clips = []
    total = 0.0
    while total < target_duration:
        clips.append(clip)
        total += clip.duration

    looped = concatenate_videoclips(clips, method="chain")
    return looped.subclipped(0, target_duration)


def _create_image_scene(
    image_path: str, audio_path: str, width: int, height: int
) -> CompositeVideoClip:
    """Create a scene from an image and audio.

    The image is displayed for the duration of the audio, resized to fit
    the target resolution while maintaining aspect ratio.
    """
    audio = AudioFileClip(audio_path)
    duration = audio.duration

    # Load and resize image
    img_clip = ImageClip(image_path, duration=duration)

    # Resize to fit within target resolution while maintaining aspect ratio
    img_w, img_h = img_clip.size
    scale_w = width / img_w
    scale_h = height / img_h
    scale = min(scale_w, scale_h)
    img_clip = img_clip.resized(scale)

    # Center the image on a background
    bg = _create_background_clip(duration, width, height)
    scene = CompositeVideoClip(
        [bg, img_clip.with_position("center")],
        size=(width, height),
    )

    scene = scene.with_audio(audio)
    return scene


def _create_video_scene(
    video_path: str, audio_path: str, width: int, height: int
) -> CompositeVideoClip:
    """Create a scene from a video clip and audio.

    The video is trimmed or looped to match the audio duration,
    then resized to fit the target resolution.
    """
    audio = AudioFileClip(audio_path)
    duration = audio.duration

    video = VideoFileClip(video_path)

    # Loop or trim video to match audio duration
    video = _loop_clip(video, duration)

    # Resize to fit target resolution
    vid_w, vid_h = video.size
    scale_w = width / vid_w
    scale_h = height / vid_h
    scale = min(scale_w, scale_h)
    video = video.resized(scale)

    # Center on background
    bg = _create_background_clip(duration, width, height)
    scene = CompositeVideoClip(
        [bg, video.with_position("center")],
        size=(width, height),
    )

    scene = scene.with_audio(audio)
    return scene


def _create_gif_scene(
    gif_path: str, audio_path: str, width: int, height: int
) -> CompositeVideoClip:
    """Create a scene from a GIF and audio.

    The GIF is looped to match audio duration.
    """
    audio = AudioFileClip(audio_path)
    duration = audio.duration

    # Load GIF as video clip
    gif_clip = VideoFileClip(gif_path)

    # Loop to match audio duration
    gif_clip = _loop_clip(gif_clip, duration)

    # Resize
    gif_w, gif_h = gif_clip.size
    scale_w = width / gif_w
    scale_h = height / gif_h
    scale = min(scale_w, scale_h)
    gif_clip = gif_clip.resized(scale)

    # Center on background
    bg = _create_background_clip(duration, width, height)
    scene = CompositeVideoClip(
        [bg, gif_clip.with_position("center")],
        size=(width, height),
    )

    scene = scene.with_audio(audio)
    return scene


def _create_fallback_scene(
    audio_path: str, width: int, height: int
) -> ColorClip:
    """Create a fallback scene with just a colored background and audio."""
    audio = AudioFileClip(audio_path)
    duration = audio.duration

    bg = ColorClip(size=(width, height), color=(20, 20, 30), duration=duration)
    bg = bg.with_audio(audio)
    return bg


def _build_scene_clip(
    media: Optional[MediaItem],
    audio_path: str,
    width: int,
    height: int,
):
    """Build a scene clip from media and audio.

    Dispatches to the appropriate scene builder based on media type.
    Falls back to a plain background if no media is available.
    """
    if media is None or media.local_path is None:
        return _create_fallback_scene(audio_path, width, height)

    local_path = media.local_path

    if not os.path.exists(local_path):
        logger.warning(f"Media file not found: {local_path}, using fallback")
        return _create_fallback_scene(audio_path, width, height)

    try:
        if media.media_type == MediaType.video:
            return _create_video_scene(local_path, audio_path, width, height)
        elif media.media_type == MediaType.image:
            return _create_image_scene(local_path, audio_path, width, height)
        elif media.media_type == MediaType.gif:
            return _create_gif_scene(local_path, audio_path, width, height)
        else:
            return _create_fallback_scene(audio_path, width, height)
    except Exception as e:
        logger.warning(f"Error processing media {local_path}: {e}, using fallback")
        return _create_fallback_scene(audio_path, width, height)


def _cleanup_intermediate_files(
    tts_results: list[TTSResult], scene_media: list[SceneMedia]
) -> None:
    """Remove intermediate TTS audio and downloaded media files after assembly.

    Only removes files that exist and logs warnings on failure rather than
    raising exceptions, since the video has already been assembled.
    """
    # Collect directories to remove (parent dirs of scene media)
    dirs_to_remove: set[str] = set()

    # Remove TTS audio files
    for tts in tts_results:
        try:
            audio_path = Path(tts.audio_path)
            if audio_path.exists():
                audio_path.unlink()
                # Track parent dir for potential removal
                dirs_to_remove.add(str(audio_path.parent))
        except OSError as e:
            logger.warning(f"Failed to remove TTS file {tts.audio_path}: {e}")

    # Remove downloaded media files
    for sm in scene_media:
        for item in sm.media_items:
            if item.local_path:
                try:
                    media_path = Path(item.local_path)
                    if media_path.exists():
                        media_path.unlink()
                        dirs_to_remove.add(str(media_path.parent))
                except OSError as e:
                    logger.warning(f"Failed to remove media file {item.local_path}: {e}")

    # Remove empty parent directories
    for dir_path in dirs_to_remove:
        try:
            p = Path(dir_path)
            if p.exists() and p.is_dir() and not any(p.iterdir()):
                p.rmdir()
        except OSError:
            pass  # Directory not empty or already removed


async def assemble_video(
    script: VideoScript,
    tts_results: list[TTSResult],
    scene_media: list[SceneMedia],
    format: VideoFormat = VideoFormat.landscape,
    output_dir: Optional[str] = None,
    quality_settings: Optional[VideoQualitySettings] = None,
) -> VideoResult:
    """Assemble the final video from script, audio, and media.

    Args:
        script: The video script.
        tts_results: TTS audio results per scene.
        scene_media: Media items per scene.
        format: Video format (shorts or landscape).
        output_dir: Optional output directory override.
        quality_settings: Optional video quality settings for resolution, bitrate, etc.

    Returns:
        VideoResult with path to the assembled video.
    """
    width, height = _get_resolution(format, quality_settings)
    base_dir = Path(output_dir or settings.output_dir)

    # Determine output format extension
    output_ext = "mp4"
    if quality_settings is not None:
        output_ext = quality_settings.output_format.value

    video_id = uuid.uuid4().hex[:12]
    output_path = base_dir / "videos" / f"{video_id}.{output_ext}"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(
        f"Assembling video: {len(script.scenes)} scenes, "
        f"format: {format.value} ({width}x{height})"
    )

    # Build a lookup for TTS results and media by scene number
    tts_map = {r.scene_number: r for r in tts_results}
    media_map = {m.scene_number: m for m in scene_media}

    scene_clips = []

    for scene in script.scenes:
        tts = tts_map.get(scene.scene_number)
        if tts is None:
            logger.warning(f"No TTS for scene {scene.scene_number}, skipping")
            continue

        # Get the first available media item for this scene
        scene_media_data = media_map.get(scene.scene_number)
        media_item = None
        if scene_media_data and scene_media_data.media_items:
            # Find the first item with a local path
            for item in scene_media_data.media_items:
                if item.local_path and os.path.exists(item.local_path):
                    media_item = item
                    break

        clip = _build_scene_clip(media_item, tts.audio_path, width, height)
        scene_clips.append(clip)

    if not scene_clips:
        raise ValueError("No scene clips could be assembled")

    # Concatenate all scenes
    final = None
    try:
        if len(scene_clips) > 1:
            final = concatenate_videoclips(scene_clips, method="compose", padding=-0.5)
        else:
            final = scene_clips[0]

        # Determine write parameters based on quality settings
        write_fps = 24
        write_codec = "libx264"
        write_audio_codec = "aac"
        write_preset = "medium"
        write_bitrate = None

        if quality_settings is not None:
            write_fps = FPS_MAP[quality_settings.fps]
            write_preset = quality_settings.codec_preset.value

            # Determine bitrate
            if quality_settings.bitrate == BitratePreset.custom:
                write_bitrate = quality_settings.custom_bitrate
            else:
                write_bitrate = BITRATE_MAP.get(quality_settings.bitrate)

            # Determine codec based on output format
            if quality_settings.output_format == OutputFormat.webm:
                write_codec = "libvpx"
                write_audio_codec = "libvorbis"
            elif quality_settings.output_format == OutputFormat.avi:
                write_codec = "libx264"
                write_audio_codec = "aac"

        # Build write_videofile kwargs
        write_kwargs: dict = {
            "fps": write_fps,
            "codec": write_codec,
            "audio_codec": write_audio_codec,
            "preset": write_preset,
            "threads": 2,
            "logger": None,
        }
        if write_bitrate:
            write_kwargs["bitrate"] = write_bitrate

        # Write final video in a thread to avoid blocking the async event loop
        logger.info(f"Writing video to {output_path}...")
        await asyncio.to_thread(
            final.write_videofile,
            str(output_path),
            **write_kwargs,
        )

        total_duration = final.duration if hasattr(final, "duration") else 0
    finally:
        # Ensure all clips are closed even if write_videofile raises
        if final is not None:
            try:
                final.close()
            except Exception:
                pass
        for clip in scene_clips:
            try:
                clip.close()
            except Exception:
                pass

    # Clean up intermediate files (media and TTS audio)
    _cleanup_intermediate_files(tts_results, scene_media)

    logger.info(f"Video assembled: {output_path} ({total_duration:.1f}s)")

    return VideoResult(
        video_id=video_id,
        video_path=str(output_path),
        duration_seconds=total_duration,
        scenes_count=len(scene_clips),
        format=format,
    )
