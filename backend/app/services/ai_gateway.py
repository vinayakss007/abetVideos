"""OpenAI-compatible AI gateway supporting multiple providers with per-user API keys."""

import asyncio
import json
import logging
from typing import Any, Optional

import httpx
from openai import AsyncOpenAI, APIError, APIConnectionError, RateLimitError

from app.settings_manager import get_user_setting

logger = logging.getLogger(__name__)


class AIGateway:
    """Gateway for OpenAI-compatible API providers.

    Supports per-user API key and base URL via the settings context.
    If no per-user override exists, falls back to global settings.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        max_retries: int = 3,
    ):
        resolved_key = api_key or get_user_setting("openai_api_key") or "not-configured"
        resolved_url = base_url or get_user_setting("openai_base_url") or "https://api.openai.com/v1"
        resolved_model = model or get_user_setting("openai_model") or "gpt-4o-mini"

        self.api_key = resolved_key
        self.base_url = resolved_url
        self.model = resolved_model
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


ai_gateway = AIGateway()


def get_active_base_url() -> str:
    """Resolve the active base URL from user context or global settings."""
    return get_user_setting("openai_base_url") or "https://api.openai.com/v1"


def get_active_api_key() -> str:
    """Resolve the active API key from user context or global settings."""
    return get_user_setting("openai_api_key") or "not-configured"


async def fetch_available_models() -> list[dict[str, Any]]:
    """Fetch available models from the currently configured provider.

    Calls GET {base_url}/models using the configured API key.
    Falls back to an empty list on any error.
    """
    base_url = get_active_base_url().rstrip("/")
    api_key = get_active_api_key()
    headers = {"Authorization": f"Bearer {api_key}"} if api_key and api_key != "not-configured" else {}

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"{base_url}/models", headers=headers)
            resp.raise_for_status()
            data = resp.json()
            models = data.get("data", data) if isinstance(data, dict) else data
            if isinstance(models, list):
                return sorted(models, key=lambda m: m.get("id", ""))
            return []
    except Exception as e:
        logger.warning("Failed to fetch models from %s: %s", base_url, e)
        return []
