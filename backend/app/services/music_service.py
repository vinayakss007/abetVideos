"""Background music browser - curated royalty-free tracks + Pixabay Music search."""

import logging
from typing import Any

import httpx

from app.settings_manager import get_user_setting

HTTP_TIMEOUT = 10.0

logger = logging.getLogger(__name__)

CURATED_MUSIC: list[dict[str, Any]] = [
    {"id": "curated_01", "title": "Gentle Ambient", "mood": "calm", "duration": 180, "url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3", "source": "SoundHelix"},
    {"id": "curated_02", "title": "Soft Piano", "mood": "calm", "duration": 240, "url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3", "source": "SoundHelix"},
    {"id": "curated_03", "title": "Uplifting Pop", "mood": "happy", "duration": 200, "url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3", "source": "SoundHelix"},
    {"id": "curated_04", "title": "Energetic Rock", "mood": "energetic", "duration": 220, "url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-4.mp3", "source": "SoundHelix"},
    {"id": "curated_05", "title": "Cinematic Epic", "mood": "dramatic", "duration": 190, "url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-5.mp3", "source": "SoundHelix"},
    {"id": "curated_06", "title": "Chill Lo-Fi", "mood": "calm", "duration": 210, "url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-6.mp3", "source": "SoundHelix"},
    {"id": "curated_07", "title": "Happy Ukulele", "mood": "happy", "duration": 170, "url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-7.mp3", "source": "SoundHelix"},
    {"id": "curated_08", "title": "Inspiring Orchestra", "mood": "inspirational", "duration": 230, "url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-8.mp3", "source": "SoundHelix"},
    {"id": "curated_09", "title": "Corporate Tech", "mood": "professional", "duration": 180, "url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-9.mp3", "source": "SoundHelix"},
    {"id": "curated_10", "title": "Mysterious Dark", "mood": "mysterious", "duration": 200, "url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-10.mp3", "source": "SoundHelix"},
    {"id": "curated_11", "title": "Tropical Summer", "mood": "happy", "duration": 190, "url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-11.mp3", "source": "SoundHelix"},
    {"id": "curated_12", "title": "Acoustic Guitar", "mood": "calm", "duration": 210, "url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-12.mp3", "source": "SoundHelix"},
]

MOODS = ["calm", "happy", "energetic", "dramatic", "inspirational", "professional", "mysterious"]


async def search_music(query: str) -> list[dict[str, Any]]:
    """Search music from Pixabay API, fall back to curated list."""
    pixabay_key = get_user_setting("pixabay_api_key")
    if pixabay_key and pixabay_key != "your-pixabay-api-key":
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    "https://pixabay.com/api/music/",
                    params={"key": pixabay_key, "q": query, "per_page": 20},
                    timeout=HTTP_TIMEOUT,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    hits = data.get("hits", [])
                    results = []
                    for h in hits:
                        results.append({
                            "id": f"pixabay_{h.get('id')}",
                            "title": h.get("title", "Untitled"),
                            "mood": query.lower(),
                            "duration": h.get("duration", 0),
                            "url": h.get("url") or (h.get("previews", {}) or {}).get("mp3", ""),
                            "source": "Pixabay",
                        })
                    if results:
                        return results
        except Exception as e:
            logger.warning("Pixabay music search failed: %s", e)

    # Fall back to curated list filtered by query
    q = query.lower()
    results = [t for t in CURATED_MUSIC if q in t["mood"] or q in t["title"].lower()]
    if not results:
        results = CURATED_MUSIC[:6]
    return results
