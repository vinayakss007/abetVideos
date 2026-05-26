"""Tests for script generator service."""

import json
from unittest.mock import AsyncMock, patch

import pytest

from app.models.schemas import VideoScript, VideoStyle
from app.services.script_generator import generate_script, _build_user_prompt


class TestBuildUserPrompt:
    def test_basic_prompt(self):
        prompt = _build_user_prompt("Python basics", 1.0, VideoStyle.educational)
        assert "Python basics" in prompt
        assert "60 seconds" in prompt
        assert "educational" in prompt

    def test_longer_duration(self):
        prompt = _build_user_prompt("History of Rome", 5.0, VideoStyle.documentary)
        assert "300 seconds" in prompt
        assert "5.0 minutes" in prompt
        assert "documentary" in prompt

    def test_different_styles(self):
        for style in VideoStyle:
            prompt = _build_user_prompt("Topic", 1.0, style)
            assert style.value in prompt


class TestGenerateScript:
    @pytest.mark.asyncio
    async def test_successful_generation(self):
        mock_response = {
            "title": "Understanding Python",
            "scenes": [
                {
                    "scene_number": 1,
                    "narration": "Welcome to this video about Python programming.",
                    "visual_description": "A laptop with Python code on screen",
                    "duration_seconds": 10.0,
                },
                {
                    "scene_number": 2,
                    "narration": "Python is one of the most popular languages.",
                    "visual_description": "Graph showing programming language popularity",
                    "duration_seconds": 15.0,
                },
                {
                    "scene_number": 3,
                    "narration": "Thanks for watching!",
                    "visual_description": "Subscribe button animation",
                    "duration_seconds": 5.0,
                },
            ],
            "total_duration": 30.0,
        }

        mock_gateway = AsyncMock()
        mock_gateway.chat_completion_json = AsyncMock(return_value=mock_response)

        script = await generate_script(
            topic="Python programming",
            duration_minutes=0.5,
            style=VideoStyle.educational,
            gateway=mock_gateway,
        )

        assert isinstance(script, VideoScript)
        assert script.title == "Understanding Python"
        assert len(script.scenes) == 3
        assert script.total_duration == 30.0
        assert script.scenes[0].narration == "Welcome to this video about Python programming."

        # Verify the gateway was called with correct parameters
        mock_gateway.chat_completion_json.assert_called_once()
        call_kwargs = mock_gateway.chat_completion_json.call_args[1]
        assert call_kwargs["temperature"] == 0.7

    @pytest.mark.asyncio
    async def test_invalid_response_raises_error(self):
        # Response missing required fields
        mock_response = {
            "title": "Test",
            # Missing 'scenes' and 'total_duration'
        }

        mock_gateway = AsyncMock()
        mock_gateway.chat_completion_json = AsyncMock(return_value=mock_response)

        with pytest.raises(ValueError, match="does not match expected script format"):
            await generate_script(
                topic="Test topic",
                gateway=mock_gateway,
            )

    @pytest.mark.asyncio
    async def test_gateway_error_propagates(self):
        mock_gateway = AsyncMock()
        mock_gateway.chat_completion_json = AsyncMock(
            side_effect=ValueError("Invalid JSON response from AI")
        )

        with pytest.raises(ValueError):
            await generate_script(
                topic="Test topic",
                gateway=mock_gateway,
            )

    @pytest.mark.asyncio
    async def test_messages_include_system_and_user(self):
        mock_response = {
            "title": "Test",
            "scenes": [
                {
                    "scene_number": 1,
                    "narration": "Test narration",
                    "visual_description": "Test visual",
                    "duration_seconds": 5.0,
                }
            ],
            "total_duration": 5.0,
        }

        mock_gateway = AsyncMock()
        mock_gateway.chat_completion_json = AsyncMock(return_value=mock_response)

        await generate_script(topic="Test", gateway=mock_gateway)

        call_kwargs = mock_gateway.chat_completion_json.call_args[1]
        messages = call_kwargs["messages"]
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert "Test" in messages[1]["content"]
