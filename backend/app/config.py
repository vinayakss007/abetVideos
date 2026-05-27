"""Application configuration using pydantic-settings."""

from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file."""

    # OpenAI-compatible API settings
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"

    # Media API keys
    pexels_api_key: str = ""
    pixabay_api_key: str = ""
    giphy_api_key: str = ""
    unsplash_access_key: str = ""
    freesound_api_key: str = ""

    # AI generation settings
    ai_image_enabled: bool = True
    ai_video_enabled: bool = False
    ai_image_max_per_video: int = 5
    ai_video_max_per_video: int = 3
    ai_image_quality: str = "standard"
    ai_image_size: str = "1792x1024"
    replicate_api_token: str = ""

    # Media caching
    media_cache_enabled: bool = True

    # Output configuration
    output_dir: str = "./output"

    # TTS configuration
    tts_voice: str = "en-US-AriaNeural"

    # Server configuration
    host: str = "0.0.0.0"
    port: int = 8000

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

    def get_output_path(self) -> Path:
        """Get the output directory path, creating it if needed."""
        path = Path(self.output_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path


settings = Settings()
