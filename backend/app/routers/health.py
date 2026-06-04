"""Health check router with dependency verification."""

import logging
import shutil
import subprocess
from pathlib import Path

from fastapi import APIRouter

from app.config import settings

MIN_FREE_GB = 0.5
FFMPEG_TIMEOUT_SECONDS = 5

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["health"])


def _check_ffmpeg() -> bool:
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
            timeout=FFMPEG_TIMEOUT_SECONDS,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _check_disk_space(path: Path) -> dict[str, object]:
    try:
        stat = shutil.disk_usage(path)
        free_gb = stat.free / (1024 ** 3)
        return {
            "free_gb": round(free_gb, 1),
            "ok": free_gb > MIN_FREE_GB,
        }
    except OSError:
        return {"free_gb": 0, "ok": False}


def _check_api_keys() -> dict[str, bool]:
    return {
        "openai_configured": bool(settings.openai_api_key),
        "pexels_configured": bool(settings.pexels_api_key),
        "pixabay_configured": bool(settings.pixabay_api_key),
        "giphy_configured": bool(settings.giphy_api_key),
    }


@router.get("/health")
async def health_check():
    """Health check endpoint with dependency verification."""
    ffmpeg_ok = _check_ffmpeg()
    disk = _check_disk_space(settings.get_output_path())
    keys = _check_api_keys()

    checks = {
        "ffmpeg": ffmpeg_ok,
        "disk_space": disk["ok"],
        **{f"api_key_{k}": v for k, v in keys.items()},
    }

    overall = all(checks.values())

    return {
        "status": "ok" if overall else "degraded",
        "service": "abet-videos-backend",
        "checks": checks,
        "disk": disk,
    }
