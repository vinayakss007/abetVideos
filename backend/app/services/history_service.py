import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.config import settings
from app.json_storage import locked_read, locked_write

logger = logging.getLogger(__name__)

HISTORY_DIR = Path(__file__).parent.parent / "data"
MAX_HISTORY = 10
MIN_VIDEO_SIZE = 1024


def _history_path(user_id: str) -> Path:
    return HISTORY_DIR / f"{user_id}_history.json"


def get_history(user_id: str) -> list[dict[str, Any]]:
    return locked_read(_history_path(user_id)) or []


def _cleanup_video_files(history: list[dict[str, Any]]) -> None:
    """Remove videos not in the last 10 history entries and corrupted files."""
    videos_dir = Path(settings.output_dir) / "videos"
    if not videos_dir.exists():
        return

    keep_ids = {entry["video_id"] for entry in history}

    for f in videos_dir.iterdir():
        if not f.is_file():
            continue
        if f.stat().st_size < MIN_VIDEO_SIZE:
            try:
                f.unlink()
                logger.info("Removed corrupted video: %s", f.name)
            except OSError as e:
                logger.warning("Failed to remove corrupted file %s: %s", f.name, e)
            continue
        video_id = f.stem
        if video_id not in keep_ids and f.suffix == ".mp4":
            try:
                f.unlink()
                logger.info("Removed old video not in history: %s", f.name)
            except OSError as e:
                logger.warning("Failed to remove old video %s: %s", f.name, e)
        if f.suffix == ".srt" and video_id not in keep_ids:
            try:
                f.unlink()
            except OSError:
                pass


def add_to_history(
    user_id: str,
    video_id: str,
    title: str,
    topic: str,
    duration_seconds: float,
    scenes_count: int,
    format: str,
) -> None:
    history = get_history(user_id)
    entry = {
        "id": uuid.uuid4().hex[:12],
        "video_id": video_id,
        "title": title,
        "topic": topic,
        "duration_seconds": duration_seconds,
        "scenes_count": scenes_count,
        "format": format,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    history.insert(0, entry)
    history = history[:MAX_HISTORY]
    locked_write(_history_path(user_id), history)
    _cleanup_video_files(history)


def delete_from_history(user_id: str, entry_id: str) -> bool:
    """Delete a single history entry. Returns True if found and deleted."""
    history = get_history(user_id)
    for i, entry in enumerate(history):
        if entry["id"] == entry_id:
            video_id = entry.get("video_id")
            removed = history.pop(i)
            locked_write(_history_path(user_id), history)
            # Clean up associated video file
            if video_id:
                videos_dir = Path(settings.output_dir) / "videos"
                for ext in (".mp4", ".srt"):
                    f = videos_dir / f"{video_id}{ext}"
                    try:
                        f.unlink(missing_ok=True)
                    except OSError:
                        pass
            return True
    return False


def clear_history(user_id: str) -> None:
    """Clear all history and remove all associated video files."""
    locked_write(_history_path(user_id), [])
    _cleanup_video_files([])
