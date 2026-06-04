"""Audio processing service for normalization, background music, and subtitles."""

import logging
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import httpx
import numpy as np
from moviepy import AudioFileClip, CompositeAudioClip, concatenate_audioclips

SAMPLE_RATE = 22050
TARGET_PEAK_AMPLITUDE = 0.9
MAX_GAIN_CLAMP = 5.0
DUCKING_RATIO = 0.3

from app.models.schemas import TTSResult, VideoScript

logger = logging.getLogger(__name__)

# Maximum allowed download size for background music (50 MB)
_MAX_MUSIC_DOWNLOAD_BYTES = 50 * 1024 * 1024

# Allowed content-type prefixes for audio files
_ALLOWED_AUDIO_CONTENT_TYPES = ("audio/", "application/octet-stream")


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

    normalized = []

    for clip in audio_clips:
        try:
            # Sample audio data to determine peak amplitude
            samples = clip.to_soundarray(fps=SAMPLE_RATE)
            peak = np.max(np.abs(samples))
            if peak > 0:
                gain = TARGET_PEAK_AMPLITUDE / peak
                # Clamp gain to avoid extreme amplification of very quiet clips
                gain = min(gain, MAX_GAIN_CLAMP)
                normalized.append(clip.with_volume_scaled(gain))
            else:
                normalized.append(clip)
        except Exception as e:
            logger.warning(f"Failed to normalize audio clip: {e}")
            normalized.append(clip)

    return normalized


async def download_audio(url: str, output_dir: Path) -> str:
    """Download a background music file from a URL.

    Validates the URL scheme (https only), checks Content-Type header,
    and enforces a size limit to prevent SSRF and resource exhaustion.

    Args:
        url: URL of the audio file to download (must be https).
        output_dir: Directory to save the downloaded file.

    Returns:
        Local file path of the downloaded audio.

    Raises:
        ValueError: If the URL scheme is not https, content-type is
            not audio, or size exceeds the limit.
    """
    # Validate URL scheme to prevent SSRF (only allow https)
    parsed = urlparse(url)
    if parsed.scheme not in ("https",):
        raise ValueError("Only https URLs are allowed for background music")
    if not parsed.hostname:
        raise ValueError("Invalid URL: no hostname")

    output_dir.mkdir(parents=True, exist_ok=True)
    filename = parsed.path.split("/")[-1].split("?")[0] or "background_music.mp3"
    output_path = output_dir / filename

    async with httpx.AsyncClient(timeout=60.0) as client:
        # Use a streaming request so we can check headers before downloading fully
        async with client.stream("GET", url) as response:
            response.raise_for_status()

            # Check content-type
            content_type = response.headers.get("content-type", "").lower()
            if not any(content_type.startswith(ct) for ct in _ALLOWED_AUDIO_CONTENT_TYPES):
                raise ValueError(
                    "Invalid content type for background music: expected audio/*"
                )

            # Check content-length if provided
            content_length = response.headers.get("content-length")
            if content_length and int(content_length) > _MAX_MUSIC_DOWNLOAD_BYTES:
                raise ValueError(
                    "Background music file too large (max 50 MB)"
                )

            # Download with size limit enforcement
            total_bytes = 0
            chunks = []
            async for chunk in response.aiter_bytes(chunk_size=65536):
                total_bytes += len(chunk)
                if total_bytes > _MAX_MUSIC_DOWNLOAD_BYTES:
                    raise ValueError(
                        "Background music file too large (max 50 MB)"
                    )
                chunks.append(chunk)

        output_path.write_bytes(b"".join(chunks))

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
    its volume. If ducking is enabled, the music volume is lowered during
    narration segments using time-varying gain based on scene_audio_timings.

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
            # Implement time-varying ducking: lower music during narration,
            # raise it between narration segments.
            ducking_ratio = DUCKING_RATIO  # Reduce to 30% during narration

            def _ducking_filter(get_frame, t):
                """Apply time-varying volume based on narration timings."""
                frame = get_frame(t)
                t_arr = np.atleast_1d(t)
                # Start with full volume (ones)
                gain = np.ones(len(t_arr))
                for start, end in scene_audio_timings:
                    mask = (t_arr >= start) & (t_arr <= end)
                    gain[mask] = ducking_ratio
                # Reshape gain for broadcasting with frame shape (N, channels)
                return frame * gain.reshape(-1, 1)

            music = music.transform(_ducking_filter)

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
    crossfade_duration: float = 0.0,
) -> str:
    """Generate an SRT subtitle file from script and TTS timing data.

    Computes cumulative start times from TTS durations, accounting for
    crossfade overlap between scenes. When crossfade is applied, each
    scene after the first overlaps with its predecessor, so timestamps
    advance by (duration - crossfade) instead of the full duration.

    Args:
        script: The video script with narration text.
        tts_results: TTS results with duration info per scene.
        output_path: Path to write the .srt file.
        crossfade_duration: Duration of crossfade overlap in seconds.

    Returns:
        Path to the generated .srt file.
    """
    tts_map = {r.scene_number: r for r in tts_results}

    srt_entries = []
    current_time = 0.0
    subtitle_index = 1

    for i, scene in enumerate(script.scenes):
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

            for j, segment in enumerate(segments):
                seg_start = start_time + (j * segment_duration)
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

        # Advance current_time, subtracting crossfade overlap for scenes after the first
        if i == 0 or crossfade_duration <= 0:
            current_time = end_time
        else:
            current_time = end_time - crossfade_duration

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
