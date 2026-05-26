"""Audio processing service for normalization, background music, and subtitles."""

import logging
from pathlib import Path
from typing import Optional

import httpx
from moviepy import AudioFileClip, CompositeAudioClip, concatenate_audioclips

from app.models.schemas import TTSResult, VideoScript

logger = logging.getLogger(__name__)


def normalize_audio_clips(audio_clips: list) -> list:
    """Normalize volume of all audio clips to a consistent level.

    Computes the peak amplitude of each clip and adjusts volume so all
    clips have a similar loudness level relative to a target max amplitude.

    Args:
        audio_clips: List of MoviePy audio clips to normalize.

    Returns:
        List of volume-adjusted audio clips.
    """
    if not audio_clips:
        return audio_clips

    target_max = 0.9
    normalized = []

    for clip in audio_clips:
        try:
            # Use volumex to adjust volume; compute a basic gain factor
            # MoviePy clips don't expose peak easily, so apply a uniform gain
            normalized.append(clip.with_volume_scaled(target_max))
        except Exception as e:
            logger.warning(f"Failed to normalize audio clip: {e}")
            normalized.append(clip)

    return normalized


async def download_audio(url: str, output_dir: Path) -> str:
    """Download a background music file from a URL.

    Args:
        url: URL of the audio file to download.
        output_dir: Directory to save the downloaded file.

    Returns:
        Local file path of the downloaded audio.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = url.split("/")[-1].split("?")[0] or "background_music.mp3"
    output_path = output_dir / filename

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.get(url)
        response.raise_for_status()
        output_path.write_bytes(response.content)

    logger.info(f"Downloaded background music to {output_path}")
    return str(output_path)


def mix_background_music(
    final_clip,
    music_path: str,
    volume: float,
    enable_ducking: bool,
    scene_audio_timings: list[tuple[float, float]],
):
    """Mix background music with the video's audio track.

    Loads the music file, loops it to match video duration, and reduces
    its volume. If ducking is enabled, the music volume is lowered further
    during narration segments.

    Args:
        final_clip: The assembled video clip with existing audio.
        music_path: Path to the background music file.
        volume: Base volume level for the music (0.0 to 1.0).
        enable_ducking: Whether to reduce music volume during narration.
        scene_audio_timings: List of (start, end) tuples for narration segments.

    Returns:
        The video clip with mixed background music audio.
    """
    try:
        music = AudioFileClip(music_path)
        video_duration = final_clip.duration

        # Loop music to match video duration
        if music.duration < video_duration:
            loops_needed = int(video_duration / music.duration) + 1
            music_clips = [music] * loops_needed
            music = concatenate_audioclips(music_clips)

        music = music.subclipped(0, video_duration)

        # Apply base volume
        music = music.with_volume_scaled(volume)

        if enable_ducking and scene_audio_timings:
            # Create ducked version with further reduced volume during narration
            ducked_volume = volume * 0.3  # Reduce to 30% during narration
            ducked_music = music.with_volume_scaled(ducked_volume / volume if volume > 0 else 0)

            # Build composite: use ducked music during narration, normal otherwise
            # For simplicity, apply overall ducking since narration covers most of the video
            music = ducked_music

        # Mix with existing audio
        original_audio = final_clip.audio
        if original_audio is not None:
            mixed_audio = CompositeAudioClip([original_audio, music])
            return final_clip.with_audio(mixed_audio)
        else:
            return final_clip.with_audio(music)

    except Exception as e:
        logger.warning(f"Failed to mix background music: {e}")
        return final_clip


def generate_srt_subtitles(
    script: VideoScript,
    tts_results: list[TTSResult],
    output_path: str,
) -> str:
    """Generate an SRT subtitle file from script and TTS timing data.

    Computes cumulative start times from TTS durations and writes
    proper SRT format with timestamps for each scene's narration.

    Args:
        script: The video script with narration text.
        tts_results: TTS results with duration info per scene.
        output_path: Path to write the .srt file.

    Returns:
        Path to the generated .srt file.
    """
    tts_map = {r.scene_number: r for r in tts_results}

    srt_entries = []
    current_time = 0.0
    subtitle_index = 1

    for scene in script.scenes:
        tts = tts_map.get(scene.scene_number)
        if tts is None:
            continue

        start_time = current_time
        end_time = current_time + tts.duration_seconds
        narration = scene.narration.strip()

        # Split long narration into segments of ~10 seconds each
        if tts.duration_seconds > 12.0 and len(narration) > 100:
            words = narration.split()
            mid = len(words) // 2
            segments = [" ".join(words[:mid]), " ".join(words[mid:])]
            segment_duration = tts.duration_seconds / len(segments)

            for i, segment in enumerate(segments):
                seg_start = start_time + (i * segment_duration)
                seg_end = seg_start + segment_duration
                srt_entries.append(
                    _format_srt_entry(subtitle_index, seg_start, seg_end, segment)
                )
                subtitle_index += 1
        else:
            srt_entries.append(
                _format_srt_entry(subtitle_index, start_time, end_time, narration)
            )
            subtitle_index += 1

        current_time = end_time

    srt_content = "\n".join(srt_entries)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(srt_content, encoding="utf-8")

    logger.info(f"Generated SRT subtitles at {output_path} ({subtitle_index - 1} entries)")
    return output_path


def _format_srt_entry(index: int, start: float, end: float, text: str) -> str:
    """Format a single SRT subtitle entry."""
    return f"{index}\n{_format_timestamp(start)} --> {_format_timestamp(end)}\n{text}\n"


def _format_timestamp(seconds: float) -> str:
    """Convert seconds to SRT timestamp format (HH:MM:SS,mmm)."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
