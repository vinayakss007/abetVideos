"""Runtime settings persistence layer.

Reads/writes per-user JSON files for API keys and configuration.
On startup, global defaults are loaded from .env.
When a user is authenticated, their personal settings override the defaults.
"""

import contextvars
import json
import logging
from pathlib import Path
from typing import Any

from app.config import settings
from app.json_storage import locked_read, locked_write

logger = logging.getLogger(__name__)

SETTINGS_DIR = Path(__file__).parent / "user_settings"
DATA_DIR = Path(__file__).parent / "data"

SENSITIVE_KEYS = {
    "openai_api_key",
    "pexels_api_key",
    "pixabay_api_key",
    "giphy_api_key",
    "unsplash_access_key",
    "freesound_api_key",
}

ALL_SETTING_KEYS = {
    "openai_api_key",
    "openai_base_url",
    "openai_model",
    "pexels_api_key",
    "pixabay_api_key",
    "giphy_api_key",
    "unsplash_access_key",
    "freesound_api_key",
    "media_cache_enabled",
    "tts_voice",
    "output_dir",
}

MASKED_PATTERN_PREFIX = "****"

_user_settings_ctx: contextvars.ContextVar[dict | None] = contextvars.ContextVar(
    "user_settings", default=None
)


def set_active_user(user_id: str | None) -> None:
    """Load a user's settings into the current request context."""
    if user_id is None:
        _user_settings_ctx.set(None)
        return
    path = _user_settings_path(user_id)
    if path.exists():
        data = locked_read(path)
        _user_settings_ctx.set(data if data else {})
        logger.debug("Loaded settings for user %s", user_id)
    else:
        _user_settings_ctx.set({})


def _user_settings_path(user_id: str) -> Path:
    return DATA_DIR / "settings" / f"{user_id}.json"


def get_user_setting(key: str) -> Any:
    """Get a setting value, checking user context first, then global defaults."""
    ctx = _user_settings_ctx.get()
    if ctx is not None and key in ctx:
        return ctx[key]
    return getattr(settings, key, None)


def _is_masked(val: str) -> bool:
    """Detect if a value looks like a masked key submitted back from the frontend."""
    return val.startswith(MASKED_PATTERN_PREFIX) or (
        len(val) >= 8 and "****" in val
    )


def _load(user_id: str | None = None) -> dict[str, Any]:
    if user_id:
        path = _user_settings_path(user_id)
    else:
        path = DATA_DIR / "settings.json"
    return locked_read(path) or {}


def _save(data: dict[str, Any], user_id: str | None = None) -> None:
    if user_id:
        path = _user_settings_path(user_id)
    else:
        path = DATA_DIR / "settings.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    locked_write(path, data)


def load_runtime_settings() -> None:
    """Load global settings from the legacy JSON file and apply them."""
    data = _load(user_id=None)
    if not data:
        return
    for key, value in data.items():
        if hasattr(settings, key) and value is not None:
            setattr(settings, key, value)
    logger.info("Loaded global runtime settings")


def get_settings(user_id: str | None = None) -> dict[str, Any]:
    """Return settings with sensitive values masked, merged with global defaults."""
    user_data = _load(user_id) if user_id else {}
    result: dict[str, Any] = {}
    for key in ALL_SETTING_KEYS:
        raw = user_data.get(key) if user_id else getattr(settings, key, None)
        if raw is None:
            raw = getattr(settings, key, "")
        if raw is None:
            raw = ""
        if key in SENSITIVE_KEYS:
            result[f"{key}_configured"] = bool(raw)
            result[key] = ""
        else:
            result[key] = raw
    return result


def update_settings(updates: dict[str, Any], user_id: str | None = None) -> dict[str, Any]:
    """Apply partial updates and persist. If user_id is given, saves per-user."""
    current = _load(user_id)

    for key, value in updates.items():
        if key not in ALL_SETTING_KEYS:
            continue
        if value is None:
            continue
        if isinstance(value, str):
            value = value.strip()
        if key in SENSITIVE_KEYS and isinstance(value, str) and _is_masked(value):
            logger.debug("Skipping masked %s update — preserving real value", key)
            continue
        if user_id:
            current[key] = value
        else:
            setattr(settings, key, value)
            current[key] = value

    _save(current, user_id)

    if user_id:
        set_active_user(user_id)

    logger.info("Settings updated for %s", user_id or "global")
    return get_settings(user_id)
