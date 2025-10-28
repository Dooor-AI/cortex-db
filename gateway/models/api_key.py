"""API Key models."""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class APIKeyType(str, Enum):
    """Type of API key."""

    ADMIN = "admin"
    DATABASE = "database"
    READONLY = "readonly"


class APIKeyPermissions(BaseModel):
    """Permissions for an API key."""

    admin: bool = False
    manage_keys: bool = False
    manage_databases: bool = False
    manage_collections: bool = False
    manage_providers: bool = False
    databases: List[str] = Field(default_factory=list)
    readonly: bool = False


class APIKey(BaseModel):
    """API Key model (stored in database)."""

    id: UUID
    key_hash: str
    key_prefix: str
    name: str
    description: Optional[str] = None
    type: APIKeyType
    permissions: APIKeyPermissions
    created_at: datetime
    created_by: Optional[UUID] = None
    last_used_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    enabled: bool = True

    class Config:
        from_attributes = True


class APIKeyCreate(BaseModel):
    """Request to create a new API key."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    type: APIKeyType
    databases: Optional[List[str]] = None
    expires_at: Optional[datetime] = None


class APIKeyResponse(BaseModel):
    """API Key response (without sensitive data)."""

    id: UUID
    key_prefix: str
    name: str
    description: Optional[str] = None
    type: APIKeyType
    permissions: APIKeyPermissions
    created_at: datetime
    created_by: Optional[UUID] = None
    last_used_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    enabled: bool


class APIKeyCreated(BaseModel):
    """Response after creating an API key (includes actual key - shown only once)."""

    id: UUID
    key: str  # Full key - only shown once!
    key_prefix: str
    name: str
    type: APIKeyType
    permissions: APIKeyPermissions
    created_at: datetime
    expires_at: Optional[datetime] = None


class APIKeyUpdate(BaseModel):
    """Request to update an API key."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    databases: Optional[List[str]] = None
    expires_at: Optional[datetime] = None
    enabled: Optional[bool] = None

