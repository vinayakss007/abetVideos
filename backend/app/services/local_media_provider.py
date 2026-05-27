"""Local media library provider.

Implements the MediaProvider interface to search the local library
before hitting external APIs. This provider is registered first in the
registry so user-uploaded media takes priority.
"""

import logging
from typing import Optional

import httpx

from app.models.schemas import MediaItem, MediaType
from app.services.media_sourcer import MediaProvider

logger = logging.getLogger(__name__)


class LocalMediaProvider(MediaProvider):
    """Media provider that searches the local media library.

    Matches query words against item labels using case-insensitive
    substring matching. Returns MediaItems with local_path already set.
    """

    name = "local_library"
    supported_media_types = [MediaType.video, MediaType.image]

    def is_configured(self) -> bool:
        """Return True if the library metadata file exists and has items."""
        try:
            from app.services.library_service import library_service
            items = library_service.list_items()
            return len(items) > 0
        except Exception:
            return False

    async def search(
        self, query: str, client: httpx.AsyncClient, per_page: int = 3
    ) -> list[MediaItem]:
        """Search local library for media matching the query.

        Matches query words against item labels and description using
        case-insensitive substring matching.
        """
        try:
            from app.services.library_service import library_service

            query_words = query.lower().split()
            if not query_words:
                return []

            all_items = library_service.list_items()
            matched = []

            for item in all_items:
                # Only return images and videos (not music)
                if item.category.value not in ("image", "video"):
                    continue

                # Check if any query word matches any label or the description
                item_text = " ".join(item.labels) + " " + item.description.lower()
                for word in query_words:
                    if word in item_text:
                        matched.append(item)
                        break

            # Convert to MediaItem objects
            results: list[MediaItem] = []
            for lib_item in matched[:per_page]:
                media_type = (
                    MediaType.video if lib_item.category.value == "video"
                    else MediaType.image
                )
                results.append(
                    MediaItem(
                        url=f"file://{lib_item.file_path}",
                        local_path=lib_item.file_path,
                        media_type=media_type,
                        source="local_library",
                        query=query,
                    )
                )

            if results:
                logger.info(f"Local library matched {len(results)} items for '{query}'")

            return results
        except Exception as e:
            logger.warning(f"Local library search failed: {e}")
            return []
