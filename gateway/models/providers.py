from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EmbeddingProviderType(str, Enum):
    GEMINI = "gemini"


class EmbeddingProviderBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=128)
    provider: EmbeddingProviderType = Field(default=EmbeddingProviderType.GEMINI)
    embedding_model: str = Field(min_length=1)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class EmbeddingProviderCreate(EmbeddingProviderBase):
    api_key: str = Field(min_length=1)


class EmbeddingProvider(EmbeddingProviderBase):
    id: UUID
    enabled: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    has_api_key: bool = True

    @field_validator("metadata", mode="before")
    @classmethod
    def ensure_metadata_dict(cls, value: Any) -> Dict[str, Any]:
        if value is None:
            return {}
        if isinstance(value, dict):
            return value
        raise ValueError("metadata must be an object")


class EmbeddingProviderRecord(EmbeddingProvider):
    api_key: str
