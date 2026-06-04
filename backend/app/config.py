"""Application configuration using pydantic-settings."""

import secrets
from pathlib import Path

from pydantic_settings import BaseSettings

DEFAULT_SECRET = "change-me-to-a-secure-random-string-at-least-32-chars"
SECRET_FILE = Path(__file__).parent / ".jwt_secret"


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

    # Media caching
    media_cache_enabled: bool = True

    # Output configuration
    output_dir: str = "./output"

    # TTS configuration
    tts_voice: str = "en-US-AriaNeural"

    # JWT configuration
    jwt_secret: str = DEFAULT_SECRET
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 10080  # 7 days

    # Server configuration
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: str = "*"

    # Sentry / error tracking
    sentry_dsn: str = ""

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.jwt_secret == DEFAULT_SECRET:
            if SECRET_FILE.exists():
                stored = SECRET_FILE.read_text().strip()
                if stored and stored != DEFAULT_SECRET:
                    self.jwt_secret = stored
                    return
            new_secret = secrets.token_hex(32)
            SECRET_FILE.write_text(new_secret)
            SECRET_FILE.chmod(0o600)
            self.jwt_secret = new_secret

    def get_output_path(self) -> Path:
        """Get the output directory path, creating it if needed."""
        path = Path(self.output_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path


settings = Settings()
