"""Pydantic models for request/response schemas."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class LibraryCategory(str, Enum):
    """Local media library categories."""

    music = "music"
    image = "image"
    video = "video"


class BrandingPosition(str, Enum):
    """Branding overlay position options."""

    top_left = "top-left"
    top_right = "top-right"
    bottom_left = "bottom-left"
    bottom_right = "bottom-right"
    top_center = "top-center"
    bottom_center = "bottom-center"


class VideoStyle(str, Enum):
    """Video style options."""

    educational = "educational"
    entertaining = "entertaining"
    documentary = "documentary"
    motivational = "motivational"
    news = "news"


class VideoFormat(str, Enum):
    """Video format/orientation options."""

    shorts = "shorts"  # 1080x1920 vertical
    landscape = "landscape"  # 1920x1080 horizontal


class Resolution(str, Enum):
    """Video resolution presets."""

    res_480p = "480p"
    res_720p = "720p"
    res_1080p = "1080p"
    res_4k = "4k"


class BitratePreset(str, Enum):
    """Video bitrate presets."""

    low = "low"
    medium = "medium"
    high = "high"
    custom = "custom"


class FPSOption(str, Enum):
    """Frames per second options."""

    fps_24 = "24"
    fps_30 = "30"
    fps_60 = "60"


class CodecPreset(str, Enum):
    """FFmpeg codec speed presets."""

    ultrafast = "ultrafast"
    superfast = "superfast"
    veryfast = "veryfast"
    faster = "faster"
    fast = "fast"
    medium = "medium"
    slow = "slow"
    slower = "slower"
    veryslow = "veryslow"


class OutputFormat(str, Enum):
    """Video output file format."""

    mp4 = "mp4"
    webm = "webm"
    avi = "avi"


class VideoQualitySettings(BaseModel):
    """Video quality configuration settings."""

    resolution: Resolution = Field(
        default=Resolution.res_1080p, description="Video resolution"
    )
    bitrate: BitratePreset = Field(
        default=BitratePreset.medium, description="Bitrate preset"
    )
    custom_bitrate: Optional[str] = Field(
        None,
        pattern=r"^\d+[kKmMgG]?$",
        description="Custom bitrate value (e.g. '6M'), used when bitrate is 'custom'",
    )
    fps: FPSOption = Field(default=FPSOption.fps_24, description="Frames per second")
    codec_preset: CodecPreset = Field(
        default=CodecPreset.medium, description="FFmpeg codec speed preset"
    )
    output_format: OutputFormat = Field(
        default=OutputFormat.mp4, description="Output file format"
    )


class AudioSettings(BaseModel):
    """Audio processing configuration settings."""

    crossfade_duration: float = Field(
        default=0.5, ge=0.0, le=2.0, description="Crossfade duration between scenes in seconds"
    )
    normalize_audio: bool = Field(
        default=True, description="Normalize audio volume across all scenes"
    )
    background_music_url: Optional[str] = Field(
        default=None, description="URL of background music file to mix in"
    )
    background_music_volume: float = Field(
        default=0.15, ge=0.0, le=1.0, description="Background music volume (0.0 to 1.0)"
    )
    enable_ducking: bool = Field(
        default=True, description="Auto-duck background music during narration"
    )
    generate_subtitles: bool = Field(
        default=False, description="Generate SRT subtitle file alongside the video"
    )


class LibraryItem(BaseModel):
    """A media item in the local library."""

    id: str = Field(..., description="Unique item identifier")
    filename: str = Field(..., description="Stored filename")
    original_filename: str = Field(..., description="Original upload filename")
    category: LibraryCategory = Field(..., description="Item category")
    labels: list[str] = Field(default_factory=list, description="Searchable labels")
    description: str = Field(default="", description="Item description")
    file_path: str = Field(..., description="Path to stored file")
    created_at: str = Field(..., description="ISO timestamp of creation")
    file_size: int = Field(default=0, description="File size in bytes")


class BrandingConfig(BaseModel):
    """Branding overlay configuration."""

    id: str = Field(..., description="Branding config identifier")
    image_path: str = Field(..., description="Path to branding image")
    position: BrandingPosition = Field(
        default=BrandingPosition.bottom_right, description="Position on video"
    )
    size_percent: float = Field(
        default=15.0, ge=10.0, le=50.0, description="Size as percentage of video width"
    )
    opacity: float = Field(
        default=0.8, ge=0.1, le=1.0, description="Branding opacity"
    )
    enabled: bool = Field(default=True, description="Whether branding is enabled")


class VideoRequest(BaseModel):
    """Request model for video generation."""

    topic: str = Field(..., min_length=3, max_length=500, description="Video topic")
    duration_minutes: float = Field(
        default=1.0, ge=0.5, le=10.0, description="Desired video duration in minutes"
    )
    style: VideoStyle = Field(
        default=VideoStyle.educational, description="Video style"
    )
    format: VideoFormat = Field(
        default=VideoFormat.landscape, description="Video format/orientation"
    )


class ScriptScene(BaseModel):
    """A single scene in the video script."""

    scene_number: int = Field(..., description="Scene sequence number")
    narration: str = Field(..., description="Narration text for this scene")
    visual_description: str = Field(
        ..., description="Description of visuals for this scene"
    )
    duration_seconds: float = Field(
        ..., ge=2.0, le=60.0, description="Scene duration in seconds"
    )


class VideoScript(BaseModel):
    """Complete video script generated by AI."""

    title: str = Field(..., description="Video title")
    scenes: list[ScriptScene] = Field(..., min_length=1, description="List of scenes")
    total_duration: float = Field(..., description="Total duration in seconds")


class MediaType(str, Enum):
    """Types of media that can be sourced."""

    video = "video"
    image = "image"
    gif = "gif"
    sound = "sound"


class MediaItem(BaseModel):
    """A media item sourced for a scene."""

    url: str = Field(..., description="URL of the media")
    local_path: Optional[str] = Field(None, description="Local file path after download")
    media_type: MediaType = Field(..., description="Type of media")
    source: str = Field(..., description="Source API (pexels, pixabay, giphy)")
    query: str = Field(..., description="Search query used")
    width: Optional[int] = None
    height: Optional[int] = None


class SceneMedia(BaseModel):
    """Media items for a specific scene."""

    scene_number: int
    media_items: list[MediaItem] = Field(default_factory=list)


class TTSResult(BaseModel):
    """Result of TTS generation for a scene."""

    scene_number: int = Field(..., description="Scene number")
    audio_path: str = Field(..., description="Path to generated audio file")
    duration_seconds: float = Field(..., description="Audio duration in seconds")


class VideoResult(BaseModel):
    """Result of video assembly."""

    video_id: str = Field(..., description="Unique video identifier")
    video_path: str = Field(..., description="Path to the assembled video")
    duration_seconds: float = Field(..., description="Total video duration")
    scenes_count: int = Field(..., description="Number of scenes")
    format: VideoFormat = Field(..., description="Video format")
    subtitle_path: Optional[str] = Field(
        default=None, description="Path to generated SRT subtitle file"
    )


class GenerateScriptRequest(BaseModel):
    """Request to generate a video script."""

    topic: str = Field(..., min_length=3, max_length=500)
    duration_minutes: float = Field(default=1.0, ge=0.5, le=10.0)
    style: VideoStyle = Field(default=VideoStyle.educational)


class GenerateTTSRequest(BaseModel):
    """Request to generate TTS audio from a script."""

    script: VideoScript
    voice: Optional[str] = None


class SourceMediaRequest(BaseModel):
    """Request to source media for a script."""

    script: VideoScript
    preferred_type: Optional[MediaType] = None
    ai_generation_settings: Optional["AIGenerationSettings"] = Field(
        default=None, description="Optional AI generation settings"
    )


class SearchMediaRequest(BaseModel):
    """Request to search media across all sources."""

    query: str = Field(..., min_length=1, max_length=200, description="Search query")


class AssembleVideoRequest(BaseModel):
    """Request to assemble the final video."""

    script: VideoScript
    tts_results: list[TTSResult]
    scene_media: list[SceneMedia]
    format: VideoFormat = Field(default=VideoFormat.landscape)
    quality_settings: Optional[VideoQualitySettings] = Field(
        default=None, description="Optional video quality settings"
    )
    audio_settings: Optional[AudioSettings] = Field(
        default=None, description="Optional audio processing settings"
    )
    branding_config: Optional[BrandingConfig] = Field(
        default=None, description="Optional branding overlay config"
    )


class GenerateFullRequest(BaseModel):
    """Request for the full pipeline generation via SSE."""

    topic: str = Field(..., min_length=3, max_length=500)
    duration_minutes: float = Field(default=1.0, ge=0.5, le=10.0)
    style: VideoStyle = Field(default=VideoStyle.educational)
    quality_settings: Optional[VideoQualitySettings] = Field(
        default=None, description="Optional video quality settings"
    )
    audio_settings: Optional[AudioSettings] = Field(
        default=None, description="Optional audio processing settings"
    )
    ai_generation_settings: Optional["AIGenerationSettings"] = Field(
        default=None, description="Optional AI generation settings"
    )
    branding_config: Optional[BrandingConfig] = Field(
        default=None, description="Optional branding overlay config"
    )


# --- AI Generation schemas ---


class AIImageSize(str, Enum):
    """AI image size options."""

    size_1024x1024 = "1024x1024"
    size_1792x1024 = "1792x1024"
    size_1024x1792 = "1024x1792"


class AIImageQuality(str, Enum):
    """AI image quality options."""

    standard = "standard"
    hd = "hd"


class AIGenerationSettings(BaseModel):
    """AI generation configuration settings."""

    ai_image_enabled: bool = Field(default=True, description="Enable AI image generation fallback")
    ai_video_enabled: bool = Field(default=False, description="Enable AI video generation fallback")
    ai_image_max_per_video: int = Field(
        default=5, ge=0, le=20, description="Max AI-generated images per video"
    )
    ai_video_max_per_video: int = Field(
        default=3, ge=0, le=10, description="Max AI-generated videos per video"
    )
    ai_image_quality: AIImageQuality = Field(
        default=AIImageQuality.standard, description="AI image quality"
    )
    ai_image_size: AIImageSize = Field(
        default=AIImageSize.size_1792x1024, description="AI image size"
    )


class AIGenerationStats(BaseModel):
    """Statistics about AI generation usage in a video."""

    ai_images_generated: int = Field(default=0, description="Number of AI images generated")
    ai_videos_generated: int = Field(default=0, description="Number of AI videos generated")
    ai_image_limit: int = Field(default=5, description="AI image generation limit")
    ai_video_limit: int = Field(default=3, description="AI video generation limit")


# --- Editor schemas ---


class TextOverlayInstruction(BaseModel):
    """A text overlay to be applied to a specific scene."""

    text: str = Field(..., description="Text content to overlay")
    x: float = Field(..., ge=0, le=100, description="X position (0-100 percent)")
    y: float = Field(..., ge=0, le=100, description="Y position (0-100 percent)")
    font_size: int = Field(..., ge=8, le=200, description="Font size in pixels")
    color: str = Field(..., description="Text color (e.g. '#FFFFFF')")
    scene_number: int = Field(..., description="Scene number to apply overlay to")


class SceneTrim(BaseModel):
    """Trim boundaries for a scene."""

    scene_number: int = Field(..., description="Scene number to trim")
    start_time: float = Field(..., ge=0, description="Start time in seconds")
    end_time: float = Field(..., ge=0, description="End time in seconds")

    @model_validator(mode="after")
    def end_time_gte_start_time(self) -> "SceneTrim":
        if self.end_time < self.start_time:
            raise ValueError("end_time must be greater than or equal to start_time")
        return self


class SceneAudioLevel(BaseModel):
    """Audio volume adjustment for a scene."""

    scene_number: int = Field(..., description="Scene number to adjust")
    volume: float = Field(..., ge=0.0, le=2.0, description="Volume multiplier (0.0 to 2.0)")


class MediaReplacement(BaseModel):
    """A media replacement for a specific scene."""

    scene_number: int = Field(..., description="Scene number to replace media for")
    media_url: str = Field(..., description="New media URL")
    media_type: str = Field(default="video", description="Type of the new media (video, image, gif)")


class EditInstruction(BaseModel):
    """Full set of edit instructions for a video."""

    scene_order: list[int] = Field(default_factory=list, description="Reordered scene numbers")
    trims: list[SceneTrim] = Field(default_factory=list, description="Per-scene trim instructions")
    text_overlays: list[TextOverlayInstruction] = Field(
        default_factory=list, description="Text overlays to apply"
    )
    audio_levels: list[SceneAudioLevel] = Field(
        default_factory=list, description="Per-scene audio level adjustments"
    )
    background_music_volume: float = Field(
        default=0.15, ge=0.0, le=1.0, description="Background music volume (0.0 to 1.0)"
    )
    media_replacements: list[MediaReplacement] = Field(
        default_factory=list, description="Per-scene media replacements"
    )


class EditRequest(BaseModel):
    """Request to apply edits to a video."""

    instructions: EditInstruction


class EditResponse(BaseModel):
    """Response after applying edits to a video."""

    video_id: str = Field(..., description="New video identifier")
    video_path: str = Field(..., description="Path to the edited video")
    duration_seconds: float = Field(..., description="Duration of edited video")


class SceneMetadata(BaseModel):
    """Metadata for a single scene in a video."""

    scene_number: int = Field(..., description="Scene number")
    thumbnail_url: str = Field(..., description="URL to scene thumbnail")
    duration_seconds: float = Field(..., description="Scene duration in seconds")
    narration: str = Field(..., description="Scene narration text")
    visual_description: str = Field(..., description="Visual description")
    media_url: Optional[str] = Field(None, description="Original media URL")


class PreviewFrameRequest(BaseModel):
    """Request to extract a preview frame at a given timestamp."""

    timestamp: float = Field(..., ge=0, description="Timestamp in seconds")


class PreviewFrameResponse(BaseModel):
    """Response with an extracted preview frame."""

    frame_data: str = Field(..., description="Base64-encoded JPEG frame data")
    timestamp: float = Field(..., description="Actual timestamp extracted")
    width: int = Field(..., description="Frame width in pixels")
    height: int = Field(..., description="Frame height in pixels")
