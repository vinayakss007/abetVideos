"""Local media library API routes."""

import logging
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, Path, UploadFile

from app.models.schemas import LibraryCategory, LibraryItem
from app.services.library_service import library_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/library", tags=["library"])


@router.post("/upload", response_model=LibraryItem)
async def upload_library_item(
    file: UploadFile = File(...),
    category: str = Form(...),
    labels: str = Form(default=""),
    description: str = Form(default=""),
):
    """Upload a media file to the local library.

    Accepts multipart form data with the file and metadata.
    Labels should be comma-separated.
    """
    # Validate category
    try:
        cat = LibraryCategory(category)
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid category: {category}. Must be one of: music, image, video",
        )

    # Read file content
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=422, detail="Empty file")

    # Validate content type against category
    content_type = file.content_type
    if content_type and content_type != "application/octet-stream":
        type_prefix_map = {
            LibraryCategory.music: "audio/",
            LibraryCategory.image: "image/",
            LibraryCategory.video: "video/",
        }
        expected_prefix = type_prefix_map[cat]
        if not content_type.startswith(expected_prefix):
            raise HTTPException(
                status_code=422,
                detail=f"Invalid content type '{content_type}' for category '{category}'. Expected {expected_prefix}*",
            )

    # Validate file size
    size_limits = {
        LibraryCategory.music: 50 * 1024 * 1024,   # 50MB
        LibraryCategory.image: 20 * 1024 * 1024,   # 20MB
        LibraryCategory.video: 200 * 1024 * 1024,  # 200MB
    }
    max_size = size_limits[cat]
    if len(file_bytes) > max_size:
        max_mb = max_size // (1024 * 1024)
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size for {category} is {max_mb}MB",
        )

    # Parse labels
    label_list = [l.strip() for l in labels.split(",") if l.strip()]

    try:
        item = library_service.add_item(
            file_bytes=file_bytes,
            filename=file.filename or "unnamed",
            category=cat,
            labels=label_list,
            description=description,
        )
        return item
    except Exception as e:
        logger.error(f"Library upload failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload file")


@router.get("/search", response_model=list[LibraryItem])
async def search_library(query: str = ""):
    """Search library items by query matching labels and description."""
    if not query:
        raise HTTPException(status_code=422, detail="Query parameter is required")
    return library_service.search_items(query)


@router.get("", response_model=list[LibraryItem])
async def list_library_items(
    category: Optional[str] = None,
    search: Optional[str] = None,
):
    """List library items with optional category and search filters."""
    cat = None
    if category:
        try:
            cat = LibraryCategory(category)
        except ValueError:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid category: {category}. Must be one of: music, image, video",
            )

    return library_service.list_items(category=cat, search=search)


@router.get("/{item_id}", response_model=LibraryItem)
async def get_library_item(item_id: str = Path(...)):
    """Get a specific library item by ID."""
    item = library_service.get_item(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.delete("/{item_id}")
async def delete_library_item(item_id: str = Path(...)):
    """Delete a library item by ID."""
    deleted = library_service.delete_item(item_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"detail": "Item deleted", "id": item_id}
