"""AI Video generation provider using Replicate API."""

import asyncio
import logging
import uuid
from pathlib import Path

import httpx

from app.config import settings
from app.models.schemas import MediaItem, MediaType
from app.services.media_sourcer import MediaProvider

logger = logging.getLogger(__name__)

REPLICATE_API_URL = "https://api.replicate.com/v1/predictions"
REPLICATE_MODEL_VERSION = (
    "stability-ai/stable-video-diffusion:"
    "3f0457e4619daac51203dedb472816fd4af51f3149fa7a9e0b5ffcf1b8172438"
)


class AIVideoProvider(MediaProvider):
    """AI video generation provider using Replicate API.

    Uses Stable Video Diffusion via Replicate to generate short video clips
    from text prompts. Requires a valid Replicate API token.
    """

    name = "ai_video"
    supported_media_types = [MediaType.video]

    def is_configured(self) -> bool:
        """Check if the Replicate API token is configured."""
        return bool(settings.replicate_api_token)

    async def search(
        self, query: str, client: httpx.AsyncClient, per_page: int = 1
    ) -> list[MediaItem]:
        """Generate an AI video based on the query.

        Args:
            query: The prompt/description for video generation.
            client: HTTP client for API calls and downloading.
            per_page: Number of videos to generate (capped at 1 for cost).

        Returns:
            List containing the generated MediaItem, or empty list on failure.
        """
        if not self.is_configured():
            return []

        try:
            # Create a prediction
            headers = {
                "Authorization": f"Token {settings.replicate_api_token}",
                "Content-Type": "application/json",
            }

            payload = {
                "version": REPLICATE_MODEL_VERSION.split(":")[1],
                "input": {
                    "prompt": query,
                    "num_frames": 25,
                    "num_inference_steps": 25,
                    "width": 1024,
                    "height": 576,
                },
            }

            response = await client.post(
                REPLICATE_API_URL,
                json=payload,
                headers=headers,
                timeout=30.0,
            )
            response.raise_for_status()
            prediction = response.json()

            prediction_id = prediction.get("id")
            if not prediction_id:
                logger.warning("Replicate prediction returned no ID")
                return []

            # Poll for completion
            poll_url = f"{REPLICATE_API_URL}/{prediction_id}"
            max_attempts = 60  # Up to 5 minutes of polling
            for _ in range(max_attempts):
                await asyncio.sleep(5)
                poll_response = await client.get(
                    poll_url, headers=headers, timeout=15.0
                )
                poll_response.raise_for_status()
                status_data = poll_response.json()

                status = status_data.get("status")
                if status == "succeeded":
                    output = status_data.get("output")
                    if not output:
                        logger.warning("Replicate prediction succeeded but no output")
                        return []

                    # Output is typically a URL or list of URLs
                    video_url = output if isinstance(output, str) else output[0]

                    # Download the generated video
                    output_dir = Path(settings.output_dir) / "media" / "ai_generated"
                    output_dir.mkdir(parents=True, exist_ok=True)
                    filename = f"ai_vid_{uuid.uuid4().hex[:12]}.mp4"
                    filepath = output_dir / filename

                    dl_response = await client.get(
                        video_url, timeout=60.0, follow_redirects=True
                    )
                    dl_response.raise_for_status()

                    with open(filepath, "wb") as f:
                        f.write(dl_response.content)

                    logger.info(f"AI video generated and saved: {filepath}")

                    return [
                        MediaItem(
                            url=video_url,
                            local_path=str(filepath),
                            media_type=MediaType.video,
                            source="ai_generated",
                            query=query[:100],
                            width=1024,
                            height=576,
                        )
                    ]

                elif status == "failed":
                    error = status_data.get("error", "Unknown error")
                    logger.warning(f"Replicate prediction failed: {error}")
                    return []

                elif status == "canceled":
                    logger.warning("Replicate prediction was canceled")
                    return []

            logger.warning("Replicate prediction timed out after polling")
            return []

        except Exception as e:
            logger.warning(f"AI video generation failed for '{query}': {e}")
            return []
