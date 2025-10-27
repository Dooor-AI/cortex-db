"""Collections API for CortexDB."""

from typing import List, Optional

from .http_client import HTTPClient
from .models import CollectionSchema, FieldDefinition


class CollectionsAPI:
    """API for managing collections."""

    def __init__(self, http_client: HTTPClient):
        """Initialize Collections API.

        Args:
            http_client: HTTP client instance
        """
        self._http = http_client

    async def list(self, database: Optional[str] = None) -> List[CollectionSchema]:
        """List all collections.

        Args:
            database: Optional database name to filter by

        Returns:
            List of collection schemas
        """
        if database:
            response = await self._http.get(f"/databases/{database}/collections")
        else:
            response = await self._http.get("/collections")

        # Handle both list and dict responses
        if isinstance(response, list):
            collections_data = response
        else:
            collections_data = response.get("collections", [])

        # Parse collections - API returns nested schema structure
        collections = []
        for item in collections_data:
            # Check if schema is nested
            if "schema" in item and isinstance(item["schema"], dict):
                schema_data = item["schema"]
                # Add database info if present
                if "database_name" in item:
                    schema_data["database"] = item["database_name"]
                collections.append(CollectionSchema(**schema_data))
            else:
                # Direct schema format
                collections.append(CollectionSchema(**item))

        return collections

    async def create(
        self,
        name: str,
        fields: List[FieldDefinition],
        database: Optional[str] = None,
        embedding_provider: Optional[str] = None,
    ) -> CollectionSchema:
        """Create a new collection.

        Args:
            name: Collection name
            fields: List of field definitions
            database: Optional database name
            embedding_provider: Optional embedding provider name

        Returns:
            Created collection schema

        Raises:
            ValueError: If vectorize=True is used without embedding_provider

        Example:
            >>> from cortexdb import CortexClient, FieldDefinition, FieldType
            >>> async with CortexClient() as client:
            ...     schema = await client.collections.create(
            ...         name="documents",
            ...         fields=[
            ...             FieldDefinition(name="title", type=FieldType.STRING),
            ...             FieldDefinition(
            ...                 name="content",
            ...                 type=FieldType.TEXT,
            ...                 vectorize=True
            ...             )
            ...         ],
            ...         embedding_provider="gemini-pro"
            ...     )
        """
        # Check if any field has vectorize=True
        has_vectorize = any(field.vectorize for field in fields)
        
        if has_vectorize and not embedding_provider:
            raise ValueError(
                "embedding_provider is required when using vectorize=True. "
                "Please provide an embedding_provider parameter or set vectorize=False on your fields."
            )
        
        payload = {
            "name": name,
            "fields": [field.model_dump(exclude_none=True) for field in fields],
        }

        if embedding_provider:
            payload["config"] = {"embedding_provider_id": embedding_provider}

        if database:
            response = await self._http.post(
                f"/databases/{database}/collections", json=payload
            )
        else:
            response = await self._http.post("/collections", json=payload)

        # API returns creation result, not schema - fetch the schema
        collection_name = response.get("collection", name)
        return await self.get(collection_name, database)

    async def get(self, name: str, database: Optional[str] = None) -> CollectionSchema:
        """Get collection schema.

        Args:
            name: Collection name
            database: Optional database name

        Returns:
            Collection schema

        Raises:
            CortexDBNotFoundError: If collection doesn't exist
        """
        path = f"/collections/{name}"
        response = await self._http.get(path)
        return CollectionSchema(**response)

    async def delete(self, name: str, database: Optional[str] = None) -> None:
        """Delete a collection.

        Args:
            name: Collection name
            database: Optional database name

        Raises:
            CortexDBNotFoundError: If collection doesn't exist
        """
        if database:
            await self._http.delete(f"/databases/{database}/collections/{name}")
        else:
            await self._http.delete(f"/collections/{name}")
