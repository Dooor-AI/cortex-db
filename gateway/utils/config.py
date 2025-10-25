from __future__ import annotations

from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration sourced from environment variables."""

    database_url: str = Field(
        default="postgresql://cortex:cortex_pass@postgres:5432/cortex",
        alias="DATABASE_URL",
    )
    qdrant_url: str = Field(default="http://qdrant:6333", alias="QDRANT_URL")

    minio_endpoint: str = Field(default="minio:9000", alias="MINIO_ENDPOINT")
    minio_access_key: str = Field(default="cortex", alias="MINIO_ACCESS_KEY")
    minio_secret_key: str = Field(default="cortex_pass", alias="MINIO_SECRET_KEY")
    minio_secure: bool = Field(default=False, alias="MINIO_SECURE")

    gemini_api_key: Optional[str] = Field(default=None, alias="GEMINI_API_KEY")
    gemini_embedding_model: str = Field(
        default="models/text-embedding-004", alias="GEMINI_EMBEDDING_MODEL"
    )
    gemini_vision_model: str = Field(
        default="models/gemini-1.5-flash", alias="GEMINI_VISION_MODEL"
    )

    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "populate_by_name": True,
    }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()  # type: ignore[arg-type]
