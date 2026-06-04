"""Settings API routes for managing runtime configuration per user."""

import logging

from fastapi import APIRouter, HTTPException, Depends

from app.auth.dependencies import get_current_user
from app.models.schemas import AIModelInfo, AppSettings, SettingsUpdate
from app.services.ai_gateway import fetch_available_models
from app.settings_manager import get_settings, update_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("", response_model=AppSettings)
async def read_settings(current_user: dict = Depends(get_current_user)):
    """Return current application settings for the authenticated user."""
    return get_settings(user_id=current_user["user_id"])


@router.put("", response_model=AppSettings)
async def write_settings(
    updates: SettingsUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update settings for the authenticated user.

    Accepts a partial payload — only the supplied fields are changed.
    Returns the full settings object with sensitive values masked.
    """
    try:
        raw = updates.model_dump(exclude_none=True)
        result = update_settings(raw, user_id=current_user["user_id"])
        return result
    except Exception as e:
        logger.error("Failed to update settings: %s", e)
        raise HTTPException(status_code=500, detail="Failed to save settings")


@router.get("/models", response_model=list[AIModelInfo])
async def list_available_models(current_user: dict = Depends(get_current_user)):
    """Fetch available models from the configured provider.

    Calls GET {openai_base_url}/models using the configured API key.
    Returns an empty list if the provider doesn't expose a /models endpoint.
    """
    models = await fetch_available_models()
    return [
        AIModelInfo(
            id=m.get("id", ""),
            name=m.get("name", "") or m.get("id", ""),
            owned_by=m.get("owned_by", ""),
        )
        for m in models
    ]
