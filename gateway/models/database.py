from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DatabaseCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=63, pattern=r"^[a-z][a-z0-9_]*$")
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class Database(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    name: str
    description: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
