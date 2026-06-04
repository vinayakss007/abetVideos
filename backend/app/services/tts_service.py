"""Text-to-speech service using Piper (local) with edge-tts/gTTS fallbacks."""

import asyncio
import logging
import uuid
from pathlib import Path
from typing import Optional

import edge_tts
from edge_tts.exceptions import NoAudioReceived

DEFAULT_TTS_DURATION = 5.0

from app.config import settings
from app.models.schemas import TTSResult, VideoScript

logger = logging.getLogger(__name__)

TTS_SEMAPHORE = asyncio.Semaphore(3)

PIPER_VOICES_DIR = Path(__file__).parent.parent.parent / "piper_voices"

PIPER_MODELS: dict[str, Path] = {}
for lang_dir in PIPER_VOICES_DIR.iterdir():
    if lang_dir.is_dir():
        models = sorted(lang_dir.glob("*.onnx"), key=lambda p: p.stat().st_size, reverse=True)
        if models:
            lang = lang_dir.name
            PIPER_MODELS[lang] = models[0]


async def get_audio_duration(audio_path: str) -> float:
    try:
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
        return float(stdout.decode().strip())
    except (ValueError, AttributeError, FileNotFoundError):
        logger.warning(f"Could not determine duration for {audio_path}, using estimate")
        return DEFAULT_TTS_DURATION


HINDI_FALLBACK_CHAIN = [
    "hi-IN-SwaraNeural",
    "hi-IN-MadhurNeural",
]


def _run_piper_sync(text: str, output_path: str, voice: str) -> float:
    """Run piper TTS synchronously (blocking I/O)."""
    import numpy as np
    import soundfile as sf
    from piper import PiperVoice

    lang = "hi" if voice.startswith("hi-") else "en"
    model_path = PIPER_MODELS.get(lang)
    if not model_path:
        raise FileNotFoundError(f"No piper model for language '{lang}'")

    piper_voice = PiperVoice.load(str(model_path))
    chunks = list(piper_voice.synthesize(text))

    audio = np.concatenate([c.audio_float_array for c in chunks])
    sr = chunks[0].sample_rate
    sf.write(output_path, audio, sr)
    return float(len(audio) / sr)


async def _try_piper(text: str, output_path: str, voice: str) -> float | None:
    if voice and voice.startswith("en-") and "en" not in PIPER_MODELS:
        return None
    if voice and voice.startswith("hi-") and "hi" not in PIPER_MODELS:
        return None
    try:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _run_piper_sync, text, output_path, voice)
    except Exception as e:
        logger.warning(f"Piper TTS failed: {e}")
        return None


async def _try_edge_tts(text: str, output_path: str, voice: str, max_retries: int = 3) -> float:
    fallback_voices: list[str] = [voice]
    if voice in HINDI_FALLBACK_CHAIN:
        for v in HINDI_FALLBACK_CHAIN:
            if v not in fallback_voices:
                fallback_voices.append(v)

    for voice_idx, current_voice in enumerate(fallback_voices):
        for attempt in range(max_retries):
            try:
                communicate = edge_tts.Communicate(text, current_voice)
                await communicate.save(output_path)
                duration = await get_audio_duration(output_path)
                return duration
            except NoAudioReceived:
                is_last = (
                    voice_idx == len(fallback_voices) - 1
                    and attempt == max_retries - 1
                )
                logger.warning(
                    f"NoAudioReceived with '{current_voice}' "
                    f"(attempt {attempt + 1}/{max_retries}){' — out of retries' if is_last else ', retrying...'}"
                )
                if not is_last:
                    await asyncio.sleep(2.0 * (attempt + 1))
            except Exception:
                is_last = (
                    voice_idx == len(fallback_voices) - 1
                    and attempt == max_retries - 1
                )
                logger.warning(
                    f"edge-tts failed with '{current_voice}' "
                    f"(attempt {attempt + 1}/{max_retries}){' — out of retries' if is_last else ', retrying...'}"
                )
                if not is_last:
                    await asyncio.sleep(2.0 * (attempt + 1))
    raise NoAudioReceived("No audio received after all edge-tts retries")


async def _try_gtts(text: str, output_path: str, voice: str) -> float | None:
    try:
        from gtts import gTTS
        lang = "hi" if voice.startswith("hi-") else "en"
        tts = gTTS(text, lang=lang, slow=False)
        tts.save(output_path)
        duration = await get_audio_duration(output_path)
        logger.info(f"gTTS fallback succeeded for lang={lang}")
        return duration
    except Exception as e:
        logger.warning(f"gTTS fallback failed: {e}")
        return None


async def generate_scene_audio(
    text: str,
    output_path: str,
    voice: Optional[str] = None,
    max_retries: int = 5,
) -> float:
    """Generate audio using Piper (local) -> edge-tts -> gTTS fallback."""
    voice = voice or settings.tts_voice

    duration = await _try_piper(text, output_path, voice)
    if duration is not None:
        logger.info(f"Piper TTS used for scene ({duration:.1f}s)")
        return duration

    try:
        duration = await _try_edge_tts(text, output_path, voice)
        logger.info(f"edge-tts used for scene ({duration:.1f}s)")
        return duration
    except NoAudioReceived:
        pass

    duration = await _try_gtts(text, output_path, voice)
    if duration is not None:
        return duration

    raise NoAudioReceived("All TTS backends (piper, edge-tts, gTTS) failed")


async def generate_tts(
    script: VideoScript,
    voice: Optional[str] = None,
    output_dir: Optional[str] = None,
) -> list[TTSResult]:
    voice = voice or settings.tts_voice
    base_dir = Path(output_dir or settings.output_dir)
    audio_dir = base_dir / "audio" / str(uuid.uuid4())[:8]
    audio_dir.mkdir(parents=True, exist_ok=True)

    async def generate_scene(scene) -> TTSResult:
        audio_filename = f"scene_{scene.scene_number:03d}.wav"
        audio_path = str(audio_dir / audio_filename)

        logger.info(
            f"Generating TTS for scene {scene.scene_number}: "
            f"'{scene.narration[:50]}...'"
        )

        async with TTS_SEMAPHORE:
            duration = await generate_scene_audio(
                text=scene.narration,
                output_path=audio_path,
                voice=voice,
            )

        logger.info(
            f"Scene {scene.scene_number} audio generated: "
            f"{duration:.1f}s -> {audio_path}"
        )
        return TTSResult(
            scene_number=scene.scene_number,
            audio_path=audio_path,
            duration_seconds=duration,
        )

    results = await asyncio.gather(*[generate_scene(s) for s in script.scenes])

    results.sort(key=lambda r: r.scene_number)

    total_duration = sum(r.duration_seconds for r in results)
    logger.info(
        f"TTS generation complete: {len(results)} scenes, "
        f"total duration: {total_duration:.1f}s"
    )

    return results
