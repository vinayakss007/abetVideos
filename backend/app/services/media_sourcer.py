"""Media sourcing service - searches Pexels, Pixabay, and Giphy for media."""

import asyncio
import logging
import os
import uuid
from pathlib import Path
from typing import Optional

import httpx

from app.config import settings
from app.models.schemas import MediaItem, MediaType, SceneMedia, VideoScript

logger = logging.getLogger(__name__)

# API endpoints
PEXELS_VIDEO_URL = "https://api.pexels.com/videos/search"
PEXELS_PHOTO_URL = "https://api.pexels.com/v1/search"
PIXABAY_URL = "https://pixabay.com/api/"
PIXABAY_VIDEO_URL = "https://pixabay.com/api/videos/"
GIPHY_URL = "https://api.giphy.com/v1/gifs/search"


def _extract_keywords(visual_description: str) -> str:
    """Extract search keywords from a visual description.

    Simplifies the description to key searchable terms.
    """
    # Remove common filler words and keep the essence
    stop_words = {
        "a", "an", "the", "of", "in", "on", "at", "to", "for",
        "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did",
        "will", "would", "could", "should", "may", "might",
        "with", "from", "by", "about", "into", "through",
        "that", "this", "these", "those", "it", "its",
        "and", "or", "but", "not", "no", "very", "really",
        "showing", "displaying", "featuring", "depicting",
    }

    words = visual_description.lower().split()
    keywords = [w.strip(".,!?;:'\"") for w in words if w.lower().strip(".,!?;:'\"") not in stop_words]
    # Take first 5 meaningful keywords
    return " ".join(keywords[:5])


async def search_pexels_videos(
    query: str, client: httpx.AsyncClient, per_page: int = 3
) -> list[MediaItem]:
    """Search Pexels for videos."""
    if not settings.pexels_api_key:
        return []

    try:
        response = await client.get(
            PEXELS_VIDEO_URL,
            params={"query": query, "per_page": per_page, "size": "medium"},
            headers={"Authorization": settings.pexels_api_key},
            timeout=10.0,
        )
        response.raise_for_status()
        data = response.json()

        items = []
        for video in data.get("videos", []):
            # Get medium quality video file
            video_files = video.get("video_files", [])
            if video_files:
                # Prefer HD quality
                selected = None
                for vf in video_files:
                    if vf.get("quality") == "hd":
                        selected = vf
                        break
                if not selected:
                    selected = video_files[0]

                items.append(
                    MediaItem(
                        url=selected["link"],
                        media_type=MediaType.video,
                        source="pexels",
                        query=query,
                        width=selected.get("width"),
                        height=selected.get("height"),
                    )
                )
        return items
    except Exception as e:
        logger.warning(f"Pexels video search failed for '{query}': {e}")
        return []


async def search_pexels_photos(
    query: str, client: httpx.AsyncClient, per_page: int = 3
) -> list[MediaItem]:
    """Search Pexels for photos."""
    if not settings.pexels_api_key:
        return []

    try:
        response = await client.get(
            PEXELS_PHOTO_URL,
            params={"query": query, "per_page": per_page},
            headers={"Authorization": settings.pexels_api_key},
            timeout=10.0,
        )
        response.raise_for_status()
        data = response.json()

        items = []
        for photo in data.get("photos", []):
            src = photo.get("src", {})
            url = src.get("large2x") or src.get("large") or src.get("original", "")
            if url:
                items.append(
                    MediaItem(
                        url=url,
                        media_type=MediaType.image,
                        source="pexels",
                        query=query,
                        width=photo.get("width"),
                        height=photo.get("height"),
                    )
                )
        return items
    except Exception as e:
        logger.warning(f"Pexels photo search failed for '{query}': {e}")
        return []


async def search_pixabay_videos(
    query: str, client: httpx.AsyncClient, per_page: int = 3
) -> list[MediaItem]:
    """Search Pixabay for videos."""
    if not settings.pixabay_api_key:
        return []

    try:
        response = await client.get(
            PIXABAY_VIDEO_URL,
            params={"key": settings.pixabay_api_key, "q": query, "per_page": per_page},
            timeout=10.0,
        )
        response.raise_for_status()
        data = response.json()

        items = []
        for hit in data.get("hits", []):
            videos = hit.get("videos", {})
            # Prefer medium quality
            medium = videos.get("medium", {})
            url = medium.get("url", "")
            if url:
                items.append(
                    MediaItem(
                        url=url,
                        media_type=MediaType.video,
                        source="pixabay",
                        query=query,
                        width=medium.get("width"),
                        height=medium.get("height"),
                    )
                )
        return items
    except Exception as e:
        logger.warning(f"Pixabay video search failed for '{query}': {e}")
        return []


async def search_pixabay_images(
    query: str, client: httpx.AsyncClient, per_page: int = 3
) -> list[MediaItem]:
    """Search Pixabay for images."""
    if not settings.pixabay_api_key:
        return []

    try:
        response = await client.get(
            PIXABAY_URL,
            params={
                "key": settings.pixabay_api_key,
                "q": query,
                "per_page": per_page,
                "image_type": "photo",
            },
            timeout=10.0,
        )
        response.raise_for_status()
        data = response.json()

        items = []
        for hit in data.get("hits", []):
            url = hit.get("largeImageURL", "")
            if url:
                items.append(
                    MediaItem(
                        url=url,
                        media_type=MediaType.image,
                        source="pixabay",
                        query=query,
                        width=hit.get("imageWidth"),
                        height=hit.get("imageHeight"),
                    )
                )
        return items
    except Exception as e:
        logger.warning(f"Pixabay image search failed for '{query}': {e}")
        return []


async def search_giphy(
    query: str, client: httpx.AsyncClient, limit: int = 3
) -> list[MediaItem]:
    """Search Giphy for GIFs."""
    if not settings.giphy_api_key:
        return []

    try:
        response = await client.get(
            GIPHY_URL,
            params={
                "api_key": settings.giphy_api_key,
                "q": query,
                "limit": limit,
                "rating": "g",
            },
            timeout=10.0,
        )
        response.raise_for_status()
        data = response.json()

        items = []
        for gif in data.get("data", []):
            images = gif.get("images", {})
            original = images.get("original", {})
            url = original.get("url", "")
            if url:
                items.append(
                    MediaItem(
                        url=url,
                        media_type=MediaType.gif,
                        source="giphy",
                        query=query,
                        width=int(original.get("width", 0)) or None,
                        height=int(original.get("height", 0)) or None,
                    )
                )
        return items
    except Exception as e:
        logger.warning(f"Giphy search failed for '{query}': {e}")
        return []


async def download_media(
    item: MediaItem, output_dir: Path, client: httpx.AsyncClient
) -> MediaItem:
    """Download a media item to the local filesystem.

    Args:
        item: The media item to download.
        output_dir: Directory to save the file.
        client: HTTP client for downloading.

    Returns:
        Updated MediaItem with local_path set.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    ext_map = {
        MediaType.video: ".mp4",
        MediaType.image: ".jpg",
        MediaType.gif: ".gif",
    }
    ext = ext_map.get(item.media_type, ".bin")
    filename = f"{uuid.uuid4().hex[:12]}{ext}"
    filepath = output_dir / filename

    try:
        response = await client.get(item.url, timeout=30.0, follow_redirects=True)
        response.raise_for_status()

        with open(filepath, "wb") as f:
            f.write(response.content)

        item.local_path = str(filepath)
        logger.info(f"Downloaded {item.media_type.value} from {item.source}: {filepath}")
    except Exception as e:
        logger.warning(f"Failed to download media from {item.url}: {e}")

    return item


async def source_media_for_scene(
    visual_description: str,
    scene_number: int,
    output_dir: Path,
    client: httpx.AsyncClient,
    preferred_type: Optional[MediaType] = None,
) -> SceneMedia:
    """Source media for a single scene with fallback logic.

    Tries multiple APIs in order: Pexels -> Pixabay -> Giphy.
    Downloads the best result locally.
    """
    keywords = _extract_keywords(visual_description)
    logger.info(f"Scene {scene_number}: searching for '{keywords}'")

    media_items: list[MediaItem] = []

    # Try video sources first, then images, then GIFs
    if preferred_type != MediaType.image:
        # Try Pexels videos
        items = await search_pexels_videos(keywords, client)
        media_items.extend(items)

        # Try Pixabay videos
        if not media_items:
            items = await search_pixabay_videos(keywords, client)
            media_items.extend(items)

    # Try images
    if not media_items or preferred_type == MediaType.image:
        items = await search_pexels_photos(keywords, client)
        media_items.extend(items)

        if not media_items:
            items = await search_pixabay_images(keywords, client)
            media_items.extend(items)

    # Try GIFs as fallback
    if not media_items:
        items = await search_giphy(keywords, client)
        media_items.extend(items)

    # Download the best item (first result)
    if media_items:
        scene_dir = output_dir / f"scene_{scene_number:03d}"
        media_items[0] = await download_media(media_items[0], scene_dir, client)

    return SceneMedia(scene_number=scene_number, media_items=media_items[:3])


async def source_media(
    script: VideoScript,
    preferred_type: Optional[MediaType] = None,
    output_dir: Optional[str] = None,
) -> list[SceneMedia]:
    """Source media for all scenes in a script concurrently.

    Uses asyncio.gather with a shared HTTP client and a semaphore to
    limit concurrency to 5 simultaneous scene-sourcing tasks, preventing
    API rate-limit issues on Pexels/Pixabay.

    Args:
        script: The video script.
        preferred_type: Optional preferred media type.
        output_dir: Optional output directory override.

    Returns:
        List of SceneMedia with sourced items per scene.
    """
    base_dir = Path(output_dir or settings.output_dir)
    media_dir = base_dir / "media" / str(uuid.uuid4())[:8]
    media_dir.mkdir(parents=True, exist_ok=True)

    semaphore = asyncio.Semaphore(5)

    async def _limited_source(scene):
        async with semaphore:
            return await source_media_for_scene(
                visual_description=scene.visual_description,
                scene_number=scene.scene_number,
                output_dir=media_dir,
                client=client,
                preferred_type=preferred_type,
            )

    async with httpx.AsyncClient() as client:
        tasks = [_limited_source(scene) for scene in script.scenes]
        results = await asyncio.gather(*tasks)

    logger.info(f"Media sourcing complete: {len(results)} scenes processed")
    return list(results)
