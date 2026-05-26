"""Video generation API routes."""

import json
import logging
import os
from pathlib import Path as FilePath
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException, Path
from fastapi.responses import FileResponse, StreamingResponse

from app.config import settings
from app.models.schemas import (
    AssembleVideoRequest,
    GenerateFullRequest,
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
async def download_video(video_id: str = Path(pattern=r"^[a-f0-9]{12}$")):
    """Download a generated video by its ID.

    Serves the MP4 file for the given video ID.
    The video_id must be a 12-character lowercase hex string.
    """
    output_dir = FilePath(settings.output_dir) / "videos"
    video_path = output_dir / f"{video_id}.mp4"

    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video not found")

    return FileResponse(
        path=str(video_path),
        media_type="video/mp4",
        filename=f"{video_id}.mp4",
    )


def _sse_event(step: str, progress: float, message: str, data: dict | None = None) -> str:
    """Format an SSE event."""
    payload = {"step": step, "progress": progress, "message": message}
    if data is not None:
        payload["data"] = data
    return f"data: {json.dumps(payload)}\n\n"


@router.post("/generate-full")
async def generate_full_video(request: GenerateFullRequest):
    """Generate a complete video via the full pipeline with SSE progress updates.

    Orchestrates: script generation -> TTS -> media sourcing -> video assembly.
    Streams progress events via Server-Sent Events.
    """

    async def event_stream() -> AsyncGenerator[str, None]:
        current_stage = "initialization"
        try:
            # Step 1: Script generation
            current_stage = "script_generation"
            yield _sse_event("script_generation", 0, "Starting script generation...")
            script = await generate_script(
                topic=request.topic,
                duration_minutes=request.duration_minutes,
                style=request.style,
            )
            yield _sse_event(
                "script_generation",
                25,
                f"Script generated: {script.title} ({len(script.scenes)} scenes)",
                script.model_dump(),
            )

            # Step 2: TTS generation
            current_stage = "tts_generation"
            yield _sse_event("tts_generation", 25, "Generating text-to-speech audio...")
            tts_results = await generate_tts(script=script)
            yield _sse_event(
                "tts_generation",
                50,
                f"Audio generated for {len(tts_results)} scenes",
                [r.model_dump() for r in tts_results],
            )

            # Step 3: Media sourcing
            current_stage = "media_sourcing"
            yield _sse_event("media_sourcing", 50, "Sourcing media for scenes...")
            scene_media = await source_media(script=script)
            yield _sse_event(
                "media_sourcing",
                75,
                f"Media sourced for {len(scene_media)} scenes",
                [sm.model_dump() for sm in scene_media],
            )

            # Step 4: Video assembly
            current_stage = "video_assembly"
            yield _sse_event("video_assembly", 75, "Assembling final video...")
            result = await assemble_video(
                script=script,
                tts_results=tts_results,
                scene_media=scene_media,
            )
            yield _sse_event(
                "video_assembly",
                90,
                "Video assembly complete",
            )

            # Step 5: Complete
            yield _sse_event(
                "complete",
                100,
                "Video generation complete!",
                result.model_dump(),
            )
        except Exception as e:
            logger.error(f"Full pipeline failed at stage '{current_stage}': {e}")
            yield _sse_event(
                "error",
                -1,
                f"Pipeline failed at stage '{current_stage}': {str(e)}",
                {"failed_stage": current_stage},
            )

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
