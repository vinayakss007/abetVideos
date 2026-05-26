"""Video editor service for applying edits to assembled videos."""

import base64
import json
import logging
import uuid
from io import BytesIO
from pathlib import Path
from typing import Optional

from moviepy import (
    AudioFileClip,
    CompositeVideoClip,
    VideoFileClip,
    concatenate_videoclips,
)
from PIL import Image, ImageDraw, ImageFont
import numpy as np

from app.models.schemas import EditInstruction, TextOverlayInstruction

logger = logging.getLogger(__name__)


def get_video_metadata(video_id: str) -> Optional[dict]:
    """Read metadata JSON for a given video_id.

    Args:
        video_id: The 12-character hex video identifier.

    Returns:
        Parsed metadata dict, or None if not found.
    """
    from app.config import settings

    meta_path = Path(settings.output_dir) / "videos" / f"{video_id}_meta.json"
    if not meta_path.exists():
        return None

    with open(meta_path, "r") as f:
        return json.load(f)


def extract_frame(video_path: str, timestamp: float) -> tuple[str, int, int]:
    """Extract a single frame from a video at the given timestamp.

    Args:
        video_path: Path to the video file.
        timestamp: Time in seconds to extract frame at.

    Returns:
        Tuple of (base64_jpeg_str, width, height).

    Raises:
        FileNotFoundError: If video file does not exist.
        ValueError: If timestamp is beyond video duration.
    """
    path = Path(video_path)
    if not path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    clip = None
    try:
        clip = VideoFileClip(video_path)

        if timestamp > clip.duration:
            raise ValueError(
                f"Timestamp {timestamp}s exceeds video duration {clip.duration}s"
            )

        # Get frame as numpy array
        frame_array = clip.get_frame(timestamp)

        # Convert to PIL Image
        img = Image.fromarray(frame_array.astype("uint8"), "RGB")
        width, height = img.size

        # Encode as JPEG base64
        buffer = BytesIO()
        img.save(buffer, format="JPEG", quality=85)
        buffer.seek(0)
        b64_str = base64.b64encode(buffer.read()).decode("utf-8")

        return b64_str, width, height
    finally:
        if clip is not None:
            try:
                clip.close()
            except Exception:
                pass


def _apply_text_overlay(
    frame: np.ndarray,
    overlay: TextOverlayInstruction,
    width: int,
    height: int,
) -> np.ndarray:
    """Apply a text overlay to a frame using PIL.

    Args:
        frame: Numpy array of the frame (RGB).
        overlay: The text overlay instruction.
        width: Frame width.
        height: Frame height.

    Returns:
        Modified frame as numpy array.
    """
    img = Image.fromarray(frame.astype("uint8"), "RGB")
    draw = ImageDraw.Draw(img)

    # Calculate position from percentage
    x_pos = int((overlay.x / 100.0) * width)
    y_pos = int((overlay.y / 100.0) * height)

    # Try to load a font at the specified size
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", overlay.font_size)
    except (OSError, IOError):
        try:
            font = ImageFont.truetype("/usr/share/fonts/TTF/DejaVuSans.ttf", overlay.font_size)
        except (OSError, IOError):
            font = ImageFont.load_default()

    # Parse color
    color = overlay.color if overlay.color else "#FFFFFF"

    draw.text((x_pos, y_pos), overlay.text, fill=color, font=font)

    return np.array(img)


def apply_edits(
    video_path: str,
    instructions: EditInstruction,
    output_dir: str,
) -> dict:
    """Apply edit instructions to a video and produce a new output.

    Handles scene reordering, trimming, text overlays, and audio level adjustments
    using MoviePy.

    Args:
        video_path: Path to the source video file.
        instructions: The edit instructions to apply.
        output_dir: Directory to write the edited video to.

    Returns:
        Dict with video_id, video_path, and duration_seconds.

    Raises:
        FileNotFoundError: If video file does not exist.
        ValueError: If instructions reference invalid scenes.
    """
    path = Path(video_path)
    if not path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    # Load video metadata to get scene boundaries
    video_id_src = path.stem  # e.g. "abc123def456"
    metadata = get_video_metadata(video_id_src)

    clip = None
    scene_clips = []
    final = None

    try:
        clip = VideoFileClip(video_path)

        # If we have metadata, split by scene durations
        if metadata and "scenes" in metadata:
            scenes_meta = metadata["scenes"]
            scene_boundaries = []
            current_time = 0.0
            for scene_info in scenes_meta:
                duration = scene_info.get("duration_seconds", 0)
                scene_boundaries.append((current_time, current_time + duration))
                current_time += duration

            # Determine scene order
            scene_order = instructions.scene_order
            if not scene_order:
                scene_order = [s["scene_number"] for s in scenes_meta]

            # Build trim lookup
            trim_map = {t.scene_number: t for t in instructions.trims}

            # Build audio level lookup
            audio_map = {a.scene_number: a.volume for a in instructions.audio_levels}

            # Build text overlay lookup (grouped by scene)
            overlay_map: dict[int, list[TextOverlayInstruction]] = {}
            for overlay in instructions.text_overlays:
                overlay_map.setdefault(overlay.scene_number, []).append(overlay)

            # Build media replacement lookup
            media_replacement_map = {r.scene_number: r for r in instructions.media_replacements}

            for scene_num in scene_order:
                # Find scene boundaries (scene_number is 1-indexed)
                idx = scene_num - 1
                if idx < 0 or idx >= len(scene_boundaries):
                    logger.warning(f"Scene {scene_num} out of range, skipping")
                    continue

                start, end = scene_boundaries[idx]

                # Apply trim if specified
                trim = trim_map.get(scene_num)
                if trim:
                    scene_start = start + trim.start_time
                    scene_end = start + trim.end_time
                    # Clamp to scene boundaries
                    scene_start = max(start, min(scene_start, end))
                    scene_end = max(scene_start, min(scene_end, end))
                else:
                    scene_start = start
                    scene_end = end

                if scene_end <= scene_start:
                    continue

                scene_clip = clip.subclipped(scene_start, scene_end)

                # Apply media replacement if specified
                replacement = media_replacement_map.get(scene_num)
                if replacement:
                    replacement_path = Path(replacement.media_url)
                    # Only replace if the media URL is a local file path that exists
                    if replacement_path.exists():
                        try:
                            duration_needed = scene_end - scene_start
                            replacement_clip = VideoFileClip(str(replacement_path))
                            # Trim replacement to match scene duration
                            if replacement_clip.duration > duration_needed:
                                replacement_clip = replacement_clip.subclipped(0, duration_needed)
                            # Keep the original audio if replacement has none
                            if replacement_clip.audio is None and scene_clip.audio is not None:
                                replacement_clip = replacement_clip.with_audio(scene_clip.audio)
                            scene_clip.close()
                            scene_clip = replacement_clip
                        except Exception as e:
                            logger.warning(f"Failed to apply media replacement for scene {scene_num}: {e}")
                    else:
                        logger.info(f"Media replacement for scene {scene_num} is a URL, skipping local replacement: {replacement.media_url}")

                # Apply audio level adjustment
                volume = audio_map.get(scene_num)
                if volume is not None and scene_clip.audio is not None:
                    scene_clip = scene_clip.with_volume_scaled(volume)

                # Apply text overlays using PIL-based frame modification
                overlays = overlay_map.get(scene_num, [])
                if overlays:
                    w, h = scene_clip.size

                    def make_frame_modifier(ovs, width, height):
                        def modify_frame(get_frame, t):
                            frame = get_frame(t)
                            for ov in ovs:
                                frame = _apply_text_overlay(frame, ov, width, height)
                            return frame
                        return modify_frame

                    scene_clip = scene_clip.transform(
                        make_frame_modifier(overlays, w, h)
                    )

                scene_clips.append(scene_clip)
        else:
            # No metadata - treat entire video as single scene
            scene_clips.append(clip)

        if not scene_clips:
            raise ValueError("No valid scenes to assemble after applying edits")

        # Concatenate scenes
        if len(scene_clips) > 1:
            final = concatenate_videoclips(scene_clips, method="compose")
        else:
            final = scene_clips[0]

        # Generate new video ID and write output
        new_video_id = uuid.uuid4().hex[:12]
        output_path = Path(output_dir) / "videos" / f"{new_video_id}.mp4"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        final.write_videofile(
            str(output_path),
            fps=24,
            codec="libx264",
            audio_codec="aac",
            preset="medium",
            threads=2,
            logger=None,
        )

        duration = final.duration if final else 0

        return {
            "video_id": new_video_id,
            "video_path": str(output_path),
            "duration_seconds": duration,
        }
    finally:
        if final is not None:
            try:
                final.close()
            except Exception:
                pass
        for sc in scene_clips:
            try:
                sc.close()
            except Exception:
                pass
        if clip is not None:
            try:
                clip.close()
            except Exception:
                pass
