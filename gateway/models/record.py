from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(..., description="Natural language search query")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Optional filter map")
    limit: int = Field(default=10, ge=1, le=100)


class QueryRequest(BaseModel):
    filters: Dict[str, Any] = Field(default_factory=dict)
    limit: int = Field(default=100, ge=1, le=500)
    offset: int = Field(default=0, ge=0)
