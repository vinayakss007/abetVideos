"""OpenAI-compatible AI gateway supporting multiple providers."""

import asyncio
import json
import logging
from typing import Any, Optional

from openai import AsyncOpenAI, APIError, APIConnectionError, RateLimitError

from app.config import settings

logger = logging.getLogger(__name__)


class AIGateway:
    """Gateway for OpenAI-compatible API providers.

    Supports OpenAI, Groq, Ollama, and any OpenAI-compatible endpoint
    by configuring base_url and api_key.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        max_retries: int = 3,
    ):
        self.api_key = api_key or settings.openai_api_key or "not-configured"
        self.base_url = base_url or settings.openai_base_url
        self.model = model or settings.openai_model
        self.max_retries = max_retries

        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
        )

    async def chat_completion(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        json_mode: bool = False,
    ) -> str:
        """Send a chat completion request with retry logic.

        Args:
            messages: List of message dicts with 'role' and 'content'.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens in response.
            json_mode: Whether to request JSON output format.

        Returns:
            The assistant's response content as a string.

        Raises:
            APIError: If all retries are exhausted.
        """
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        last_error: Optional[Exception] = None

        for attempt in range(self.max_retries):
            try:
                response = await self.client.chat.completions.create(**kwargs)
                content = response.choices[0].message.content
                if content is None:
                    raise APIError(
                        message="Empty response from API",
                        request=None,
                        body=None,
                    )
                return content
            except RateLimitError as e:
                last_error = e
                wait_time = 2 ** (attempt + 1)
                logger.warning(
                    f"Rate limited (attempt {attempt + 1}/{self.max_retries}), "
                    f"waiting {wait_time}s..."
                )
                await asyncio.sleep(wait_time)
            except APIConnectionError as e:
                last_error = e
                wait_time = 2**attempt
                logger.warning(
                    f"Connection error (attempt {attempt + 1}/{self.max_retries}), "
                    f"waiting {wait_time}s..."
                )
                await asyncio.sleep(wait_time)
            except APIError as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    wait_time = 2**attempt
                    logger.warning(
                        f"API error (attempt {attempt + 1}/{self.max_retries}): {e}, "
                        f"waiting {wait_time}s..."
                    )
                    await asyncio.sleep(wait_time)
                else:
                    raise

        raise last_error or APIError(
            message="All retries exhausted", request=None, body=None
        )

    async def chat_completion_json(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> dict[str, Any]:
        """Send a chat completion request expecting JSON response.

        Args:
            messages: List of message dicts with 'role' and 'content'.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens in response.

        Returns:
            Parsed JSON response as a dictionary.
        """
        content = await self.chat_completion(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            json_mode=True,
        )

        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {content[:200]}")
            raise ValueError(f"Invalid JSON response from AI: {e}") from e


# Default gateway instance
ai_gateway = AIGateway()
