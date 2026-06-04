"""Background task manager for video generation."""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Optional

from app.models.schemas import GenerateFullRequest
from app.services.history_service import add_to_history
from app.services.media_sourcer import source_media
from app.services.script_generator import generate_script
from app.services.tts_service import generate_tts
from app.services.video_assembler import assemble_video

POLL_INTERVAL_SECONDS = 0.5
from app.settings_manager import set_active_user

logger = logging.getLogger(__name__)


class TaskStatus:
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


_tasks: dict[str, dict[str, Any]] = {}


def _sse_event(step: str, progress: float, message: str, data: dict | None = None) -> str:
    payload = {"step": step, "progress": progress, "message": message}
    if data is not None:
        payload["data"] = data
    return f"data: {json.dumps(payload)}\n\n"


async def run_generation(task_id: str, request: GenerateFullRequest, user_id: str) -> None:
    task = _tasks[task_id]
    task["status"] = TaskStatus.RUNNING
    set_active_user(user_id)
    current_stage = "initialization"

    async def check_cancelled() -> bool:
        cancel_event: asyncio.Event = task["_cancel_event"]
        if cancel_event.is_set():
            task["status"] = TaskStatus.CANCELLED
            return True
        return False

    try:
        if await check_cancelled():
            return
        current_stage = "script_generation"
        task["events"].append(_sse_event("script_generation", 0, "Starting script generation..."))
        tts_voice_lang = request.audio_settings.tts_voice if request.audio_settings and request.audio_settings.tts_voice else None
        script_language = request.language
        if tts_voice_lang and tts_voice_lang.startswith("hi-"):
            script_language = "hindi"
        script = await generate_script(
            topic=request.topic,
            duration_minutes=request.duration_minutes,
            style=request.style,
            language=script_language,
        )
        task["events"].append(_sse_event(
            "script_generation", 25,
            f"Script generated: {script.title} ({len(script.scenes)} scenes)",
            script.model_dump(),
        ))
        if await check_cancelled():
            return

        current_stage = "tts_generation"
        task["events"].append(_sse_event("tts_generation", 25, "Generating text-to-speech audio..."))
        tts_voice = request.audio_settings.tts_voice if request.audio_settings else None
        tts_results = await generate_tts(script=script, voice=tts_voice)
        task["events"].append(_sse_event(
            "tts_generation", 50,
            f"Audio generated for {len(tts_results)} scenes",
            [r.model_dump() for r in tts_results],
        ))
        if await check_cancelled():
            return

        current_stage = "media_sourcing"
        task["events"].append(_sse_event("media_sourcing", 50, "Sourcing media for scenes..."))
        scene_media = await source_media(script=script)
        task["events"].append(_sse_event(
            "media_sourcing", 75,
            f"Media sourced for {len(scene_media)} scenes",
            [sm.model_dump() for sm in scene_media],
        ))
        if await check_cancelled():
            return

        current_stage = "video_assembly"
        task["events"].append(_sse_event("video_assembly", 75, "Assembling final video..."))
        result = await assemble_video(
            script=script,
            tts_results=tts_results,
            scene_media=scene_media,
            quality_settings=request.quality_settings,
            audio_settings=request.audio_settings,
        )

        add_to_history(
            user_id=user_id,
            video_id=result.video_id,
            title=script.title,
            topic=request.topic,
            duration_seconds=result.duration_seconds,
            scenes_count=result.scenes_count,
            format=result.format.value,
        )

        task["events"].append(_sse_event("video_assembly", 90, "Video assembly complete"))
        task["events"].append(_sse_event(
            "complete", 100, "Video generation complete!",
            result.model_dump(),
        ))
        task["status"] = TaskStatus.COMPLETED
        task["result"] = result.model_dump()

    except asyncio.CancelledError:
        task["status"] = TaskStatus.CANCELLED
        task["events"].append(_sse_event("error", -1, "Task cancelled"))
        logger.info("Task %s cancelled", task_id)

    except Exception as e:
        logger.error(f"Task {task_id} failed at stage '{current_stage}': {e}")
        task["status"] = TaskStatus.FAILED
        task["events"].append(_sse_event(
            "error", -1,
            f"Pipeline failed at stage '{current_stage}': {type(e).__name__}",
            {"failed_stage": current_stage},
        ))


def create_task(request: GenerateFullRequest, user_id: str) -> str:
    task_id = uuid.uuid4().hex[:12]
    _tasks[task_id] = {
        "task_id": task_id,
        "status": TaskStatus.PENDING,
        "events": [],
        "result": None,
        "user_id": user_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "_cancel_event": asyncio.Event(),
    }
    asyncio.create_task(run_generation(task_id, request, user_id))
    return task_id


def cancel_task(task_id: str) -> bool:
    """Cancel a running task. Returns True if the task was found."""
    task = _tasks.get(task_id)
    if task is None:
        return False
    if task["status"] not in (TaskStatus.PENDING, TaskStatus.RUNNING):
        return False
    cancel_event: asyncio.Event = task["_cancel_event"]
    cancel_event.set()
    task["status"] = TaskStatus.CANCELLED
    task["events"].append(_sse_event(
        "error", -1, "Task cancelled by user"
    ))
    logger.info("Task %s cancelled by user", task_id)
    return True


def get_task(task_id: str) -> Optional[dict[str, Any]]:
    return _tasks.get(task_id)


async def stream_events(task_id: str) -> AsyncGenerator[str, None]:
    task = _tasks.get(task_id)
    if task is None:
        yield _sse_event("error", -1, "Task not found")
        return

    sent = 0
    while task["status"] in (TaskStatus.PENDING, TaskStatus.RUNNING):
        while sent < len(task["events"]):
            yield task["events"][sent]
            sent += 1
        if task["status"] in (TaskStatus.PENDING, TaskStatus.RUNNING):
            await asyncio.sleep(POLL_INTERVAL_SECONDS)
        if task["status"] == TaskStatus.CANCELLED:
            return

    while sent < len(task["events"]):
        yield task["events"][sent]
        sent += 1
