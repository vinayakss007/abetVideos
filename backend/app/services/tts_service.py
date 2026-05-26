"""Text-to-speech service using edge-tts (Microsoft Edge TTS)."""

import logging
import os
import uuid
from pathlib import Path
from typing import Optional

import edge_tts

from app.config import settings
from app.models.schemas import TTSResult, VideoScript

logger = logging.getLogger(__name__)


async def get_audio_duration(audio_path: str) -> float:
    """Get the duration of an audio file using ffprobe.

    Args:
        audio_path: Path to the audio file.

    Returns:
        Duration in seconds.
    """
    import asyncio

    proc = await asyncio.create_subprocess_exec(
        "ffprobe",
        "-v", "quiet",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        audio_path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _ = await proc.communicate()

    try:
        return float(stdout.decode().strip())
    except (ValueError, AttributeError):
        logger.warning(f"Could not determine duration for {audio_path}, using estimate")
        return 5.0


async def generate_scene_audio(
    text: str,
    output_path: str,
    voice: Optional[str] = None,
) -> float:
    """Generate audio for a single text using edge-tts.

    Args:
        text: The narration text to convert to speech.
        output_path: Where to save the audio file.
        voice: TTS voice to use (default from settings).

    Returns:
        Duration of the generated audio in seconds.
    """
    voice = voice or settings.tts_voice

    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)

    duration = await get_audio_duration(output_path)
    return duration


async def generate_tts(
    script: VideoScript,
    voice: Optional[str] = None,
    output_dir: Optional[str] = None,
) -> list[TTSResult]:
    """Generate TTS audio for all scenes in a script.

    Args:
        script: The video script with scenes containing narration.
        voice: Optional voice override.
        output_dir: Optional output directory override.

    Returns:
        List of TTSResult with audio paths and durations.
    """
    voice = voice or settings.tts_voice
    base_dir = Path(output_dir or settings.output_dir)
    audio_dir = base_dir / "audio" / str(uuid.uuid4())[:8]
    audio_dir.mkdir(parents=True, exist_ok=True)

    results: list[TTSResult] = []

    for scene in script.scenes:
        audio_filename = f"scene_{scene.scene_number:03d}.mp3"
        audio_path = str(audio_dir / audio_filename)

        logger.info(
            f"Generating TTS for scene {scene.scene_number}: "
            f"'{scene.narration[:50]}...'"
        )

        duration = await generate_scene_audio(
            text=scene.narration,
            output_path=audio_path,
            voice=voice,
        )

        results.append(
            TTSResult(
                scene_number=scene.scene_number,
                audio_path=audio_path,
                duration_seconds=duration,
            )
        )

        logger.info(
            f"Scene {scene.scene_number} audio generated: "
            f"{duration:.1f}s -> {audio_path}"
        )

    total_duration = sum(r.duration_seconds for r in results)
    logger.info(
        f"TTS generation complete: {len(results)} scenes, "
        f"total duration: {total_duration:.1f}s"
    )

    return results
