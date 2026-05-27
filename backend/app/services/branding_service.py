"""Branding overlay service.

Manages branding configuration and image storage for video watermarks/logos.
Config is stored in output/branding/config.json.
"""

import json
import logging
import os
import uuid
from pathlib import Path
from typing import Optional

from app.config import settings
from app.models.schemas import BrandingConfig, BrandingPosition

logger = logging.getLogger(__name__)


class BrandingService:
    """Service for managing branding overlay configuration."""

    def __init__(self) -> None:
        self._base_dir = Path(settings.output_dir) / "branding"
        self._config_path = self._base_dir / "config.json"

    def _ensure_dirs(self) -> None:
        """Ensure branding directory exists."""
        self._base_dir.mkdir(parents=True, exist_ok=True)

    def _load_config(self) -> Optional[dict]:
        """Load branding config from JSON file."""
        if not self._config_path.exists():
            return None
        try:
            with open(self._config_path, "r") as f:
                data = json.load(f)
            return data if isinstance(data, dict) else None
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Failed to load branding config: {e}")
            return None

    def _save_config(self, config: dict) -> None:
        """Save branding config to JSON file."""
        self._ensure_dirs()
        with open(self._config_path, "w") as f:
            json.dump(config, f, indent=2)

    def upload_branding(
        self,
        file_bytes: bytes,
        filename: str,
        position: BrandingPosition = BrandingPosition.bottom_right,
        size_percent: float = 15.0,
        opacity: float = 0.8,
    ) -> BrandingConfig:
        """Upload a branding image and create/update config.

        Args:
            file_bytes: Raw image file content.
            filename: Original filename.
            position: Position on the video.
            size_percent: Size as percentage of video width.
            opacity: Branding opacity.

        Returns:
            The created BrandingConfig.
        """
        self._ensure_dirs()

        # Remove old branding image if exists
        old_config = self._load_config()
        if old_config and old_config.get("image_path"):
            old_path = old_config["image_path"]
            if os.path.exists(old_path):
                try:
                    os.unlink(old_path)
                except OSError:
                    pass

        config_id = uuid.uuid4().hex[:12]
        ext = Path(filename).suffix or ".png"
        stored_filename = f"branding_{config_id}{ext}"
        file_path = self._base_dir / stored_filename

        with open(file_path, "wb") as f:
            f.write(file_bytes)

        config = BrandingConfig(
            id=config_id,
            image_path=str(file_path),
            position=position,
            size_percent=size_percent,
            opacity=opacity,
            enabled=True,
        )

        self._save_config(config.model_dump())
        logger.info(f"Branding uploaded: {config_id} ({stored_filename})")
        return config

    def get_config(self) -> Optional[BrandingConfig]:
        """Get current branding configuration.

        Returns:
            BrandingConfig or None if not configured.
        """
        data = self._load_config()
        if data is None:
            return None
        try:
            return BrandingConfig(**data)
        except Exception as e:
            logger.warning(f"Invalid branding config: {e}")
            return None

    def update_config(
        self,
        position: Optional[BrandingPosition] = None,
        size_percent: Optional[float] = None,
        opacity: Optional[float] = None,
        enabled: Optional[bool] = None,
    ) -> Optional[BrandingConfig]:
        """Update branding configuration settings.

        Args:
            position: New position (optional).
            size_percent: New size percentage (optional).
            opacity: New opacity (optional).
            enabled: Enable/disable (optional).

        Returns:
            Updated BrandingConfig or None if no config exists.
        """
        data = self._load_config()
        if data is None:
            return None

        if position is not None:
            data["position"] = position.value
        if size_percent is not None:
            data["size_percent"] = size_percent
        if opacity is not None:
            data["opacity"] = opacity
        if enabled is not None:
            data["enabled"] = enabled

        self._save_config(data)
        return BrandingConfig(**data)

    def delete_branding(self) -> bool:
        """Delete branding configuration and image.

        Returns:
            True if deleted, False if nothing to delete.
        """
        data = self._load_config()
        if data is None:
            return False

        # Remove image file
        image_path = data.get("image_path", "")
        if image_path and os.path.exists(image_path):
            try:
                os.unlink(image_path)
            except OSError as e:
                logger.warning(f"Failed to delete branding image: {e}")

        # Remove config file
        if self._config_path.exists():
            try:
                os.unlink(self._config_path)
            except OSError as e:
                logger.warning(f"Failed to delete branding config: {e}")
                return False

        logger.info("Branding deleted")
        return True


# Global instance
branding_service = BrandingService()
