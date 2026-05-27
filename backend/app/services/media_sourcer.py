"""Media sourcing service - searches Pexels, Pixabay, Giphy, Unsplash, and Freesound for media.

Provides a pluggable provider system via the MediaProvider abstract base class
and MediaProviderRegistry. New providers can be added by subclassing
MediaProvider and registering with the registry.
"""

import asyncio
import json
import logging
import os
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

import httpx
from PIL import Image, ImageDraw, ImageFont

from app.config import settings
from app.models.schemas import MediaItem, MediaType, SceneMedia, VideoScript

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Abstract base class for media providers
# ---------------------------------------------------------------------------


class MediaProvider(ABC):
    """Abstract base class for media providers.

    Subclass this to add a new media source. Implement the `search` method
    and set the class-level attributes. Register your provider with the
    MediaProviderRegistry to make it available to the system.
    """

    name: str = ""
    supported_media_types: list[MediaType] = []

    @abstractmethod
    async def search(
        self, query: str, client: httpx.AsyncClient, per_page: int = 3
    ) -> list[MediaItem]:
        """Search this provider for media matching the query."""
        ...

    def is_configured(self) -> bool:
        """Return True if this provider has valid API credentials configured."""
        return False

    def get_status(self) -> dict:
        """Return provider status info for the API."""
        return {
            "name": self.name,
            "configured": self.is_configured(),
            "media_types": [mt.value for mt in self.supported_media_types],
        }


# ---------------------------------------------------------------------------
# Concrete provider implementations
# ---------------------------------------------------------------------------


class PexelsProvider(MediaProvider):
    """Pexels API provider for videos and photos."""

    name = "pexels"
    supported_media_types = [MediaType.video, MediaType.image]

    def is_configured(self) -> bool:
        return bool(settings.pexels_api_key)

    async def search(
        self, query: str, client: httpx.AsyncClient, per_page: int = 3
    ) -> list[MediaItem]:
        items: list[MediaItem] = []
        if not self.is_configured():
            return items
        video_items = await search_pexels_videos(query, client, per_page=per_page)
        photo_items = await search_pexels_photos(query, client, per_page=per_page)
        items.extend(video_items)
        items.extend(photo_items)
        return items


class PixabayProvider(MediaProvider):
    """Pixabay API provider for videos and images."""

    name = "pixabay"
    supported_media_types = [MediaType.video, MediaType.image]

    def is_configured(self) -> bool:
        return bool(settings.pixabay_api_key)

    async def search(
        self, query: str, client: httpx.AsyncClient, per_page: int = 3
    ) -> list[MediaItem]:
        items: list[MediaItem] = []
        if not self.is_configured():
            return items
        video_items = await search_pixabay_videos(query, client, per_page=per_page)
        image_items = await search_pixabay_images(query, client, per_page=per_page)
        items.extend(video_items)
        items.extend(image_items)
        return items


class GiphyProvider(MediaProvider):
    """Giphy API provider for GIFs."""

    name = "giphy"
    supported_media_types = [MediaType.gif]

    def is_configured(self) -> bool:
        return bool(settings.giphy_api_key)

    async def search(
        self, query: str, client: httpx.AsyncClient, per_page: int = 3
    ) -> list[MediaItem]:
        if not self.is_configured():
            return []
        return await search_giphy(query, client, limit=per_page)


class UnsplashProvider(MediaProvider):
    """Unsplash API provider for photos."""

    name = "unsplash"
    supported_media_types = [MediaType.image]

    def is_configured(self) -> bool:
        return bool(settings.unsplash_access_key)

    async def search(
        self, query: str, client: httpx.AsyncClient, per_page: int = 3
    ) -> list[MediaItem]:
        if not self.is_configured():
            return []
        return await search_unsplash(query, client, per_page=per_page)


class FreesoundProvider(MediaProvider):
    """Freesound API provider for audio/sound effects."""

    name = "freesound"
    supported_media_types = [MediaType.sound]

    def is_configured(self) -> bool:
        return bool(settings.freesound_api_key)

    async def search(
        self, query: str, client: httpx.AsyncClient, per_page: int = 3
    ) -> list[MediaItem]:
        if not self.is_configured():
            return []
        return await search_freesound(query, client, limit=per_page)


# ---------------------------------------------------------------------------
# Provider registry
# ---------------------------------------------------------------------------


class MediaProviderRegistry:
    """Registry that manages all media providers and handles fallback.

    Providers are tried in registration order. Only providers with valid
    API credentials are considered active. To add a new provider, create a
    class that extends MediaProvider and call registry.register(YourProvider()).
    """

    def __init__(self) -> None:
        self._providers: list[MediaProvider] = []

    def register(self, provider: MediaProvider) -> None:
        """Register a new media provider."""
        self._providers.append(provider)

    def get_all_providers(self) -> list[MediaProvider]:
        """Return all registered providers."""
        return list(self._providers)

    def get_active_providers(self) -> list[MediaProvider]:
        """Return only providers with valid API credentials."""
        return [p for p in self._providers if p.is_configured()]

    def get_providers_status(self) -> list[dict]:
        """Return status info for all registered providers."""
        return [p.get_status() for p in self._providers]

    async def search_all(
        self, query: str, client: httpx.AsyncClient, per_page: int = 2
    ) -> list[MediaItem]:
        """Search all active providers concurrently."""
        active = self.get_active_providers()
        if not active:
            return []

        tasks = [p.search(query, client, per_page=per_page) for p in active]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_items: list[MediaItem] = []
        for result in results:
            if isinstance(result, list):
                all_items.extend(result)
        return all_items

    async def search_with_fallback(
        self,
        query: str,
        client: httpx.AsyncClient,
        preferred_types: list[MediaType] | None = None,
        per_page: int = 3,
    ) -> list[MediaItem]:
        """Search providers with fallback - tries each active provider in order.

        If preferred_types is specified, providers supporting those types
        are tried first.
        """
        active = self.get_active_providers()
        if not active:
            return []

        # Sort providers: those matching preferred types first
        if preferred_types:
            preferred = [
                p for p in active
                if any(mt in p.supported_media_types for mt in preferred_types)
            ]
            others = [p for p in active if p not in preferred]
            ordered = preferred + others
        else:
            ordered = active

        for provider in ordered:
            try:
                items = await provider.search(query, client, per_page=per_page)
                if items:
                    return items
            except Exception as e:
                logger.warning(f"Provider {provider.name} failed: {e}")
                continue

        return []


# Global registry instance with all built-in providers
provider_registry = MediaProviderRegistry()
provider_registry.register(PexelsProvider())
provider_registry.register(PixabayProvider())
provider_registry.register(GiphyProvider())
provider_registry.register(UnsplashProvider())
provider_registry.register(FreesoundProvider())


def _register_ai_providers() -> None:
    """Register AI providers lazily to avoid circular imports."""
    from app.services.ai_image_provider import AIImageProvider
    from app.services.ai_video_provider import AIVideoProvider

    provider_registry.register(AIImageProvider())
    provider_registry.register(AIVideoProvider())


_register_ai_providers()

# Module-level lock for cache manifest read-modify-write operations
_cache_manifest_lock = asyncio.Lock()

# API endpoints
PEXELS_VIDEO_URL = "https://api.pexels.com/videos/search"
PEXELS_PHOTO_URL = "https://api.pexels.com/v1/search"
PIXABAY_URL = "https://pixabay.com/api/"
PIXABAY_VIDEO_URL = "https://pixabay.com/api/videos/"
GIPHY_URL = "https://api.giphy.com/v1/gifs/search"
UNSPLASH_SEARCH_URL = "https://api.unsplash.com/search/photos"
FREESOUND_SEARCH_URL = "https://freesound.org/apiv2/search/text/"


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


async def ai_extract_keywords(visual_description: str) -> str:
    """Extract optimal search keywords using the AI gateway.

    Uses the AI gateway to produce 3-5 search-optimized keywords
    from a visual description. Falls back to _extract_keywords on failure.
    """
    try:
        from app.services.ai_gateway import ai_gateway

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a media search keyword extractor. Given a visual description, "
                    "output 3-5 optimal search keywords separated by spaces. "
                    "Output ONLY the keywords, nothing else."
                ),
            },
            {
                "role": "user",
                "content": f"Extract search keywords from: {visual_description}",
            },
        ]
        result = await ai_gateway.chat_completion(
            messages=messages,
            temperature=0.3,
            max_tokens=50,
        )
        keywords = result.strip()
        if keywords:
            return keywords
    except Exception as e:
        logger.warning(f"AI keyword extraction failed, using fallback: {e}")

    return _extract_keywords(visual_description)


def filter_by_quality(
    items: list[MediaItem], min_width: int = 1280, min_height: int = 720
) -> list[MediaItem]:
    """Filter media items by minimum resolution.

    Items without width/height information pass through.
    """
    filtered = []
    for item in items:
        if item.width is None or item.height is None:
            filtered.append(item)
        elif item.width >= min_width and item.height >= min_height:
            filtered.append(item)
    return filtered


def _get_cache_manifest_path(output_dir: Path) -> Path:
    """Get the path to the media cache manifest file."""
    cache_dir = output_dir / "media_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / "manifest.json"


def _load_cache_manifest(manifest_path: Path) -> dict[str, str]:
    """Load the cache manifest from disk."""
    if manifest_path.exists():
        try:
            with open(manifest_path, "r") as f:
                return json.loads(f.read())
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _save_cache_manifest(manifest_path: Path, manifest: dict[str, str]) -> None:
    """Save the cache manifest to disk."""
    with open(manifest_path, "w") as f:
        f.write(json.dumps(manifest, indent=2))


async def search_unsplash(
    query: str, client: httpx.AsyncClient, per_page: int = 3
) -> list[MediaItem]:
    """Search Unsplash for photos."""
    if not settings.unsplash_access_key:
        return []

    try:
        response = await client.get(
            UNSPLASH_SEARCH_URL,
            params={"query": query, "per_page": per_page},
            headers={"Authorization": f"Client-ID {settings.unsplash_access_key}"},
            timeout=10.0,
        )
        response.raise_for_status()
        data = response.json()

        items = []
        for photo in data.get("results", []):
            urls = photo.get("urls", {})
            url = urls.get("regular", "")
            if url:
                items.append(
                    MediaItem(
                        url=url,
                        media_type=MediaType.image,
                        source="unsplash",
                        query=query,
                        width=photo.get("width"),
                        height=photo.get("height"),
                    )
                )
        return items
    except Exception as e:
        logger.warning(f"Unsplash search failed for '{query}': {e}")
        return []


async def search_freesound(
    query: str, client: httpx.AsyncClient, limit: int = 3
) -> list[MediaItem]:
    """Search Freesound for audio/sound effects."""
    if not settings.freesound_api_key:
        return []

    try:
        response = await client.get(
            FREESOUND_SEARCH_URL,
            params={
                "query": query,
                "token": settings.freesound_api_key,
                "fields": "id,name,previews,duration",
                "page_size": limit,
            },
            timeout=10.0,
        )
        response.raise_for_status()
        data = response.json()

        items = []
        for result in data.get("results", []):
            previews = result.get("previews", {})
            url = previews.get("preview-hq-mp3") or previews.get("preview-lq-mp3", "")
            if url:
                items.append(
                    MediaItem(
                        url=url,
                        media_type=MediaType.sound,
                        source="freesound",
                        query=query,
                    )
                )
        return items
    except Exception as e:
        logger.warning(f"Freesound search failed for '{query}': {e}")
        return []


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


def generate_text_on_background(
    visual_description: str,
    output_dir: Path,
    width: int = 1920,
    height: int = 1080,
) -> MediaItem:
    """Generate a text-on-background fallback image using PIL.

    Creates a dark gradient background with white text centered on it.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create gradient background (dark blue to dark purple)
    img = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(img)

    # Draw a vertical gradient
    for y in range(height):
        ratio = y / height
        r = int(20 + ratio * 30)
        g = int(20 + ratio * 10)
        b = int(40 + ratio * 40)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # Add text
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
    except (IOError, OSError):
        font = ImageFont.load_default()

    # Wrap text to fit the image
    max_chars_per_line = 40
    words = visual_description.split()
    lines = []
    current_line = ""
    for word in words:
        if len(current_line) + len(word) + 1 <= max_chars_per_line:
            current_line = f"{current_line} {word}" if current_line else word
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)

    # Draw text centered
    line_height = 60
    total_text_height = len(lines) * line_height
    start_y = (height - total_text_height) // 2

    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        x = (width - text_width) // 2
        y = start_y + i * line_height
        draw.text((x, y), line, fill=(255, 255, 255), font=font)

    filename = f"fallback_{uuid.uuid4().hex[:12]}.png"
    filepath = output_dir / filename
    img.save(filepath, "PNG")

    return MediaItem(
        url=f"file://{filepath}",
        local_path=str(filepath),
        media_type=MediaType.image,
        source="generated",
        query=visual_description[:50],
        width=width,
        height=height,
    )


async def download_media(
    item: MediaItem, output_dir: Path, client: httpx.AsyncClient
) -> MediaItem:
    """Download a media item to the local filesystem.

    Uses file-based caching with an asyncio.Lock to prevent race
    conditions when multiple coroutines update the manifest concurrently.

    Args:
        item: The media item to download.
        output_dir: Directory to save the file.
        client: HTTP client for downloading.

    Returns:
        Updated MediaItem with local_path set.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Check cache if enabled (under lock to avoid race conditions)
    if settings.media_cache_enabled:
        async with _cache_manifest_lock:
            manifest_path = _get_cache_manifest_path(output_dir)
            manifest = _load_cache_manifest(manifest_path)
            cached_path = manifest.get(item.url)
            if cached_path and Path(cached_path).exists():
                item.local_path = cached_path
                logger.info(f"Cache hit for {item.url}")
                return item

    ext_map = {
        MediaType.video: ".mp4",
        MediaType.image: ".jpg",
        MediaType.gif: ".gif",
        MediaType.sound: ".mp3",
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

        # Update cache manifest under lock
        if settings.media_cache_enabled:
            async with _cache_manifest_lock:
                manifest_path = _get_cache_manifest_path(output_dir)
                manifest = _load_cache_manifest(manifest_path)
                manifest[item.url] = str(filepath)
                _save_cache_manifest(manifest_path, manifest)

    except Exception as e:
        logger.warning(f"Failed to download media from {item.url}: {e}")

    return item


async def search_all_sources(
    query: str, client: httpx.AsyncClient, per_source: int = 2
) -> list[MediaItem]:
    """Search all media sources concurrently and return aggregated results.

    Returns up to 9 results across all sources.
    """
    tasks = [
        search_pexels_videos(query, client, per_page=per_source),
        search_pixabay_videos(query, client, per_page=per_source),
        search_unsplash(query, client, per_page=per_source),
        search_pexels_photos(query, client, per_page=per_source),
        search_pixabay_images(query, client, per_page=per_source),
        search_giphy(query, client, limit=per_source),
        search_freesound(query, client, limit=per_source),
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    all_items: list[MediaItem] = []
    for result in results:
        if isinstance(result, list):
            all_items.extend(result)

    return all_items[:9]


async def source_media_for_scene(
    visual_description: str,
    scene_number: int,
    output_dir: Path,
    client: httpx.AsyncClient,
    preferred_type: Optional[MediaType] = None,
    ai_generation_settings=None,
    ai_stats: Optional[dict] = None,
) -> SceneMedia:
    """Source media for a single scene with fallback logic.

    Fallback chain:
    1. Video sources (Pexels videos, Pixabay videos)
    2. Image sources (Unsplash, Pexels photos, Pixabay images)
    3. GIFs (Giphy)
    3.5a. AI image generation (if enabled and under limit)
    3.5b. AI video generation (if enabled and under limit)
    4. Text-on-background fallback using PIL
    """
    keywords = await ai_extract_keywords(visual_description)
    logger.info(f"Scene {scene_number}: searching for '{keywords}'")

    media_items: list[MediaItem] = []

    # Step 1: Try video sources
    if preferred_type != MediaType.image:
        items = await search_pexels_videos(keywords, client)
        media_items.extend(items)

        if not media_items:
            items = await search_pixabay_videos(keywords, client)
            media_items.extend(items)

    # Step 2: Try image sources
    if not media_items or preferred_type == MediaType.image:
        items = await search_unsplash(keywords, client)
        media_items.extend(items)

        if not media_items:
            items = await search_pexels_photos(keywords, client)
            media_items.extend(items)

        if not media_items:
            items = await search_pixabay_images(keywords, client)
            media_items.extend(items)

    # Step 3: Try GIFs as fallback
    if not media_items:
        items = await search_giphy(keywords, client)
        media_items.extend(items)

    # Step 3.5: AI generation fallback (before text-on-background)
    if not media_items and ai_generation_settings is not None and ai_stats is not None:
        # Step 3.5a: AI image generation
        if (
            ai_generation_settings.ai_image_enabled
            and ai_stats.get("ai_images_generated", 0) < ai_generation_settings.ai_image_max_per_video
        ):
            from app.services.ai_image_provider import AIImageProvider

            ai_image_provider = AIImageProvider(
                quality=ai_generation_settings.ai_image_quality.value
                if hasattr(ai_generation_settings.ai_image_quality, "value")
                else ai_generation_settings.ai_image_quality,
                size=ai_generation_settings.ai_image_size.value
                if hasattr(ai_generation_settings.ai_image_size, "value")
                else ai_generation_settings.ai_image_size,
            )
            if ai_image_provider.is_configured():
                items = await ai_image_provider.search(visual_description, client)
                if items:
                    media_items.extend(items)
                    ai_stats["ai_images_generated"] = ai_stats.get("ai_images_generated", 0) + 1

        # Step 3.5b: AI video generation
        if (
            not media_items
            and ai_generation_settings.ai_video_enabled
            and ai_stats.get("ai_videos_generated", 0) < ai_generation_settings.ai_video_max_per_video
        ):
            from app.services.ai_video_provider import AIVideoProvider

            ai_video_provider = AIVideoProvider()
            if ai_video_provider.is_configured():
                items = await ai_video_provider.search(visual_description, client)
                if items:
                    media_items.extend(items)
                    ai_stats["ai_videos_generated"] = ai_stats.get("ai_videos_generated", 0) + 1

    # Apply quality filter
    media_items = filter_by_quality(media_items)

    # Step 4: Text-on-background fallback
    if not media_items:
        scene_dir = output_dir / f"scene_{scene_number:03d}"
        fallback_item = generate_text_on_background(visual_description, scene_dir)
        media_items.append(fallback_item)

    # Download the best item (first result)
    if media_items and not media_items[0].local_path:
        scene_dir = output_dir / f"scene_{scene_number:03d}"
        media_items[0] = await download_media(media_items[0], scene_dir, client)

    return SceneMedia(scene_number=scene_number, media_items=media_items[:3])


async def source_media(
    script: VideoScript,
    preferred_type: Optional[MediaType] = None,
    output_dir: Optional[str] = None,
    ai_generation_settings=None,
) -> tuple[list[SceneMedia], dict]:
    """Source media for all scenes in a script concurrently.

    Uses asyncio.gather with a shared HTTP client and a semaphore to
    limit concurrency to 5 simultaneous scene-sourcing tasks, preventing
    API rate-limit issues on Pexels/Pixabay.

    Args:
        script: The video script.
        preferred_type: Optional preferred media type.
        output_dir: Optional output directory override.
        ai_generation_settings: Optional AI generation settings for fallback.

    Returns:
        List of SceneMedia with sourced items per scene.
    """
    base_dir = Path(output_dir or settings.output_dir)
    media_dir = base_dir / "media" / str(uuid.uuid4())[:8]
    media_dir.mkdir(parents=True, exist_ok=True)

    # Shared AI generation stats tracker
    ai_stats: dict = {"ai_images_generated": 0, "ai_videos_generated": 0}

    semaphore = asyncio.Semaphore(5)

    async def _limited_source(scene):
        async with semaphore:
            return await source_media_for_scene(
                visual_description=scene.visual_description,
                scene_number=scene.scene_number,
                output_dir=media_dir,
                client=client,
                preferred_type=preferred_type,
                ai_generation_settings=ai_generation_settings,
                ai_stats=ai_stats,
            )

    async with httpx.AsyncClient() as client:
        # Process scenes sequentially to properly track AI generation limits
        if ai_generation_settings is not None:
            results = []
            for scene in script.scenes:
                result = await _limited_source(scene)
                results.append(result)
        else:
            tasks = [_limited_source(scene) for scene in script.scenes]
            results = await asyncio.gather(*tasks)

    logger.info(f"Media sourcing complete: {len(results)} scenes processed")
    if ai_generation_settings is not None:
        logger.info(
            f"AI generation stats: {ai_stats['ai_images_generated']} images, "
            f"{ai_stats['ai_videos_generated']} videos"
        )
    return list(results), ai_stats
