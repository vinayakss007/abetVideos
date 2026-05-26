"""Video generation API routes."""

import logging
import os
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.config import settings
from app.models.schemas import (
    AssembleVideoRequest,
    GenerateScriptRequest,
    GenerateTTSRequest,
    SceneMedia,
    SourceMediaRequest,
    TTSResult,
    VideoResult,
    VideoScript,
)
from app.services.media_sourcer import source_media
from app.services.script_generator import generate_script
from app.services.tts_service import generate_tts
from app.services.video_assembler import assemble_video

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/videos", tags=["videos"])


@router.post("/generate-script", response_model=VideoScript)
async def generate_video_script(request: GenerateScriptRequest):
    """Generate a video script from a topic using AI.

    Takes a topic, desired duration, and style, then uses the AI gateway
    to generate a structured video script with scenes, narration, and
    visual descriptions.
    """
    try:
        script = await generate_script(
            topic=request.topic,
            duration_minutes=request.duration_minutes,
            style=request.style,
        )
        return script
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Script generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Script generation failed: {str(e)}",
        )


@router.post("/generate-tts", response_model=list[TTSResult])
async def generate_video_tts(request: GenerateTTSRequest):
    """Generate text-to-speech audio for a video script.

    Takes a VideoScript and generates audio files for each scene's
    narration using edge-tts.
    """
    try:
        results = await generate_tts(
            script=request.script,
            voice=request.voice,
        )
        return results
    except Exception as e:
        logger.error(f"TTS generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"TTS generation failed: {str(e)}",
        )


@router.post("/source-media", response_model=list[SceneMedia])
async def source_video_media(request: SourceMediaRequest):
    """Source media (videos, images, GIFs) for a video script.

    Searches Pexels, Pixabay, and Giphy APIs for relevant media
    based on each scene's visual description.
    """
    try:
        results = await source_media(
            script=request.script,
            preferred_type=request.preferred_type,
        )
        return results
    except Exception as e:
        logger.error(f"Media sourcing failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Media sourcing failed: {str(e)}",
        )


@router.post("/assemble", response_model=VideoResult)
async def assemble_final_video(request: AssembleVideoRequest):
    """Assemble the final video from script, audio, and media.

    Combines TTS audio with sourced media using MoviePy to produce
    the final MP4 video file.
    """
    try:
        result = await assemble_video(
            script=request.script,
            tts_results=request.tts_results,
            scene_media=request.scene_media,
            format=request.format,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Video assembly failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Video assembly failed: {str(e)}",
        )


@router.get("/{video_id}/download")
async def download_video(video_id: str):
    """Download a generated video by its ID.

    Serves the MP4 file for the given video ID.
    """
    output_dir = Path(settings.output_dir) / "videos"
    video_path = output_dir / f"{video_id}.mp4"

    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video not found")

    return FileResponse(
        path=str(video_path),
        media_type="video/mp4",
        filename=f"{video_id}.mp4",
    )
