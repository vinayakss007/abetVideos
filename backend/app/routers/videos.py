"""Video generation API routes (authenticated)."""

import logging
from pathlib import Path as FilePath

from fastapi import APIRouter, HTTPException, Depends, Path
from fastapi.responses import FileResponse, StreamingResponse

import httpx

from app.auth.dependencies import get_current_user
from app.config import settings
from app.models.schemas import (
    AssembleVideoRequest,
    GenerateFullRequest,
    GenerateScriptRequest,
    GenerateTTSRequest,
    MediaItem,
    SceneMedia,
    SearchMediaRequest,
    SourceMediaRequest,
    TTSResult,
    VideoResult,
    VideoScript,
)
from app.services.history_service import add_to_history, get_history
from app.services.media_sourcer import source_media, search_all_sources, provider_registry
from app.services.music_service import search_music
from app.services.script_generator import generate_script
from app.services.tts_service import generate_tts
from app.services.video_assembler import assemble_video
from app.services.task_manager import create_task, get_task, stream_events, TaskStatus
from app.settings_manager import set_active_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/videos", tags=["videos"])


def _safe_error_detail(prefix: str, exc: Exception) -> str:
    return f"{prefix}: {type(exc).__name__}"


def _load_user_context(current_user: dict) -> None:
    """Load the authenticated user's settings into the request context."""
    set_active_user(current_user["user_id"])


@router.get("/providers")
async def list_providers(current_user: dict = Depends(get_current_user)):
    """Return the list of configured/active media providers."""
    _load_user_context(current_user)
    return provider_registry.get_providers_status()


@router.post("/generate-script", response_model=VideoScript)
async def generate_video_script(
    request: GenerateScriptRequest,
    current_user: dict = Depends(get_current_user),
):
    """Generate a video script from a topic using AI."""
    _load_user_context(current_user)
    try:
        language = request.language if hasattr(request, 'language') else "english"
        script = await generate_script(
            topic=request.topic,
            duration_minutes=request.duration_minutes,
            style=request.style,
            language=language,
        )
        return script
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Script generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=_safe_error_detail("Script generation failed", e),
        )


@router.post("/generate-tts", response_model=list[TTSResult])
async def generate_video_tts(
    request: GenerateTTSRequest,
    current_user: dict = Depends(get_current_user),
):
    """Generate text-to-speech audio for a video script."""
    _load_user_context(current_user)
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
            detail=_safe_error_detail("TTS generation failed", e),
        )


@router.post("/source-media", response_model=list[SceneMedia])
async def source_video_media(
    request: SourceMediaRequest,
    current_user: dict = Depends(get_current_user),
):
    """Source media (videos, images, GIFs) for a video script."""
    _load_user_context(current_user)
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
            detail=_safe_error_detail("Media sourcing failed", e),
        )


@router.post("/search-media", response_model=list[MediaItem])
async def search_media(
    request: SearchMediaRequest,
    current_user: dict = Depends(get_current_user),
):
    """Search all media sources for a given query."""
    _load_user_context(current_user)
    try:
        async with httpx.AsyncClient() as client:
            results = await search_all_sources(request.query, client)
        return results
    except Exception as e:
        logger.error(f"Media search failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=_safe_error_detail("Media search failed", e),
        )


@router.get("/music-search")
async def list_music(
    query: str = "calm",
    current_user: dict = Depends(get_current_user),
):
    """Search royalty-free background music by mood or keyword."""
    _load_user_context(current_user)
    return await search_music(query)


@router.get("/history")
async def list_video_history(
    current_user: dict = Depends(get_current_user),
):
    """Return the last 10 generated videos for the current user."""
    _load_user_context(current_user)
    return get_history(current_user["user_id"])


@router.delete("/history/{entry_id}")
async def delete_history_entry(
    entry_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Delete a single history entry and its associated video file."""
    _load_user_context(current_user)
    from app.services.history_service import delete_from_history
    result = delete_from_history(current_user["user_id"], entry_id)
    if not result:
        raise HTTPException(status_code=404, detail="Entry not found")
    return {"detail": "Deleted"}


@router.delete("/history")
async def clear_all_history(
    current_user: dict = Depends(get_current_user),
):
    """Clear all history entries and associated video files."""
    _load_user_context(current_user)
    from app.services.history_service import clear_history
    clear_history(current_user["user_id"])
    return {"detail": "All history cleared"}


@router.post("/assemble", response_model=VideoResult)
async def assemble_final_video(
    request: AssembleVideoRequest,
    current_user: dict = Depends(get_current_user),
):
    """Assemble the final video from script, audio, and media."""
    _load_user_context(current_user)
    try:
        result = await assemble_video(
            script=request.script,
            tts_results=request.tts_results,
            scene_media=request.scene_media,
            format=request.format,
            quality_settings=request.quality_settings,
            audio_settings=request.audio_settings,
        )
        add_to_history(
            user_id=current_user["user_id"],
            video_id=result.video_id,
            title=request.script.title,
            topic=request.script.title,
            duration_seconds=result.duration_seconds,
            scenes_count=result.scenes_count,
            format=result.format.value,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Video assembly failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=_safe_error_detail("Video assembly failed", e),
        )


@router.get("/{video_id}/download")
async def download_video(
    video_id: str = Path(pattern=r"^[a-f0-9]{12}$"),
    current_user: dict = Depends(get_current_user),
):
    """Download a generated video by its ID."""
    _load_user_context(current_user)
    output_dir = FilePath(settings.output_dir) / "videos"
    video_path = output_dir / f"{video_id}.mp4"

    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video not found")

    return FileResponse(
        path=str(video_path),
        media_type="video/mp4",
        filename=f"{video_id}.mp4",
    )


@router.get("/audio-download")
async def download_audio(
    video_id: str,
    scene_number: int,
    current_user: dict = Depends(get_current_user),
):
    """Download a generated audio file by video_id and scene_number."""
    _load_user_context(current_user)
    base = FilePath(settings.output_dir).resolve()
    audio_file = (base / "videos" / video_id / f"scene_{scene_number}.mp3").resolve()
    try:
        audio_file.relative_to(base)
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied")
    if not audio_file.exists() or not audio_file.is_file():
        raise HTTPException(status_code=404, detail="Audio not found")
    return FileResponse(
        path=str(audio_file),
        media_type="audio/mpeg",
        filename=audio_file.name,
    )


@router.get("/{video_id}/subtitles")
async def get_video_subtitles(
    video_id: str = Path(pattern=r"^[a-f0-9]{12}$"),
    current_user: dict = Depends(get_current_user),
):
    """Serve the generated SRT subtitle file for a video."""
    _load_user_context(current_user)
    output_dir = FilePath(settings.output_dir) / "videos"
    srt_path = output_dir / f"{video_id}.srt"

    if not srt_path.exists():
        raise HTTPException(status_code=404, detail="Subtitles not found")

    return FileResponse(
        path=str(srt_path),
        media_type="application/x-subrip",
        filename=f"{video_id}.srt",
    )


@router.get("/{video_id}/thumbnail")
async def get_video_thumbnail(
    video_id: str = Path(pattern=r"^[a-f0-9]{12}$"),
    current_user: dict = Depends(get_current_user),
):
    """Serve the generated thumbnail image for a video."""
    _load_user_context(current_user)
    output_dir = FilePath(settings.output_dir) / "videos"
    thumb_path = output_dir / f"{video_id}.jpg"

    if not thumb_path.exists():
        raise HTTPException(status_code=404, detail="Thumbnail not found")

    return FileResponse(
        path=str(thumb_path),
        media_type="image/jpeg",
        filename=f"{video_id}.jpg",
    )


@router.post("/generate-full")
async def generate_full_video(
    request: GenerateFullRequest,
    current_user: dict = Depends(get_current_user),
):
    """Start a background video generation task. Returns task_id immediately."""
    _load_user_context(current_user)
    task_id = create_task(request, current_user["user_id"])
    return {"task_id": task_id, "status": TaskStatus.PENDING}


@router.get("/tasks/{task_id}")
async def get_task_status(
    task_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get the current status of a video generation task."""
    _load_user_context(current_user)
    task = get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    if task["user_id"] != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    return {
        "task_id": task["task_id"],
        "status": task["status"],
        "result": task["result"],
        "created_at": task["created_at"],
    }


@router.delete("/tasks/{task_id}")
async def cancel_video_task(
    task_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Cancel a running video generation task."""
    _load_user_context(current_user)
    task = get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    if task["user_id"] != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    if not cancel_task(task_id):
        raise HTTPException(status_code=409, detail="Task is not cancellable")
    return {"detail": "Task cancelled"}


@router.get("/tasks/{task_id}/stream")
async def stream_task_events(
    task_id: str,
    current_user: dict = Depends(get_current_user),
):
    """SSE stream of events for a running task."""
    _load_user_context(current_user)
    task = get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    if task["user_id"] != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    return StreamingResponse(
        stream_events(task_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
