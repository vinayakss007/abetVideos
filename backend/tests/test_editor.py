"""Tests for editor schemas and API endpoints."""

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.models.schemas import (
    EditInstruction,
    EditRequest,
    EditResponse,
    PreviewFrameRequest,
    PreviewFrameResponse,
    SceneAudioLevel,
    SceneMetadata,
    SceneTrim,
    TextOverlayInstruction,
)


# --- Schema validation tests ---


class TestTextOverlayInstruction:
    def test_valid_overlay(self):
        overlay = TextOverlayInstruction(
            text="Hello World",
            x=50.0,
            y=25.0,
            font_size=24,
            color="#FFFFFF",
            scene_number=1,
        )
        assert overlay.text == "Hello World"
        assert overlay.x == 50.0
        assert overlay.y == 25.0
        assert overlay.font_size == 24
        assert overlay.color == "#FFFFFF"
        assert overlay.scene_number == 1

    def test_x_out_of_range(self):
        with pytest.raises(ValidationError):
            TextOverlayInstruction(
                text="Test", x=101.0, y=50.0, font_size=24, color="#FFF", scene_number=1
            )

    def test_y_out_of_range(self):
        with pytest.raises(ValidationError):
            TextOverlayInstruction(
                text="Test", x=50.0, y=-1.0, font_size=24, color="#FFF", scene_number=1
            )

    def test_font_size_too_small(self):
        with pytest.raises(ValidationError):
            TextOverlayInstruction(
                text="Test", x=50.0, y=50.0, font_size=5, color="#FFF", scene_number=1
            )

    def test_font_size_too_large(self):
        with pytest.raises(ValidationError):
            TextOverlayInstruction(
                text="Test", x=50.0, y=50.0, font_size=250, color="#FFF", scene_number=1
            )


class TestSceneTrim:
    def test_valid_trim(self):
        trim = SceneTrim(scene_number=1, start_time=0.5, end_time=5.0)
        assert trim.scene_number == 1
        assert trim.start_time == 0.5
        assert trim.end_time == 5.0

    def test_start_time_negative(self):
        with pytest.raises(ValidationError):
            SceneTrim(scene_number=1, start_time=-1.0, end_time=5.0)

    def test_end_time_negative(self):
        with pytest.raises(ValidationError):
            SceneTrim(scene_number=1, start_time=0.0, end_time=-1.0)

    def test_zero_times_valid(self):
        trim = SceneTrim(scene_number=1, start_time=0.0, end_time=0.0)
        assert trim.start_time == 0.0
        assert trim.end_time == 0.0


class TestSceneAudioLevel:
    def test_valid_audio_level(self):
        level = SceneAudioLevel(scene_number=2, volume=1.5)
        assert level.scene_number == 2
        assert level.volume == 1.5

    def test_volume_too_low(self):
        with pytest.raises(ValidationError):
            SceneAudioLevel(scene_number=1, volume=-0.1)

    def test_volume_too_high(self):
        with pytest.raises(ValidationError):
            SceneAudioLevel(scene_number=1, volume=2.5)

    def test_volume_at_boundaries(self):
        level_min = SceneAudioLevel(scene_number=1, volume=0.0)
        assert level_min.volume == 0.0
        level_max = SceneAudioLevel(scene_number=1, volume=2.0)
        assert level_max.volume == 2.0


class TestEditInstruction:
    def test_valid_full_instruction(self):
        instr = EditInstruction(
            scene_order=[3, 1, 2],
            trims=[SceneTrim(scene_number=1, start_time=0.5, end_time=4.0)],
            text_overlays=[
                TextOverlayInstruction(
                    text="Title", x=10.0, y=10.0, font_size=32, color="#FF0000", scene_number=1
                )
            ],
            audio_levels=[SceneAudioLevel(scene_number=2, volume=0.8)],
            background_music_volume=0.2,
        )
        assert instr.scene_order == [3, 1, 2]
        assert len(instr.trims) == 1
        assert len(instr.text_overlays) == 1
        assert len(instr.audio_levels) == 1
        assert instr.background_music_volume == 0.2

    def test_defaults(self):
        instr = EditInstruction()
        assert instr.scene_order == []
        assert instr.trims == []
        assert instr.text_overlays == []
        assert instr.audio_levels == []
        assert instr.background_music_volume == 0.15

    def test_background_music_volume_range(self):
        with pytest.raises(ValidationError):
            EditInstruction(background_music_volume=1.5)
        with pytest.raises(ValidationError):
            EditInstruction(background_music_volume=-0.1)


class TestEditRequest:
    def test_valid_request(self):
        req = EditRequest(instructions=EditInstruction(scene_order=[1, 2]))
        assert req.instructions.scene_order == [1, 2]


class TestEditResponse:
    def test_valid_response(self):
        resp = EditResponse(
            video_id="abc123def456",
            video_path="/output/videos/abc123def456.mp4",
            duration_seconds=30.5,
        )
        assert resp.video_id == "abc123def456"
        assert resp.duration_seconds == 30.5


class TestSceneMetadata:
    def test_valid_metadata(self):
        meta = SceneMetadata(
            scene_number=1,
            thumbnail_url="/static/videos/abc_thumb_1.jpg",
            duration_seconds=5.0,
            narration="Welcome to our video",
            visual_description="A beautiful sunrise",
            media_url="https://example.com/media.mp4",
        )
        assert meta.scene_number == 1
        assert meta.media_url == "https://example.com/media.mp4"

    def test_media_url_optional(self):
        meta = SceneMetadata(
            scene_number=1,
            thumbnail_url="/static/videos/abc_thumb_1.jpg",
            duration_seconds=5.0,
            narration="Hello",
            visual_description="Test",
        )
        assert meta.media_url is None


class TestPreviewFrameRequest:
    def test_valid_request(self):
        req = PreviewFrameRequest(timestamp=2.5)
        assert req.timestamp == 2.5

    def test_negative_timestamp(self):
        with pytest.raises(ValidationError):
            PreviewFrameRequest(timestamp=-1.0)

    def test_zero_timestamp_valid(self):
        req = PreviewFrameRequest(timestamp=0.0)
        assert req.timestamp == 0.0


class TestPreviewFrameResponse:
    def test_valid_response(self):
        resp = PreviewFrameResponse(
            frame_data="base64encodeddata",
            timestamp=1.0,
            width=1920,
            height=1080,
        )
        assert resp.frame_data == "base64encodeddata"
        assert resp.width == 1920


# --- Endpoint routing tests ---


class TestEditorEndpoints:
    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_get_scenes_not_found(self, client):
        """GET /scenes returns 404 for nonexistent video."""
        response = client.get("/api/videos/aabbccddeeff/scenes")
        assert response.status_code == 404

    def test_get_scenes_invalid_video_id(self, client):
        """GET /scenes returns 422 for invalid video_id format."""
        response = client.get("/api/videos/invalid/scenes")
        assert response.status_code == 422

    @patch("app.routers.editor.get_video_metadata")
    def test_get_scenes_success(self, mock_get_meta, client):
        """GET /scenes returns scene list for valid video."""
        mock_get_meta.return_value = {
            "video_id": "aabbccddeeff",
            "scenes": [
                {
                    "scene_number": 1,
                    "duration_seconds": 5.0,
                    "narration": "Welcome!",
                    "visual_description": "Intro screen",
                    "media_url": "https://example.com/vid.mp4",
                },
                {
                    "scene_number": 2,
                    "duration_seconds": 8.0,
                    "narration": "Main content",
                    "visual_description": "Code editor",
                    "media_url": None,
                },
            ],
        }

        response = client.get("/api/videos/aabbccddeeff/scenes")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["scene_number"] == 1
        assert data[0]["thumbnail_url"] == "https://example.com/vid.mp4"
        assert data[1]["thumbnail_url"] == "/static/videos/aabbccddeeff_thumb_2.jpg"

    def test_post_edit_not_found(self, client):
        """POST /edit returns 404 for nonexistent video."""
        payload = {
            "instructions": {
                "scene_order": [1, 2],
                "trims": [],
                "text_overlays": [],
                "audio_levels": [],
                "background_music_volume": 0.15,
            }
        }
        response = client.post("/api/videos/aabbccddeeff/edit", json=payload)
        assert response.status_code == 404

    def test_post_edit_invalid_payload(self, client):
        """POST /edit returns 422 for invalid payload."""
        payload = {
            "instructions": {
                "background_music_volume": 5.0,  # out of range
            }
        }
        response = client.post("/api/videos/aabbccddeeff/edit", json=payload)
        assert response.status_code == 422

    def test_post_edit_invalid_video_id(self, client):
        """POST /edit returns 422 for invalid video_id format."""
        payload = {"instructions": {"scene_order": [1]}}
        response = client.post("/api/videos/not-hex!/edit", json=payload)
        assert response.status_code == 422

    @patch("app.routers.editor.apply_edits")
    def test_post_edit_success(self, mock_apply, client, tmp_path):
        """POST /edit returns EditResponse on success."""
        mock_apply.return_value = {
            "video_id": "newvideo12345",
            "video_path": "/output/videos/newvideo12345.mp4",
            "duration_seconds": 25.0,
        }

        # Create a fake video file so the endpoint finds it
        from app.config import settings
        video_dir = Path(settings.output_dir) / "videos"
        video_dir.mkdir(parents=True, exist_ok=True)
        video_file = video_dir / "aabbccddeeff.mp4"
        video_file.write_bytes(b"fake video content")

        try:
            payload = {
                "instructions": {
                    "scene_order": [2, 1],
                    "trims": [{"scene_number": 1, "start_time": 0.5, "end_time": 4.0}],
                    "text_overlays": [],
                    "audio_levels": [{"scene_number": 2, "volume": 1.2}],
                    "background_music_volume": 0.1,
                }
            }
            response = client.post("/api/videos/aabbccddeeff/edit", json=payload)
            assert response.status_code == 200
            data = response.json()
            assert data["video_id"] == "newvideo12345"
            assert data["duration_seconds"] == 25.0
        finally:
            if video_file.exists():
                video_file.unlink()

    def test_post_preview_frame_not_found(self, client):
        """POST /preview-frame returns 404 for nonexistent video."""
        payload = {"timestamp": 1.0}
        response = client.post("/api/videos/aabbccddeeff/preview-frame", json=payload)
        assert response.status_code == 404

    def test_post_preview_frame_invalid_payload(self, client):
        """POST /preview-frame returns 422 for invalid payload."""
        payload = {"timestamp": -5.0}
        response = client.post("/api/videos/aabbccddeeff/preview-frame", json=payload)
        assert response.status_code == 422

    def test_post_preview_frame_invalid_video_id(self, client):
        """POST /preview-frame returns 422 for invalid video_id format."""
        payload = {"timestamp": 1.0}
        response = client.post("/api/videos/xyz/preview-frame", json=payload)
        assert response.status_code == 422

    @patch("app.routers.editor.extract_frame")
    def test_post_preview_frame_success(self, mock_extract, client):
        """POST /preview-frame returns frame data on success."""
        mock_extract.return_value = ("base64jpegdata", 1920, 1080)

        # Create a fake video file
        from app.config import settings
        video_dir = Path(settings.output_dir) / "videos"
        video_dir.mkdir(parents=True, exist_ok=True)
        video_file = video_dir / "aabbccddeeff.mp4"
        video_file.write_bytes(b"fake video content")

        try:
            payload = {"timestamp": 2.5}
            response = client.post("/api/videos/aabbccddeeff/preview-frame", json=payload)
            assert response.status_code == 200
            data = response.json()
            assert data["frame_data"] == "base64jpegdata"
            assert data["timestamp"] == 2.5
            assert data["width"] == 1920
            assert data["height"] == 1080
        finally:
            if video_file.exists():
                video_file.unlink()
