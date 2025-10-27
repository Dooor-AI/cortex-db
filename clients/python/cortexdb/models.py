"""CortexDB data models."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class FieldType(str, Enum):
    """Field type enumeration."""

    STRING = "string"
    TEXT = "text"
    INT = "int"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    JSON = "json"
    FILE = "file"


class StoreLocation(str, Enum):
    """Storage location enumeration."""

    POSTGRES = "postgres"
    QDRANT = "qdrant"
    QDRANT_PAYLOAD = "qdrant_payload"
    MINIO = "minio"


class ExtractConfig(BaseModel):
    """Configuration for text extraction from files."""

    chunk_size: Optional[int] = Field(None, description="Size of text chunks")
    chunk_overlap: Optional[int] = Field(None, description="Overlap between chunks")


class FieldDefinition(BaseModel):
    """Field definition in a collection schema."""

    name: str = Field(..., description="Field name")
    type: FieldType = Field(..., description="Field type")
    vectorize: bool = Field(False, description="Whether to vectorize this field")
    store_in: List[StoreLocation] = Field(
        default_factory=lambda: [StoreLocation.POSTGRES], description="Where to store the field"
    )
    extract_config: Optional[ExtractConfig] = Field(None, description="Text extraction config")


class CollectionSchema(BaseModel):
    """Collection schema definition."""

    name: str = Field(..., description="Collection name")
    database: Optional[str] = Field(None, description="Database name")
    fields: List[FieldDefinition] = Field(..., description="Field definitions")
    embedding_provider: Optional[str] = Field(None, description="Embedding provider name")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")


class Record(BaseModel):
    """Record in a collection."""

    id: str = Field(..., description="Record ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    data: Dict[str, Any] = Field(default_factory=dict, description="Record data")


class VectorChunk(BaseModel):
    """Vectorized text chunk."""

    id: str = Field(..., description="Chunk ID")
    field: str = Field(..., description="Field name")
    chunk_index: int = Field(..., description="Chunk index")
    text: str = Field(..., description="Chunk text")


class SearchResult(BaseModel):
    """Search result with score."""

    id: str = Field(..., description="Record ID")
    score: float = Field(..., description="Similarity score")
    data: Dict[str, Any] = Field(default_factory=dict, description="Record data")


class QueryRequest(BaseModel):
    """Query request parameters."""

    query: str = Field(..., description="Search query text")
    limit: int = Field(10, ge=1, le=100, description="Maximum results to return")
    filters: Optional[Dict[str, Any]] = Field(None, description="Filter conditions")


class EmbeddingProvider(BaseModel):
    """Embedding provider configuration."""

    name: str = Field(..., description="Provider name")
    api_key: str = Field(..., description="API key")
    model: Optional[str] = Field(None, description="Model name")
    api_base: Optional[str] = Field(None, description="API base URL")
