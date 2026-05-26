"""Video editor API routes."""

import asyncio
import logging
from pathlib import Path as FilePath

from fastapi import APIRouter, HTTPException, Path

from app.config import settings
from app.models.schemas import (
    EditInstruction,
    EditRequest,
    EditResponse,
    PreviewFrameRequest,
    PreviewFrameResponse,
    SceneMetadata,
)
from app.services.video_editor import apply_edits, extract_frame, get_video_metadata

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/videos", tags=["editor"])

# Limit concurrent edit requests to avoid exhausting RAM on large videos
_edit_semaphore = asyncio.Semaphore(2)


@router.get("/{video_id}/scenes", response_model=list[SceneMetadata])
async def get_scenes(video_id: str = Path(pattern=r"^[a-f0-9]{12}$")):
    """Get scene metadata for a video.

    Returns a list of scenes with thumbnails, durations, and descriptions.
    The video_id must be a 12-character lowercase hex string.
    """
    metadata = get_video_metadata(video_id)
    if metadata is None:
        raise HTTPException(status_code=404, detail="Video metadata not found")

    scenes = metadata.get("scenes", [])
    result = []
    for scene in scenes:
        scene_num = scene.get("scene_number", 0)
        media_url = scene.get("media_url")

        # Use original media URL as thumbnail, or construct a static path
        if media_url:
            thumbnail_url = media_url
        else:
            thumbnail_url = f"/static/videos/{video_id}_thumb_{scene_num}.jpg"

        result.append(
            SceneMetadata(
                scene_number=scene_num,
                thumbnail_url=thumbnail_url,
                duration_seconds=scene.get("duration_seconds", 0),
                narration=scene.get("narration", ""),
                visual_description=scene.get("visual_description", ""),
                media_url=media_url,
            )
        )

    return result


@router.post("/{video_id}/edit", response_model=EditResponse)
async def edit_video(
    request: EditRequest,
    video_id: str = Path(pattern=r"^[a-f0-9]{12}$"),
):
    """Apply edit instructions to a video and produce a new version.

    Accepts an EditInstruction payload describing reordering, trims,
    text overlays, and audio level overrides.
    """
    output_dir = FilePath(settings.output_dir)
    video_path = output_dir / "videos" / f"{video_id}.mp4"

    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video not found")

    async with _edit_semaphore:
        try:
            result = await asyncio.to_thread(
                apply_edits,
                video_path=str(video_path),
                instructions=request.instructions,
                output_dir=str(output_dir),
            )
            return EditResponse(
                video_id=result["video_id"],
                video_path=result["video_path"],
                duration_seconds=result["duration_seconds"],
            )
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="Video not found")
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
        except Exception as e:
            logger.error(f"Video editing failed: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Video editing failed: {type(e).__name__}",
            )


@router.post("/{video_id}/preview-frame", response_model=PreviewFrameResponse)
async def preview_frame(
    request: PreviewFrameRequest,
    video_id: str = Path(pattern=r"^[a-f0-9]{12}$"),
):
    """Extract a preview frame from a video at the given timestamp.

    Returns a base64-encoded JPEG image of the frame.
    """
    output_dir = FilePath(settings.output_dir)
    video_path = output_dir / "videos" / f"{video_id}.mp4"

    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video not found")

    try:
        frame_data, width, height = await asyncio.to_thread(
            extract_frame, str(video_path), request.timestamp
        )
        return PreviewFrameResponse(
            frame_data=frame_data,
            timestamp=request.timestamp,
            width=width,
            height=height,
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Video not found")
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Frame extraction failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Frame extraction failed: {type(e).__name__}",
        )
