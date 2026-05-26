"""Tests for Pydantic model validation."""

import pytest
from pydantic import ValidationError

from app.models.schemas import (
    AssembleVideoRequest,
    AudioSettings,
    BitratePreset,
    CodecPreset,
    FPSOption,
    GenerateFullRequest,
    GenerateScriptRequest,
    GenerateTTSRequest,
    MediaItem,
    MediaType,
    OutputFormat,
    Resolution,
    SceneMedia,
    ScriptScene,
    SourceMediaRequest,
    TTSResult,
    VideoFormat,
    VideoQualitySettings,
    VideoRequest,
    VideoResult,
    VideoScript,
    VideoStyle,
)


class TestVideoRequest:
    def test_valid_request(self):
        req = VideoRequest(topic="Python programming", duration_minutes=2.0)
        assert req.topic == "Python programming"
        assert req.duration_minutes == 2.0
        assert req.style == VideoStyle.educational
        assert req.format == VideoFormat.landscape

    def test_minimum_topic_length(self):
        with pytest.raises(ValidationError):
            VideoRequest(topic="ab")

    def test_duration_range(self):
        with pytest.raises(ValidationError):
            VideoRequest(topic="Valid topic", duration_minutes=0.1)
        with pytest.raises(ValidationError):
            VideoRequest(topic="Valid topic", duration_minutes=15.0)

    def test_all_styles(self):
        for style in VideoStyle:
            req = VideoRequest(topic="Test topic", style=style)
            assert req.style == style

    def test_all_formats(self):
        for fmt in VideoFormat:
            req = VideoRequest(topic="Test topic", format=fmt)
            assert req.format == fmt


class TestScriptScene:
    def test_valid_scene(self):
        scene = ScriptScene(
            scene_number=1,
            narration="Welcome to this video about Python.",
            visual_description="A laptop screen showing Python code",
            duration_seconds=10.0,
        )
        assert scene.scene_number == 1
        assert scene.duration_seconds == 10.0

    def test_duration_minimum(self):
        with pytest.raises(ValidationError):
            ScriptScene(
                scene_number=1,
                narration="Short",
                visual_description="Test",
                duration_seconds=1.0,
            )

    def test_duration_maximum(self):
        with pytest.raises(ValidationError):
            ScriptScene(
                scene_number=1,
                narration="Long scene",
                visual_description="Test",
                duration_seconds=90.0,
            )


class TestVideoScript:
    def test_valid_script(self):
        script = VideoScript(
            title="Python Tutorial",
            scenes=[
                ScriptScene(
                    scene_number=1,
                    narration="Welcome!",
                    visual_description="Intro screen",
                    duration_seconds=5.0,
                ),
                ScriptScene(
                    scene_number=2,
                    narration="Let's learn Python.",
                    visual_description="Code editor",
                    duration_seconds=15.0,
                ),
            ],
            total_duration=20.0,
        )
        assert script.title == "Python Tutorial"
        assert len(script.scenes) == 2
        assert script.total_duration == 20.0

    def test_empty_scenes_fails(self):
        with pytest.raises(ValidationError):
            VideoScript(title="Test", scenes=[], total_duration=0)


class TestMediaItem:
    def test_valid_media_item(self):
        item = MediaItem(
            url="https://example.com/video.mp4",
            media_type=MediaType.video,
            source="pexels",
            query="nature",
        )
        assert item.url == "https://example.com/video.mp4"
        assert item.media_type == MediaType.video
        assert item.local_path is None

    def test_with_local_path(self):
        item = MediaItem(
            url="https://example.com/img.jpg",
            media_type=MediaType.image,
            source="pixabay",
            query="city skyline",
            local_path="/tmp/img123.jpg",
        )
        assert item.local_path == "/tmp/img123.jpg"


class TestTTSResult:
    def test_valid_result(self):
        result = TTSResult(
            scene_number=1,
            audio_path="/output/audio/scene_001.mp3",
            duration_seconds=8.5,
        )
        assert result.scene_number == 1
        assert result.duration_seconds == 8.5


class TestVideoResult:
    def test_valid_result(self):
        result = VideoResult(
            video_id="abc123",
            video_path="/output/videos/abc123.mp4",
            duration_seconds=60.0,
            scenes_count=5,
            format=VideoFormat.landscape,
        )
        assert result.video_id == "abc123"
        assert result.scenes_count == 5


class TestGenerateScriptRequest:
    def test_valid_request(self):
        req = GenerateScriptRequest(topic="AI in healthcare")
        assert req.topic == "AI in healthcare"
        assert req.duration_minutes == 1.0
        assert req.style == VideoStyle.educational

    def test_custom_values(self):
        req = GenerateScriptRequest(
            topic="Space exploration",
            duration_minutes=5.0,
            style=VideoStyle.documentary,
        )
        assert req.duration_minutes == 5.0
        assert req.style == VideoStyle.documentary


class TestGenerateTTSRequest:
    def test_valid_request(self):
        script = VideoScript(
            title="Test",
            scenes=[
                ScriptScene(
                    scene_number=1,
                    narration="Hello",
                    visual_description="Test visual",
                    duration_seconds=5.0,
                )
            ],
            total_duration=5.0,
        )
        req = GenerateTTSRequest(script=script)
        assert req.voice is None


class TestSourceMediaRequest:
    def test_valid_request(self):
        script = VideoScript(
            title="Test",
            scenes=[
                ScriptScene(
                    scene_number=1,
                    narration="Hello",
                    visual_description="Mountains at sunset",
                    duration_seconds=5.0,
                )
            ],
            total_duration=5.0,
        )
        req = SourceMediaRequest(script=script, preferred_type=MediaType.video)
        assert req.preferred_type == MediaType.video


class TestAssembleVideoRequest:
    def test_valid_request(self):
        script = VideoScript(
            title="Test",
            scenes=[
                ScriptScene(
                    scene_number=1,
                    narration="Hello",
                    visual_description="Test",
                    duration_seconds=5.0,
                )
            ],
            total_duration=5.0,
        )
        tts = [TTSResult(scene_number=1, audio_path="/tmp/audio.mp3", duration_seconds=5.0)]
        media = [
            SceneMedia(
                scene_number=1,
                media_items=[
                    MediaItem(
                        url="https://example.com/vid.mp4",
                        media_type=MediaType.video,
                        source="pexels",
                        query="test",
                        local_path="/tmp/vid.mp4",
                    )
                ],
            )
        ]
        req = AssembleVideoRequest(
            script=script,
            tts_results=tts,
            scene_media=media,
            format=VideoFormat.shorts,
        )
        assert req.format == VideoFormat.shorts
        assert len(req.tts_results) == 1

    def test_with_quality_settings(self):
        script = VideoScript(
            title="Test",
            scenes=[
                ScriptScene(
                    scene_number=1,
                    narration="Hello",
                    visual_description="Test",
                    duration_seconds=5.0,
                )
            ],
            total_duration=5.0,
        )
        tts = [TTSResult(scene_number=1, audio_path="/tmp/audio.mp3", duration_seconds=5.0)]
        media = [SceneMedia(scene_number=1, media_items=[])]
        quality = VideoQualitySettings(
            resolution=Resolution.res_720p,
            bitrate=BitratePreset.high,
            fps=FPSOption.fps_30,
            codec_preset=CodecPreset.fast,
            output_format=OutputFormat.webm,
        )
        req = AssembleVideoRequest(
            script=script,
            tts_results=tts,
            scene_media=media,
            format=VideoFormat.landscape,
            quality_settings=quality,
        )
        assert req.quality_settings is not None
        assert req.quality_settings.resolution == Resolution.res_720p
        assert req.quality_settings.output_format == OutputFormat.webm

    def test_quality_settings_defaults_to_none(self):
        script = VideoScript(
            title="Test",
            scenes=[
                ScriptScene(
                    scene_number=1,
                    narration="Hello",
                    visual_description="Test",
                    duration_seconds=5.0,
                )
            ],
            total_duration=5.0,
        )
        tts = [TTSResult(scene_number=1, audio_path="/tmp/audio.mp3", duration_seconds=5.0)]
        media = [SceneMedia(scene_number=1, media_items=[])]
        req = AssembleVideoRequest(
            script=script,
            tts_results=tts,
            scene_media=media,
        )
        assert req.quality_settings is None


class TestVideoQualitySettings:
    def test_defaults(self):
        settings = VideoQualitySettings()
        assert settings.resolution == Resolution.res_1080p
        assert settings.bitrate == BitratePreset.medium
        assert settings.custom_bitrate is None
        assert settings.fps == FPSOption.fps_24
        assert settings.codec_preset == CodecPreset.medium
        assert settings.output_format == OutputFormat.mp4

    def test_all_resolutions(self):
        for res in Resolution:
            settings = VideoQualitySettings(resolution=res)
            assert settings.resolution == res

    def test_all_bitrate_presets(self):
        for bp in BitratePreset:
            settings = VideoQualitySettings(bitrate=bp)
            assert settings.bitrate == bp

    def test_all_fps_options(self):
        for fps in FPSOption:
            settings = VideoQualitySettings(fps=fps)
            assert settings.fps == fps

    def test_all_codec_presets(self):
        for cp in CodecPreset:
            settings = VideoQualitySettings(codec_preset=cp)
            assert settings.codec_preset == cp

    def test_all_output_formats(self):
        for fmt in OutputFormat:
            settings = VideoQualitySettings(output_format=fmt)
            assert settings.output_format == fmt

    def test_custom_bitrate_field(self):
        settings = VideoQualitySettings(
            bitrate=BitratePreset.custom,
            custom_bitrate="6M",
        )
        assert settings.bitrate == BitratePreset.custom
        assert settings.custom_bitrate == "6M"

    def test_custom_bitrate_without_custom_preset(self):
        settings = VideoQualitySettings(
            bitrate=BitratePreset.high,
            custom_bitrate="10M",
        )
        assert settings.bitrate == BitratePreset.high
        assert settings.custom_bitrate == "10M"

    def test_invalid_resolution_value(self):
        with pytest.raises(ValidationError):
            VideoQualitySettings(resolution="invalid")

    def test_invalid_custom_bitrate_format(self):
        """Test that invalid custom_bitrate values are rejected by regex."""
        with pytest.raises(ValidationError):
            VideoQualitySettings(bitrate=BitratePreset.custom, custom_bitrate="abc")
        with pytest.raises(ValidationError):
            VideoQualitySettings(bitrate=BitratePreset.custom, custom_bitrate="-1M")
        with pytest.raises(ValidationError):
            VideoQualitySettings(bitrate=BitratePreset.custom, custom_bitrate="6 M")

    def test_valid_custom_bitrate_formats(self):
        """Test that various valid bitrate formats are accepted."""
        for value in ("6M", "500k", "10G", "4000", "8m"):
            settings = VideoQualitySettings(
                bitrate=BitratePreset.custom, custom_bitrate=value
            )
            assert settings.custom_bitrate == value

    def test_invalid_fps_value(self):
        with pytest.raises(ValidationError):
            VideoQualitySettings(fps="120")

    def test_invalid_output_format(self):
        with pytest.raises(ValidationError):
            VideoQualitySettings(output_format="mkv")


class TestGenerateFullRequest:
    def test_valid_request(self):
        req = GenerateFullRequest(topic="AI in healthcare")
        assert req.topic == "AI in healthcare"
        assert req.quality_settings is None

    def test_with_quality_settings(self):
        quality = VideoQualitySettings(
            resolution=Resolution.res_4k,
            fps=FPSOption.fps_60,
        )
        req = GenerateFullRequest(
            topic="Space exploration",
            quality_settings=quality,
        )
        assert req.quality_settings is not None
        assert req.quality_settings.resolution == Resolution.res_4k
        assert req.quality_settings.fps == FPSOption.fps_60


class TestAudioSettings:
    def test_defaults(self):
        audio = AudioSettings()
        assert audio.crossfade_duration == 0.5
        assert audio.normalize_audio is True
        assert audio.background_music_url is None
        assert audio.background_music_volume == 0.15
        assert audio.enable_ducking is True
        assert audio.generate_subtitles is False

    def test_custom_crossfade_duration(self):
        audio = AudioSettings(crossfade_duration=1.5)
        assert audio.crossfade_duration == 1.5

    def test_crossfade_duration_min(self):
        audio = AudioSettings(crossfade_duration=0.0)
        assert audio.crossfade_duration == 0.0

    def test_crossfade_duration_max(self):
        audio = AudioSettings(crossfade_duration=2.0)
        assert audio.crossfade_duration == 2.0

    def test_crossfade_duration_below_min(self):
        with pytest.raises(ValidationError):
            AudioSettings(crossfade_duration=-0.1)

    def test_crossfade_duration_above_max(self):
        with pytest.raises(ValidationError):
            AudioSettings(crossfade_duration=2.5)

    def test_background_music_volume_range(self):
        audio = AudioSettings(background_music_volume=0.0)
        assert audio.background_music_volume == 0.0
        audio = AudioSettings(background_music_volume=1.0)
        assert audio.background_music_volume == 1.0

    def test_background_music_volume_below_min(self):
        with pytest.raises(ValidationError):
            AudioSettings(background_music_volume=-0.1)

    def test_background_music_volume_above_max(self):
        with pytest.raises(ValidationError):
            AudioSettings(background_music_volume=1.5)

    def test_with_background_music_url(self):
        audio = AudioSettings(background_music_url="https://example.com/music.mp3")
        assert audio.background_music_url == "https://example.com/music.mp3"

    def test_all_boolean_flags(self):
        audio = AudioSettings(
            normalize_audio=False,
            enable_ducking=False,
            generate_subtitles=True,
        )
        assert audio.normalize_audio is False
        assert audio.enable_ducking is False
        assert audio.generate_subtitles is True

    def test_full_custom_settings(self):
        audio = AudioSettings(
            crossfade_duration=1.0,
            normalize_audio=False,
            background_music_url="https://example.com/track.mp3",
            background_music_volume=0.3,
            enable_ducking=False,
            generate_subtitles=True,
        )
        assert audio.crossfade_duration == 1.0
        assert audio.normalize_audio is False
        assert audio.background_music_url == "https://example.com/track.mp3"
        assert audio.background_music_volume == 0.3
        assert audio.enable_ducking is False
        assert audio.generate_subtitles is True


class TestVideoResultWithSubtitles:
    def test_result_without_subtitles(self):
        result = VideoResult(
            video_id="abc123",
            video_path="/output/videos/abc123.mp4",
            duration_seconds=60.0,
            scenes_count=5,
            format=VideoFormat.landscape,
        )
        assert result.subtitle_path is None

    def test_result_with_subtitles(self):
        result = VideoResult(
            video_id="abc123",
            video_path="/output/videos/abc123.mp4",
            duration_seconds=60.0,
            scenes_count=5,
            format=VideoFormat.landscape,
            subtitle_path="/output/videos/abc123.srt",
        )
        assert result.subtitle_path == "/output/videos/abc123.srt"


class TestAssembleVideoRequestWithAudio:
    def test_with_audio_settings(self):
        script = VideoScript(
            title="Test",
            scenes=[
                ScriptScene(
                    scene_number=1,
                    narration="Hello",
                    visual_description="Test",
                    duration_seconds=5.0,
                )
            ],
            total_duration=5.0,
        )
        tts = [TTSResult(scene_number=1, audio_path="/tmp/audio.mp3", duration_seconds=5.0)]
        media = [SceneMedia(scene_number=1, media_items=[])]
        audio = AudioSettings(
            crossfade_duration=1.0,
            generate_subtitles=True,
        )
        req = AssembleVideoRequest(
            script=script,
            tts_results=tts,
            scene_media=media,
            audio_settings=audio,
        )
        assert req.audio_settings is not None
        assert req.audio_settings.crossfade_duration == 1.0
        assert req.audio_settings.generate_subtitles is True

    def test_audio_settings_defaults_to_none(self):
        script = VideoScript(
            title="Test",
            scenes=[
                ScriptScene(
                    scene_number=1,
                    narration="Hello",
                    visual_description="Test",
                    duration_seconds=5.0,
                )
            ],
            total_duration=5.0,
        )
        tts = [TTSResult(scene_number=1, audio_path="/tmp/audio.mp3", duration_seconds=5.0)]
        media = [SceneMedia(scene_number=1, media_items=[])]
        req = AssembleVideoRequest(
            script=script,
            tts_results=tts,
            scene_media=media,
        )
        assert req.audio_settings is None


class TestGenerateFullRequestWithAudio:
    def test_with_audio_settings(self):
        audio = AudioSettings(
            crossfade_duration=0.8,
            normalize_audio=True,
            generate_subtitles=True,
        )
        req = GenerateFullRequest(
            topic="Space exploration",
            audio_settings=audio,
        )
        assert req.audio_settings is not None
        assert req.audio_settings.crossfade_duration == 0.8

    def test_audio_settings_defaults_to_none(self):
        req = GenerateFullRequest(topic="AI in healthcare")
        assert req.audio_settings is None


class TestMediaTypeSound:
    def test_sound_enum_value(self):
        assert MediaType.sound == "sound"
        assert MediaType.sound.value == "sound"

    def test_media_item_with_sound_type(self):
        item = MediaItem(
            url="https://freesound.org/preview/12345.mp3",
            media_type=MediaType.sound,
            source="freesound",
            query="ocean waves",
        )
        assert item.media_type == MediaType.sound
        assert item.source == "freesound"

    def test_all_media_types(self):
        expected = {"video", "image", "gif", "sound"}
        actual = {mt.value for mt in MediaType}
        assert actual == expected


class TestSearchMediaRequest:
    def test_valid_request(self):
        from app.models.schemas import SearchMediaRequest
        req = SearchMediaRequest(query="sunset ocean")
        assert req.query == "sunset ocean"

    def test_empty_query_fails(self):
        from app.models.schemas import SearchMediaRequest
        with pytest.raises(ValidationError):
            SearchMediaRequest(query="")


class TestSearchMediaEndpoint:
    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from app.main import app
        return TestClient(app)

    def test_search_media_returns_list(self, client, monkeypatch):
        """Test the search-media endpoint returns media items."""
        from app.routers import videos

        async def mock_search_all_sources(query, http_client, per_source=2):
            return [
                MediaItem(
                    url="https://example.com/photo.jpg",
                    media_type=MediaType.image,
                    source="unsplash",
                    query=query,
                    width=1920,
                    height=1080,
                ),
                MediaItem(
                    url="https://example.com/video.mp4",
                    media_type=MediaType.video,
                    source="pexels",
                    query=query,
                    width=1920,
                    height=1080,
                ),
            ]

        monkeypatch.setattr(videos, "search_all_sources", mock_search_all_sources)

        response = client.post("/api/videos/search-media", json={"query": "nature sunset"})
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["source"] == "unsplash"
        assert data[1]["source"] == "pexels"

    def test_search_media_empty_query_fails(self, client):
        """Test that empty query returns validation error."""
        response = client.post("/api/videos/search-media", json={"query": ""})
        assert response.status_code == 422
