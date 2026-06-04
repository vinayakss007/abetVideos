"""Media sourcing service - per-user API keys via settings context."""

import asyncio
import json
import logging
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

import httpx
from PIL import Image, ImageDraw, ImageFont

from app.models.schemas import MediaItem, MediaType, SceneMedia, VideoScript
from app.settings_manager import get_user_setting

MAX_CONCURRENT_SOURCES = 5
HTTP_TIMEOUT = 10.0
KEYWORD_TEMPERATURE = 0.3

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Abstract base class
# ---------------------------------------------------------------------------


class MediaProvider(ABC):
    name: str = ""
    supported_media_types: list[MediaType] = []

    @abstractmethod
    async def search(
        self, query: str, client: httpx.AsyncClient, per_page: int = 3
    ) -> list[MediaItem]:
        ...

    def is_configured(self) -> bool:
        return False

    def get_status(self) -> dict:
        return {
            "name": self.name,
            "configured": self.is_configured(),
            "media_types": [mt.value for mt in self.supported_media_types],
        }


# ---------------------------------------------------------------------------
# Concrete providers
# ---------------------------------------------------------------------------


class PexelsProvider(MediaProvider):
    name = "pexels"
    supported_media_types = [MediaType.video, MediaType.image]

    def is_configured(self) -> bool:
        return bool(get_user_setting("pexels_api_key"))

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
    name = "pixabay"
    supported_media_types = [MediaType.video, MediaType.image]

    def is_configured(self) -> bool:
        return bool(get_user_setting("pixabay_api_key"))

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
    name = "giphy"
    supported_media_types = [MediaType.gif]

    def is_configured(self) -> bool:
        return bool(get_user_setting("giphy_api_key"))

    async def search(
        self, query: str, client: httpx.AsyncClient, per_page: int = 3
    ) -> list[MediaItem]:
        if not self.is_configured():
            return []
        return await search_giphy(query, client, limit=per_page)


class UnsplashProvider(MediaProvider):
    name = "unsplash"
    supported_media_types = [MediaType.image]

    def is_configured(self) -> bool:
        return bool(get_user_setting("unsplash_access_key"))

    async def search(
        self, query: str, client: httpx.AsyncClient, per_page: int = 3
    ) -> list[MediaItem]:
        if not self.is_configured():
            return []
        return await search_unsplash(query, client, per_page=per_page)


class FreesoundProvider(MediaProvider):
    name = "freesound"
    supported_media_types = [MediaType.sound]

    def is_configured(self) -> bool:
        return bool(get_user_setting("freesound_api_key"))

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
    def __init__(self) -> None:
        self._providers: list[MediaProvider] = []

    def register(self, provider: MediaProvider) -> None:
        self._providers.append(provider)

    def get_all_providers(self) -> list[MediaProvider]:
        return list(self._providers)

    def get_active_providers(self) -> list[MediaProvider]:
        return [p for p in self._providers if p.is_configured()]

    def get_providers_status(self) -> list[dict]:
        return [p.get_status() for p in self._providers]

    async def search_all(
        self, query: str, client: httpx.AsyncClient, per_page: int = 2
    ) -> list[MediaItem]:
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
        active = self.get_active_providers()
        if not active:
            return []
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


provider_registry = MediaProviderRegistry()
provider_registry.register(PexelsProvider())
provider_registry.register(PixabayProvider())
provider_registry.register(GiphyProvider())
provider_registry.register(UnsplashProvider())
provider_registry.register(FreesoundProvider())

_cache_manifest_lock = asyncio.Lock()

PEXELS_VIDEO_URL = "https://api.pexels.com/videos/search"
PEXELS_PHOTO_URL = "https://api.pexels.com/v1/search"
PIXABAY_URL = "https://pixabay.com/api/"
PIXABAY_VIDEO_URL = "https://pixabay.com/api/videos/"
GIPHY_URL = "https://api.giphy.com/v1/gifs/search"
UNSPLASH_SEARCH_URL = "https://api.unsplash.com/search/photos"
FREESOUND_SEARCH_URL = "https://freesound.org/apiv2/search/text/"
WIKIMEDIA_COMMONS_SEARCH_URL = "https://commons.wikimedia.org/w/api.php"
WIKIMEDIA_COMMONS_FILE_URL = "https://commons.wikimedia.org/w/api.php"
BING_IMAGE_SEARCH_URL = "https://api.bing.microsoft.com/v7.0/images/search"


def _extract_keywords(visual_description: str) -> str:
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
    return " ".join(keywords[:5])


async def ai_extract_keywords(visual_description: str) -> str:
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
            temperature=KEYWORD_TEMPERATURE,
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
    filtered = []
    for item in items:
        if item.width is None or item.height is None:
            filtered.append(item)
        elif item.width >= min_width and item.height >= min_height:
            filtered.append(item)
    return filtered


def _get_cache_manifest_path(output_dir: Path) -> Path:
    cache_dir = output_dir / "media_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / "manifest.json"


def _load_cache_manifest(manifest_path: Path) -> dict[str, str]:
    if manifest_path.exists():
        try:
            with open(manifest_path, "r") as f:
                return json.loads(f.read())
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _save_cache_manifest(manifest_path: Path, manifest: dict[str, str]) -> None:
    with open(manifest_path, "w") as f:
        f.write(json.dumps(manifest, indent=2))


async def search_unsplash(
    query: str, client: httpx.AsyncClient, per_page: int = 3
) -> list[MediaItem]:
    api_key = get_user_setting("unsplash_access_key")
    if not api_key:
        return []
    try:
        response = await client.get(
            UNSPLASH_SEARCH_URL,
            params={"query": query, "per_page": per_page},
            headers={"Authorization": f"Client-ID {api_key}"},
            timeout=HTTP_TIMEOUT,
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
    api_key = get_user_setting("freesound_api_key")
    if not api_key:
        return []
    try:
        response = await client.get(
            FREESOUND_SEARCH_URL,
            params={
                "query": query,
                "token": api_key,
                "fields": "id,name,previews,duration",
                "page_size": limit,
            },
            timeout=HTTP_TIMEOUT,
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
    api_key = get_user_setting("pexels_api_key")
    if not api_key:
        return []
    try:
        response = await client.get(
            PEXELS_VIDEO_URL,
            params={"query": query, "per_page": per_page, "size": "medium"},
            headers={"Authorization": api_key},
            timeout=HTTP_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        items = []
        for video in data.get("videos", []):
            video_files = video.get("video_files", [])
            if video_files:
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
    api_key = get_user_setting("pexels_api_key")
    if not api_key:
        return []
    try:
        response = await client.get(
            PEXELS_PHOTO_URL,
            params={"query": query, "per_page": per_page},
            headers={"Authorization": api_key},
            timeout=HTTP_TIMEOUT,
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
    api_key = get_user_setting("pixabay_api_key")
    if not api_key:
        return []
    try:
        response = await client.get(
            PIXABAY_VIDEO_URL,
            params={"key": api_key, "q": query, "per_page": per_page},
            timeout=HTTP_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        items = []
        for hit in data.get("hits", []):
            videos = hit.get("videos", {})
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
    api_key = get_user_setting("pixabay_api_key")
    if not api_key:
        return []
    try:
        response = await client.get(
            PIXABAY_URL,
            params={
                "key": api_key,
                "q": query,
                "per_page": per_page,
                "image_type": "photo",
            },
            timeout=HTTP_TIMEOUT,
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
    api_key = get_user_setting("giphy_api_key")
    if not api_key:
        return []
    try:
        response = await client.get(
            GIPHY_URL,
            params={
                "api_key": api_key,
                "q": query,
                "limit": limit,
                "rating": "g",
            },
            timeout=HTTP_TIMEOUT,
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


async def search_wikimedia_commons(
    query: str, client: httpx.AsyncClient, per_page: int = 3
) -> list[MediaItem]:
    headers = {"User-Agent": "abetVideos/1.0 (video generation bot; +https://github.com/abetVideos)"}
    try:
        params = {
            "action": "query",
            "list": "search",
            "srnamespace": 6,
            "srsearch": query,
            "format": "json",
            "srlimit": per_page,
        }
        response = await client.get(
            WIKIMEDIA_COMMONS_SEARCH_URL, params=params, headers=headers, timeout=HTTP_TIMEOUT
        )
        response.raise_for_status()
        data = response.json()
        titles = [r["title"] for r in data.get("query", {}).get("search", [])]
        if not titles:
            return []

        ii_params = {
            "action": "query",
            "titles": "|".join(titles),
            "prop": "imageinfo",
            "iiprop": "url|size",
            "format": "json",
        }
        ii_resp = await client.get(
            WIKIMEDIA_COMMONS_FILE_URL, params=ii_params, headers=headers, timeout=HTTP_TIMEOUT
        )
        ii_resp.raise_for_status()
        ii_data = ii_resp.json()
        items = []
        for pid, page in ii_data.get("query", {}).get("pages", {}).items():
            if int(pid) < 0:
                continue
            ii = page.get("imageinfo", [])
            if not ii:
                continue
            url = ii[0].get("url", "")
            if not url:
                continue
            items.append(
                MediaItem(
                    url=url,
                    media_type=MediaType.image,
                    source="wikimedia",
                    query=query,
                    width=ii[0].get("width"),
                    height=ii[0].get("height"),
                )
            )
        return items
    except Exception as e:
        logger.warning(f"Wikimedia Commons search failed for '{query}': {e}")
        return []


async def search_bing_images(
    query: str, client: httpx.AsyncClient, per_page: int = 3
) -> list[MediaItem]:
    api_key = get_user_setting("bing_api_key")
    if not api_key:
        return []
    try:
        response = await client.get(
            BING_IMAGE_SEARCH_URL,
            params={"q": query, "count": per_page, "mkt": "en-US"},
            headers={"Ocp-Apim-Subscription-Key": api_key},
            timeout=HTTP_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        items = []
        for value in data.get("value", []):
            content_url = value.get("contentUrl", "")
            if not content_url:
                continue
            items.append(
                MediaItem(
                    url=content_url,
                    media_type=MediaType.image,
                    source="bing",
                    query=query,
                    width=value.get("width"),
                    height=value.get("height"),
                )
            )
        return items
    except Exception as e:
        logger.warning(f"Bing image search failed for '{query}': {e}")
        return []


def generate_text_on_background(
    visual_description: str,
    output_dir: Path,
    width: int = 1920,
    height: int = 1080,
) -> MediaItem:
    output_dir.mkdir(parents=True, exist_ok=True)
    # Build gradient using numpy (avoids 1080 individual draw.line calls)
    import numpy as np
    ratio = np.arange(height) / height
    r = (20 + ratio * 30).astype(np.uint8).reshape(-1, 1)
    g = (20 + ratio * 10).astype(np.uint8).reshape(-1, 1)
    b = (40 + ratio * 40).astype(np.uint8).reshape(-1, 1)
    arr = np.broadcast_to(np.dstack((r, g, b)), (height, width, 3))
    img = Image.fromarray(arr, "RGB")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
    except (IOError, OSError):
        font = ImageFont.load_default(size=48)
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


DOWNLOAD_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
}


async def download_media(
    item: MediaItem, output_dir: Path, client: httpx.AsyncClient
) -> MediaItem:
    output_dir.mkdir(parents=True, exist_ok=True)
    if get_user_setting("media_cache_enabled") or True:
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
        response = await client.get(
            item.url, headers=DOWNLOAD_HEADERS, timeout=30.0, follow_redirects=True
        )
        response.raise_for_status()
        with open(filepath, "wb") as f:
            f.write(response.content)
        item.local_path = str(filepath)
        logger.info(f"Downloaded {item.media_type.value} from {item.source}: {filepath}")
        if get_user_setting("media_cache_enabled"):
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
) -> SceneMedia:
    keywords = await ai_extract_keywords(visual_description)
    logger.info(f"Scene {scene_number}: searching for '{keywords}'")
    media_items: list[MediaItem] = []

    if preferred_type != MediaType.image:
        items = await search_pexels_videos(keywords, client)
        media_items.extend(items)
        if not media_items:
            items = await search_pixabay_videos(keywords, client)
            media_items.extend(items)

    if not media_items or preferred_type == MediaType.image:
        items = await search_unsplash(keywords, client)
        media_items.extend(items)
        if not media_items:
            items = await search_pexels_photos(keywords, client)
            media_items.extend(items)
        if not media_items:
            items = await search_pixabay_images(keywords, client)
            media_items.extend(items)

    if not media_items:
        items = await search_giphy(keywords, client)
        media_items.extend(items)

    if not media_items:
        items = await search_wikimedia_commons(keywords, client)
        media_items.extend(items)

    if not media_items:
        items = await search_bing_images(keywords, client)
        media_items.extend(items)

    media_items = filter_by_quality(media_items)

    if not media_items:
        scene_dir = output_dir / f"scene_{scene_number:03d}"
        fallback_item = generate_text_on_background(visual_description, scene_dir)
        media_items.append(fallback_item)

    if media_items and not media_items[0].local_path:
        scene_dir = output_dir / f"scene_{scene_number:03d}"
        media_items[0] = await download_media(media_items[0], scene_dir, client)

    return SceneMedia(scene_number=scene_number, media_items=media_items[:3])


async def source_media(
    script: VideoScript,
    preferred_type: Optional[MediaType] = None,
    output_dir: Optional[str] = None,
) -> list[SceneMedia]:
    base_dir = Path(output_dir or get_user_setting("output_dir") or "./output")
    media_dir = base_dir / "media" / str(uuid.uuid4())[:8]
    media_dir.mkdir(parents=True, exist_ok=True)
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_SOURCES)

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
