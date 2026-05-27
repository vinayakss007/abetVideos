"""AI Image generation provider using OpenAI-compatible API (via OpenRouter)."""

import logging
import uuid
from pathlib import Path

import httpx
from openai import AsyncOpenAI

from app.config import settings
from app.models.schemas import MediaItem, MediaType
from app.services.media_sourcer import MediaProvider

logger = logging.getLogger(__name__)


class AIImageProvider(MediaProvider):
    """AI image generation provider using OpenAI images.generate API.

    Uses the configured OpenRouter/OpenAI-compatible endpoint to generate
    images via DALL-E 3 or equivalent models.
    """

    name = "ai_image"
    supported_media_types = [MediaType.image]

    def __init__(self, quality: str = "standard", size: str = "1792x1024") -> None:
        self.quality = quality
        self.size = size

    def is_configured(self) -> bool:
        """Check if the OpenAI API key is configured."""
        return bool(settings.openai_api_key)

    async def search(
        self, query: str, client: httpx.AsyncClient, per_page: int = 1
    ) -> list[MediaItem]:
        """Generate an AI image based on the query.

        Args:
            query: The prompt/description for image generation.
            client: HTTP client for downloading the generated image.
            per_page: Number of images to generate (capped at 1 for cost).

        Returns:
            List containing the generated MediaItem, or empty list on failure.
        """
        if not self.is_configured():
            return []

        try:
            openai_client = AsyncOpenAI(
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url,
            )

            response = await openai_client.images.generate(
                model="dall-e-3",
                prompt=query,
                n=1,
                size=self.size,
                quality=self.quality,
            )

            if not response.data:
                logger.warning("AI image generation returned no data")
                return []

            image_url = response.data[0].url
            if not image_url:
                logger.warning("AI image generation returned no URL")
                return []

            # Download the generated image to local storage
            output_dir = Path(settings.output_dir) / "media" / "ai_generated"
            output_dir.mkdir(parents=True, exist_ok=True)
            filename = f"ai_img_{uuid.uuid4().hex[:12]}.png"
            filepath = output_dir / filename

            dl_response = await client.get(image_url, timeout=60.0, follow_redirects=True)
            dl_response.raise_for_status()

            with open(filepath, "wb") as f:
                f.write(dl_response.content)

            logger.info(f"AI image generated and saved: {filepath}")

            return [
                MediaItem(
                    url=image_url,
                    local_path=str(filepath),
                    media_type=MediaType.image,
                    source="ai_generated",
                    query=query[:100],
                    width=int(self.size.split("x")[0]),
                    height=int(self.size.split("x")[1]),
                )
            ]

        except Exception as e:
            logger.warning(f"AI image generation failed for '{query}': {e}")
            return []
