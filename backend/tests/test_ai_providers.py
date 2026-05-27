"""Tests for AI generation providers and related schemas."""

import pytest
from pydantic import ValidationError
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.schemas import (
    AIGenerationSettings,
    AIGenerationStats,
    AIImageQuality,
    AIImageSize,
)


class TestAIGenerationSettings:
    def test_defaults(self):
        settings = AIGenerationSettings()
        assert settings.ai_image_enabled is True
        assert settings.ai_video_enabled is False
        assert settings.ai_image_max_per_video == 5
        assert settings.ai_video_max_per_video == 3
        assert settings.ai_image_quality == AIImageQuality.standard
        assert settings.ai_image_size == AIImageSize.size_1792x1024

    def test_custom_values(self):
        settings = AIGenerationSettings(
            ai_image_enabled=False,
            ai_video_enabled=True,
            ai_image_max_per_video=10,
            ai_video_max_per_video=5,
            ai_image_quality=AIImageQuality.hd,
            ai_image_size=AIImageSize.size_1024x1024,
        )
        assert settings.ai_image_enabled is False
        assert settings.ai_video_enabled is True
        assert settings.ai_image_max_per_video == 10
        assert settings.ai_video_max_per_video == 5
        assert settings.ai_image_quality == AIImageQuality.hd
        assert settings.ai_image_size == AIImageSize.size_1024x1024

    def test_boundary_max_per_video_zero(self):
        settings = AIGenerationSettings(ai_image_max_per_video=0, ai_video_max_per_video=0)
        assert settings.ai_image_max_per_video == 0
        assert settings.ai_video_max_per_video == 0

    def test_boundary_max_per_video_upper(self):
        settings = AIGenerationSettings(ai_image_max_per_video=20, ai_video_max_per_video=10)
        assert settings.ai_image_max_per_video == 20
        assert settings.ai_video_max_per_video == 10

    def test_image_max_exceeds_limit(self):
        with pytest.raises(ValidationError):
            AIGenerationSettings(ai_image_max_per_video=21)

    def test_video_max_exceeds_limit(self):
        with pytest.raises(ValidationError):
            AIGenerationSettings(ai_video_max_per_video=11)

    def test_image_max_negative(self):
        with pytest.raises(ValidationError):
            AIGenerationSettings(ai_image_max_per_video=-1)

    def test_video_max_negative(self):
        with pytest.raises(ValidationError):
            AIGenerationSettings(ai_video_max_per_video=-1)

    def test_invalid_quality(self):
        with pytest.raises(ValidationError):
            AIGenerationSettings(ai_image_quality="ultra")

    def test_invalid_size(self):
        with pytest.raises(ValidationError):
            AIGenerationSettings(ai_image_size="500x500")

    def test_all_image_sizes(self):
        for size in AIImageSize:
            settings = AIGenerationSettings(ai_image_size=size)
            assert settings.ai_image_size == size

    def test_all_image_qualities(self):
        for quality in AIImageQuality:
            settings = AIGenerationSettings(ai_image_quality=quality)
            assert settings.ai_image_quality == quality


class TestAIGenerationStats:
    def test_defaults(self):
        stats = AIGenerationStats()
        assert stats.ai_images_generated == 0
        assert stats.ai_videos_generated == 0
        assert stats.ai_image_limit == 5
        assert stats.ai_video_limit == 3

    def test_custom_values(self):
        stats = AIGenerationStats(
            ai_images_generated=3,
            ai_videos_generated=2,
            ai_image_limit=10,
            ai_video_limit=5,
        )
        assert stats.ai_images_generated == 3
        assert stats.ai_videos_generated == 2
        assert stats.ai_image_limit == 10
        assert stats.ai_video_limit == 5


class TestAIImageProviderConfigured:
    def test_is_configured_true(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "test-key-123")
        # Re-import to pick up env change
        from app.services.ai_image_provider import AIImageProvider
        from app.config import Settings

        with patch("app.services.ai_image_provider.settings", Settings(openai_api_key="test-key")):
            provider = AIImageProvider()
            assert provider.is_configured() is True

    def test_is_configured_false(self):
        from app.services.ai_image_provider import AIImageProvider
        from app.config import Settings

        with patch("app.services.ai_image_provider.settings", Settings(openai_api_key="")):
            provider = AIImageProvider()
            assert provider.is_configured() is False

    def test_provider_name(self):
        from app.services.ai_image_provider import AIImageProvider

        provider = AIImageProvider()
        assert provider.name == "ai_image"

    def test_provider_media_types(self):
        from app.services.ai_image_provider import AIImageProvider
        from app.models.schemas import MediaType

        provider = AIImageProvider()
        assert MediaType.image in provider.supported_media_types


class TestAIVideoProviderConfigured:
    def test_is_configured_true(self):
        from app.services.ai_video_provider import AIVideoProvider
        from app.config import Settings

        with patch("app.services.ai_video_provider.settings", Settings(replicate_api_token="test-token")):
            provider = AIVideoProvider()
            assert provider.is_configured() is True

    def test_is_configured_false(self):
        from app.services.ai_video_provider import AIVideoProvider
        from app.config import Settings

        with patch("app.services.ai_video_provider.settings", Settings(replicate_api_token="")):
            provider = AIVideoProvider()
            assert provider.is_configured() is False

    def test_provider_name(self):
        from app.services.ai_video_provider import AIVideoProvider

        provider = AIVideoProvider()
        assert provider.name == "ai_video"

    def test_provider_media_types(self):
        from app.services.ai_video_provider import AIVideoProvider
        from app.models.schemas import MediaType

        provider = AIVideoProvider()
        assert MediaType.video in provider.supported_media_types


class TestAISettingsEndpoint:
    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from app.main import app

        return TestClient(app)

    def test_ai_settings_returns_defaults(self, client):
        response = client.get("/api/videos/ai-settings")
        assert response.status_code == 200
        data = response.json()
        assert "ai_image_enabled" in data
        assert "ai_video_enabled" in data
        assert "ai_image_max_per_video" in data
        assert "ai_video_max_per_video" in data
        assert "ai_image_quality" in data
        assert "ai_image_size" in data

    def test_ai_settings_values_match_config(self, client, monkeypatch):
        from app.routers import videos
        from app.config import Settings

        mock_settings = Settings(
            ai_image_enabled=True,
            ai_video_enabled=False,
            ai_image_max_per_video=5,
            ai_video_max_per_video=3,
            ai_image_quality="standard",
            ai_image_size="1792x1024",
        )
        monkeypatch.setattr(videos, "settings", mock_settings)

        response = client.get("/api/videos/ai-settings")
        assert response.status_code == 200
        data = response.json()
        assert data["ai_image_enabled"] is True
        assert data["ai_video_enabled"] is False
        assert data["ai_image_max_per_video"] == 5
        assert data["ai_video_max_per_video"] == 3
        assert data["ai_image_quality"] == "standard"
        assert data["ai_image_size"] == "1792x1024"


class TestSourceMediaRequestWithAI:
    def test_request_with_ai_settings(self):
        from app.models.schemas import SourceMediaRequest, VideoScript, ScriptScene

        script = VideoScript(
            title="Test",
            scenes=[
                ScriptScene(
                    scene_number=1,
                    narration="Hello",
                    visual_description="Mountains",
                    duration_seconds=5.0,
                )
            ],
            total_duration=5.0,
        )
        ai_settings = AIGenerationSettings(ai_image_enabled=True)
        req = SourceMediaRequest(
            script=script, ai_generation_settings=ai_settings
        )
        assert req.ai_generation_settings is not None
        assert req.ai_generation_settings.ai_image_enabled is True

    def test_request_without_ai_settings(self):
        from app.models.schemas import SourceMediaRequest, VideoScript, ScriptScene

        script = VideoScript(
            title="Test",
            scenes=[
                ScriptScene(
                    scene_number=1,
                    narration="Hello",
                    visual_description="Mountains",
                    duration_seconds=5.0,
                )
            ],
            total_duration=5.0,
        )
        req = SourceMediaRequest(script=script)
        assert req.ai_generation_settings is None


class TestGenerateFullRequestWithAI:
    def test_request_with_ai_settings(self):
        from app.models.schemas import GenerateFullRequest

        ai_settings = AIGenerationSettings(ai_image_enabled=True, ai_video_enabled=True)
        req = GenerateFullRequest(
            topic="Space exploration",
            ai_generation_settings=ai_settings,
        )
        assert req.ai_generation_settings is not None
        assert req.ai_generation_settings.ai_video_enabled is True

    def test_request_without_ai_settings(self):
        from app.models.schemas import GenerateFullRequest

        req = GenerateFullRequest(topic="Space exploration")
        assert req.ai_generation_settings is None
