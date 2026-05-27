"""Branding overlay API routes."""

import logging
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from app.models.schemas import BrandingConfig, BrandingPosition
from app.services.branding_service import branding_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/branding", tags=["branding"])


class BrandingUpdateRequest(BaseModel):
    """Request body for updating branding config."""

    position: Optional[str] = None
    size_percent: Optional[float] = None
    opacity: Optional[float] = None
    enabled: Optional[bool] = None


@router.post("/upload", response_model=BrandingConfig)
async def upload_branding(
    file: UploadFile = File(...),
    position: str = Form(default="bottom-right"),
    size_percent: float = Form(default=15.0),
    opacity: float = Form(default=0.8),
):
    """Upload a branding image.

    Accepts multipart form data with the image file and position settings.
    """
    # Validate position
    try:
        pos = BrandingPosition(position)
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid position: {position}. Must be one of: top-left, top-right, bottom-left, bottom-right, top-center, bottom-center",
        )

    # Validate size_percent
    if size_percent < 10.0 or size_percent > 50.0:
        raise HTTPException(status_code=422, detail="size_percent must be between 10 and 50")

    # Validate opacity
    if opacity < 0.1 or opacity > 1.0:
        raise HTTPException(status_code=422, detail="opacity must be between 0.1 and 1.0")

    # Read file content
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=422, detail="Empty file")

    try:
        config = branding_service.upload_branding(
            file_bytes=file_bytes,
            filename=file.filename or "branding.png",
            position=pos,
            size_percent=size_percent,
            opacity=opacity,
        )
        return config
    except Exception as e:
        logger.error(f"Branding upload failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload branding image")


@router.get("")
async def get_branding():
    """Get current branding configuration.

    Returns the branding config or null if not configured.
    """
    config = branding_service.get_config()
    return config


@router.put("", response_model=BrandingConfig)
async def update_branding(request: BrandingUpdateRequest):
    """Update branding configuration settings."""
    # Validate position if provided
    pos = None
    if request.position is not None:
        try:
            pos = BrandingPosition(request.position)
        except ValueError:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid position: {request.position}",
            )

    # Validate size_percent if provided
    if request.size_percent is not None and (request.size_percent < 10.0 or request.size_percent > 50.0):
        raise HTTPException(status_code=422, detail="size_percent must be between 10 and 50")

    # Validate opacity if provided
    if request.opacity is not None and (request.opacity < 0.1 or request.opacity > 1.0):
        raise HTTPException(status_code=422, detail="opacity must be between 0.1 and 1.0")

    config = branding_service.update_config(
        position=pos,
        size_percent=request.size_percent,
        opacity=request.opacity,
        enabled=request.enabled,
    )
    if config is None:
        raise HTTPException(status_code=404, detail="No branding config found. Upload a branding image first.")
    return config


@router.delete("")
async def delete_branding():
    """Delete branding configuration and image."""
    deleted = branding_service.delete_branding()
    if not deleted:
        raise HTTPException(status_code=404, detail="No branding config found")
    return {"detail": "Branding deleted"}
