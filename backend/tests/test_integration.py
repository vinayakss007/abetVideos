"""Integration tests for the full video generation pipeline."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import Depends
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.models.schemas import (
    MediaItem,
    MediaType,
    SceneMedia,
    TTSResult,
    VideoFormat,
    VideoResult,
    VideoScript,
)


@pytest.fixture
def mock_script():
    """A sample VideoScript for testing."""
    return VideoScript(
        title="Test Video",
        scenes=[
            {
                "scene_number": 1,
                "narration": "Welcome to this test video.",
                "visual_description": "A computer screen with code",
                "duration_seconds": 10.0,
            },
            {
                "scene_number": 2,
                "narration": "This is the second scene.",
                "visual_description": "Nature landscape with mountains",
                "duration_seconds": 10.0,
            },
        ],
        total_duration=20.0,
    )


@pytest.fixture
def mock_tts_results():
    """Sample TTS results."""
    return [
        TTSResult(scene_number=1, audio_path="/tmp/audio/scene_001.mp3", duration_seconds=8.0),
        TTSResult(scene_number=2, audio_path="/tmp/audio/scene_002.mp3", duration_seconds=9.0),
    ]


@pytest.fixture
def mock_scene_media():
    """Sample scene media."""
    return [
        SceneMedia(
            scene_number=1,
            media_items=[
                MediaItem(
                    url="https://example.com/video1.mp4",
                    media_type=MediaType.video,
                    source="pexels",
                    query="computer code",
                    local_path="/tmp/media/video1.mp4",
                )
            ],
        ),
        SceneMedia(
            scene_number=2,
            media_items=[
                MediaItem(
                    url="https://example.com/image1.jpg",
                    media_type=MediaType.image,
                    source="pixabay",
                    query="nature mountains",
                    local_path="/tmp/media/image1.jpg",
                )
            ],
        ),
    ]


@pytest.fixture
def mock_video_result():
    """Sample video result."""
    return VideoResult(
        video_id="abc123def456",
        video_path="/tmp/output/videos/abc123def456.mp4",
        duration_seconds=17.0,
        scenes_count=2,
        format=VideoFormat.landscape,
    )


class TestGenerateScriptEndpoint:
    """Tests for POST /api/videos/generate-script."""

    async def test_generate_script_success(self, mock_script):
        """Test successful script generation."""
        with patch(
            "app.routers.videos.generate_script",
            new_callable=AsyncMock,
            return_value=mock_script,
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/videos/generate-script",
                    json={
                        "topic": "Python programming",
                        "duration_minutes": 1.0,
                        "style": "educational",
                    },
                )

            assert response.status_code == 200
            data = response.json()
            assert data["title"] == "Test Video"
            assert len(data["scenes"]) == 2

    async def test_generate_script_invalid_topic(self):
        """Test validation error for short topic."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/videos/generate-script",
                json={
                    "topic": "ab",
                    "duration_minutes": 1.0,
                    "style": "educational",
                },
            )

        assert response.status_code == 422


class TestGenerateTTSEndpoint:
    """Tests for POST /api/videos/generate-tts."""

    async def test_generate_tts_success(self, mock_script, mock_tts_results):
        """Test successful TTS generation."""
        with patch(
            "app.routers.videos.generate_tts",
            new_callable=AsyncMock,
            return_value=mock_tts_results,
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/videos/generate-tts",
                    json={"script": mock_script.model_dump()},
                )

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["scene_number"] == 1


class TestSourceMediaEndpoint:
    """Tests for POST /api/videos/source-media."""

    async def test_source_media_success(self, mock_script, mock_scene_media):
        """Test successful media sourcing."""
        with patch(
            "app.routers.videos.source_media",
            new_callable=AsyncMock,
            return_value=mock_scene_media,
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/videos/source-media",
                    json={"script": mock_script.model_dump()},
                )

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["scene_number"] == 1


class TestAssembleEndpoint:
    """Tests for POST /api/videos/assemble."""

    async def test_assemble_success(
        self, mock_script, mock_tts_results, mock_scene_media, mock_video_result
    ):
        """Test successful video assembly."""
        with patch(
            "app.routers.videos.assemble_video",
            new_callable=AsyncMock,
            return_value=mock_video_result,
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/videos/assemble",
                    json={
                        "script": mock_script.model_dump(),
                        "tts_results": [r.model_dump() for r in mock_tts_results],
                        "scene_media": [m.model_dump() for m in mock_scene_media],
                    },
                )

            assert response.status_code == 200
            data = response.json()
            assert data["video_id"] == "abc123def456"
            assert data["scenes_count"] == 2


class TestGenerateFullSSE:
    """Tests for POST /api/videos/generate-full (SSE endpoint)."""

    async def test_generate_full_streams_events(
        self, mock_script, mock_tts_results, mock_scene_media, mock_video_result
    ):
        """Test that the full pipeline returns a task and streams SSE events."""
        with patch(
            "app.routers.videos.generate_script",
            new_callable=AsyncMock,
            return_value=mock_script,
        ), patch(
            "app.routers.videos.generate_tts",
            new_callable=AsyncMock,
            return_value=mock_tts_results,
        ), patch(
            "app.routers.videos.source_media",
            new_callable=AsyncMock,
            return_value=mock_scene_media,
        ), patch(
            "app.routers.videos.assemble_video",
            new_callable=AsyncMock,
            return_value=mock_video_result,
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/videos/generate-full",
                    json={
                        "topic": "Python programming",
                        "duration_minutes": 1.0,
                        "style": "educational",
                    },
                )

            assert response.status_code == 200
            data = response.json()
            assert "task_id" in data
            assert data["status"] == "pending"

            # Now connect to the SSE stream
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                stream_resp = await client.get(f"/api/videos/tasks/{data['task_id']}/stream")
            assert stream_resp.status_code == 200

            # Parse SSE events
            events = []
            for line in stream_resp.text.split("\n"):
                if line.startswith("data: "):
                    event_data = json.loads(line[6:])
                    events.append(event_data)
            assert len(events) >= 1

    async def test_generate_full_error_handling(self):
        """Test that errors are handled gracefully."""
        with patch(
            "app.routers.videos.generate_script",
            new_callable=AsyncMock,
            side_effect=Exception("LLM API unavailable"),
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/videos/generate-full",
                    json={
                        "topic": "Python programming",
                        "duration_minutes": 1.0,
                        "style": "educational",
                    },
                )

            assert response.status_code == 200
            data = response.json()
            assert "task_id" in data

    async def test_generate_full_validation(self):
        """Test request validation for the full pipeline."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/videos/generate-full",
                json={
                    "topic": "ab",
                    "duration_minutes": 1.0,
                    "style": "educational",
                },
            )

        assert response.status_code == 422


import time

@pytest.fixture
def clear_auth_override():
    app.dependency_overrides.clear()
    yield
    from app.auth.dependencies import get_current_user
    async def _mock():
        return {"user_id": "test_user", "email": "test@example.com", "full_name": "Test User"}
    app.dependency_overrides[get_current_user] = _mock


class TestProfileEndpoint:
    """Tests for the profile update endpoint."""

    async def test_update_profile_name(self, clear_auth_override):
        email = f"profile_name_{time.time_ns()}@example.com"
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            signup_resp = await client.post(
                "/api/auth/signup",
                json={"email": email, "password": "test_pass", "full_name": "Initial Name"},
            )
            assert signup_resp.status_code == 200, signup_resp.text
            token = signup_resp.json()["token"]

            response = await client.put(
                "/api/auth/profile",
                json={"full_name": "Updated Name"},
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Updated Name"
        assert data["email"] == email

    async def test_update_profile_email(self, clear_auth_override):
        email = f"profile_email_{time.time_ns()}@example.com"
        new_email = f"profile_email_new_{time.time_ns()}@example.com"
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            signup_resp = await client.post(
                "/api/auth/signup",
                json={"email": email, "password": "test_pass", "full_name": "Test"},
            )
            assert signup_resp.status_code == 200
            token = signup_resp.json()["token"]

            response = await client.put(
                "/api/auth/profile",
                json={"email": new_email},
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 200
        assert response.json()["email"] == new_email

    async def test_update_profile_password(self, clear_auth_override):
        email = f"profile_pw_{time.time_ns()}@example.com"
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            signup_resp = await client.post(
                "/api/auth/signup",
                json={"email": email, "password": "test_pass", "full_name": "Test"},
            )
            assert signup_resp.status_code == 200
            token = signup_resp.json()["token"]

            resp = await client.put(
                "/api/auth/profile",
                json={"current_password": "test_pass", "new_password": "new_pass_456"},
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code == 200

            login_resp = await client.post(
                "/api/auth/login",
                json={"email": email, "password": "new_pass_456"},
            )
            assert login_resp.status_code == 200


class TestHealthEndpoint:
    """Tests for the health check endpoint."""

    async def test_health_check(self):
        """Test that the health endpoint responds."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ("ok", "degraded")
        assert "checks" in data
        assert data["service"] == "abet-videos-backend"
