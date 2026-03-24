from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Multilingual Dispute Interface"
    api_prefix: str = "/api/v1"
    storage_path: Path = Path("data") / "multilingual_pipeline.db"
    temp_upload_dir: Path = Path("data") / "uploads"

    negotiation_api_url: str = "http://localhost:9000/negotiation-engine"
    negotiation_timeout_seconds: float = 30.0

    translator_provider: str = "openai"
    openai_api_key: str | None = None
    openai_translation_model: str = "gpt-4.1-mini"

    elevenlabs_api_key: str | None = None
    elevenlabs_voice_id: str | None = None
    elevenlabs_model_id: str = "eleven_multilingual_v2"

    whisper_model_size: str = "base"
    whisper_device: str = "cpu"
    tesseract_cmd: str | None = None

    enable_side_by_side_text: bool = True
    default_output_language: str = "en"
    supported_languages: list[str] = Field(
        default_factory=lambda: [
            "ar",
            "bn",
            "de",
            "en",
            "es",
            "fr",
            "gu",
            "hi",
            "ja",
            "kn",
            "ko",
            "ml",
            "mr",
            "pt",
            "ru",
            "ta",
            "te",
            "tr",
            "ur",
            "zh-cn",
            "zh-tw",
        ]
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.temp_upload_dir.mkdir(parents=True, exist_ok=True)
    settings.storage_path.parent.mkdir(parents=True, exist_ok=True)
    return settings
