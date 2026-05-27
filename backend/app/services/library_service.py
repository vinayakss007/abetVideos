"""Local media library service.

Manages user-uploaded media files (music, images, videos) with JSON metadata.
Files are stored in output/library/<category>/ directories.
"""

import json
import logging
import os
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from app.config import settings
from app.models.schemas import LibraryCategory, LibraryItem

logger = logging.getLogger(__name__)


class LibraryService:
    """Service for managing the local media library."""

    def __init__(self) -> None:
        self._base_dir = Path(settings.output_dir) / "library"
        self._metadata_path = self._base_dir / "metadata.json"
        self._lock = threading.Lock()

    def _ensure_dirs(self) -> None:
        """Ensure all library directories exist."""
        self._base_dir.mkdir(parents=True, exist_ok=True)
        (self._base_dir / "music").mkdir(parents=True, exist_ok=True)
        (self._base_dir / "images").mkdir(parents=True, exist_ok=True)
        (self._base_dir / "videos").mkdir(parents=True, exist_ok=True)

    def _category_dir(self, category: LibraryCategory) -> Path:
        """Get the directory for a given category."""
        dir_map = {
            LibraryCategory.music: "music",
            LibraryCategory.image: "images",
            LibraryCategory.video: "videos",
        }
        return self._base_dir / dir_map[category]

    def _load_metadata(self) -> list[dict]:
        """Load metadata from JSON file."""
        if not self._metadata_path.exists():
            return []
        try:
            with open(self._metadata_path, "r") as f:
                data = json.load(f)
            return data if isinstance(data, list) else []
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Failed to load library metadata: {e}")
            return []

    def _save_metadata(self, items: list[dict]) -> None:
        """Save metadata to JSON file."""
        self._ensure_dirs()
        with open(self._metadata_path, "w") as f:
            json.dump(items, f, indent=2)

    def add_item(
        self,
        file_bytes: bytes,
        filename: str,
        category: LibraryCategory,
        labels: list[str],
        description: str = "",
    ) -> LibraryItem:
        """Add a new item to the library.

        Args:
            file_bytes: Raw file content.
            filename: Original filename.
            category: Item category (music, image, video).
            labels: Searchable labels/tags.
            description: Optional description.

        Returns:
            The created LibraryItem.
        """
        self._ensure_dirs()

        item_id = uuid.uuid4().hex[:12]
        ext = Path(filename).suffix or ""
        stored_filename = f"{item_id}{ext}"

        cat_dir = self._category_dir(category)
        file_path = cat_dir / stored_filename

        with open(file_path, "wb") as f:
            f.write(file_bytes)

        item = LibraryItem(
            id=item_id,
            filename=stored_filename,
            original_filename=filename,
            category=category,
            labels=[label.strip().lower() for label in labels if label.strip()],
            description=description,
            file_path=str(file_path),
            created_at=datetime.now(timezone.utc).isoformat(),
            file_size=len(file_bytes),
        )

        with self._lock:
            metadata = self._load_metadata()
            metadata.append(item.model_dump())
            self._save_metadata(metadata)

        logger.info(f"Library item added: {item_id} ({category.value}/{stored_filename})")
        return item

    def list_items(
        self,
        category: Optional[LibraryCategory] = None,
        search: Optional[str] = None,
    ) -> list[LibraryItem]:
        """List library items with optional filtering.

        Args:
            category: Filter by category.
            search: Search query to filter by labels/description.

        Returns:
            List of matching LibraryItems.
        """
        metadata = self._load_metadata()
        items = [LibraryItem(**item) for item in metadata]

        if category is not None:
            items = [item for item in items if item.category == category]

        if search:
            query_lower = search.lower()
            items = [
                item for item in items
                if any(query_lower in label for label in item.labels)
                or query_lower in item.description.lower()
                or query_lower in item.original_filename.lower()
            ]

        return items

    def get_item(self, item_id: str) -> Optional[LibraryItem]:
        """Get a single library item by ID.

        Args:
            item_id: The item identifier.

        Returns:
            LibraryItem or None if not found.
        """
        metadata = self._load_metadata()
        for item_data in metadata:
            if item_data.get("id") == item_id:
                return LibraryItem(**item_data)
        return None

    def delete_item(self, item_id: str) -> bool:
        """Delete an item from the library.

        Removes both the file and metadata entry.

        Args:
            item_id: The item identifier.

        Returns:
            True if deleted, False if not found.
        """
        with self._lock:
            metadata = self._load_metadata()
            new_metadata = []
            deleted = False

            for item_data in metadata:
                if item_data.get("id") == item_id:
                    # Remove the file
                    file_path = item_data.get("file_path", "")
                    if file_path and os.path.exists(file_path):
                        try:
                            os.unlink(file_path)
                        except OSError as e:
                            logger.warning(f"Failed to delete file {file_path}: {e}")
                    deleted = True
                else:
                    new_metadata.append(item_data)

            if deleted:
                self._save_metadata(new_metadata)
                logger.info(f"Library item deleted: {item_id}")

        return deleted

    def search_items(self, query: str) -> list[LibraryItem]:
        """Search items by query matching against labels and description.

        Args:
            query: Search query string.

        Returns:
            List of matching LibraryItems.
        """
        return self.list_items(search=query)


# Global instance
library_service = LibraryService()
