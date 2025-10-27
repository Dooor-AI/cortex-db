"""CortexDB Python SDK.

Official Python client for CortexDB - Multi-modal RAG Platform.

Example:
    >>> import asyncio
    >>> from cortexdb import CortexClient, FieldDefinition, FieldType
    >>>
    >>> async def main():
    ...     async with CortexClient("http://localhost:8000") as client:
    ...         # Create collection
    ...         await client.collections.create(
    ...             name="documents",
    ...             fields=[
    ...                 FieldDefinition(name="title", type=FieldType.STRING),
    ...                 FieldDefinition(name="content", type=FieldType.TEXT, vectorize=True)
    ...             ]
    ...         )
    ...
    ...         # Create record
    ...         record = await client.records.create(
    ...             collection="documents",
    ...             data={"title": "Hello", "content": "World"}
    ...         )
    ...
    ...         # Search
    ...         results = await client.records.query(
    ...             collection="documents",
    ...             query="hello world",
    ...             limit=10
    ...         )
    >>>
    >>> asyncio.run(main())
"""

__version__ = "0.1.1"

from .client import CortexClient
from .exceptions import (
    CortexDBAuthenticationError,
    CortexDBConnectionError,
    CortexDBError,
    CortexDBNotFoundError,
    CortexDBPermissionError,
    CortexDBServerError,
    CortexDBTimeoutError,
    CortexDBValidationError,
)
from .models import (
    CollectionSchema,
    EmbeddingProvider,
    ExtractConfig,
    FieldDefinition,
    FieldType,
    QueryRequest,
    Record,
    SearchResult,
    StoreLocation,
    VectorChunk,
)

__all__ = [
    # Client
    "CortexClient",
    # Exceptions
    "CortexDBError",
    "CortexDBConnectionError",
    "CortexDBTimeoutError",
    "CortexDBNotFoundError",
    "CortexDBValidationError",
    "CortexDBAuthenticationError",
    "CortexDBPermissionError",
    "CortexDBServerError",
    # Models
    "CollectionSchema",
    "FieldDefinition",
    "FieldType",
    "StoreLocation",
    "ExtractConfig",
    "Record",
    "SearchResult",
    "VectorChunk",
    "QueryRequest",
    "EmbeddingProvider",
]
