"""Records API for CortexDB."""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .http_client import HTTPClient
from .models import QueryRequest, Record, SearchResult, VectorChunk


class RecordsAPI:
    """API for managing records."""

    def __init__(self, http_client: HTTPClient):
        """Initialize Records API.

        Args:
            http_client: HTTP client instance
        """
        self._http = http_client

    async def create(
        self,
        collection: str,
        data: Dict[str, Any],
        files: Optional[Dict[str, Union[str, Path, bytes]]] = None,
    ) -> Record:
        """Create a new record.

        Args:
            collection: Collection name
            data: Record data (field names and values)
            files: Optional files to upload (field name -> file path or bytes)

        Returns:
            Created record

        Example:
            >>> # Create text record
            >>> record = await client.records.create(
            ...     collection="documents",
            ...     data={"title": "Hello", "content": "World"}
            ... )
            >>>
            >>> # Create record with file
            >>> record = await client.records.create(
            ...     collection="documents",
            ...     data={"title": "My PDF", "description": "Important doc"},
            ...     files={"pdf": "/path/to/file.pdf"}
            ... )
        """
        if files:
            # Multipart form data
            form_data = data.copy()
            file_objects = {}

            for field_name, file_value in files.items():
                if isinstance(file_value, (str, Path)):
                    # File path
                    file_path = Path(file_value)
                    file_objects[field_name] = open(file_path, "rb")
                elif isinstance(file_value, bytes):
                    # Bytes
                    file_objects[field_name] = file_value
                else:
                    file_objects[field_name] = file_value

            response = await self._http.post(
                f"/collections/{collection}/records",
                data=form_data,
                files=file_objects,
            )

            # Close file handles
            for file_obj in file_objects.values():
                if hasattr(file_obj, "close"):
                    file_obj.close()
        else:
            # JSON request
            response = await self._http.post(
                f"/collections/{collection}/records",
                json=data,
            )

        # Create returns only ID - fetch the full record
        record_id = response.get("id")
        return await self.get(collection, record_id)

    async def get(self, collection: str, record_id: str) -> Record:
        """Get a record by ID.

        Args:
            collection: Collection name
            record_id: Record ID

        Returns:
            Record data

        Raises:
            CortexDBNotFoundError: If record doesn't exist
        """
        response = await self._http.get(f"/collections/{collection}/records/{record_id}")

        record_data = response.get("record", response)
        return Record(
            id=record_data["id"],
            created_at=record_data["created_at"],
            updated_at=record_data["updated_at"],
            data=record_data,
        )

    async def update(
        self,
        collection: str,
        record_id: str,
        data: Dict[str, Any],
        files: Optional[Dict[str, Union[str, Path, bytes]]] = None,
    ) -> Record:
        """Update a record.

        Args:
            collection: Collection name
            record_id: Record ID
            data: Updated field values
            files: Optional files to upload

        Returns:
            Updated record

        Raises:
            CortexDBNotFoundError: If record doesn't exist
        """
        if files:
            # Multipart form data
            form_data = data.copy()
            file_objects = {}

            for field_name, file_value in files.items():
                if isinstance(file_value, (str, Path)):
                    file_path = Path(file_value)
                    file_objects[field_name] = open(file_path, "rb")
                elif isinstance(file_value, bytes):
                    file_objects[field_name] = file_value
                else:
                    file_objects[field_name] = file_value

            response = await self._http.patch(
                f"/collections/{collection}/records/{record_id}",
                data=form_data,
                files=file_objects,
            )

            # Close file handles
            for file_obj in file_objects.values():
                if hasattr(file_obj, "close"):
                    file_obj.close()
        else:
            # JSON request
            response = await self._http.patch(
                f"/collections/{collection}/records/{record_id}",
                json=data,
            )

        # Update returns only ID - fetch the full record
        return await self.get(collection, record_id)

    async def delete(self, collection: str, record_id: str) -> None:
        """Delete a record.

        Args:
            collection: Collection name
            record_id: Record ID

        Raises:
            CortexDBNotFoundError: If record doesn't exist
        """
        await self._http.delete(f"/collections/{collection}/records/{record_id}")

    async def query(
        self,
        collection: str,
        query: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """Semantic search query.

        Args:
            collection: Collection name
            query: Search query text
            limit: Maximum results to return (1-100)
            filters: Optional filter conditions

        Returns:
            List of search results with scores

        Example:
            >>> results = await client.records.query(
            ...     collection="documents",
            ...     query="machine learning applications",
            ...     limit=5,
            ...     filters={"year": {"$gte": 2020}}
            ... )
            >>> for result in results:
            ...     print(f"{result.score:.3f} - {result.data['title']}")
        """
        request = QueryRequest(query=query, limit=limit, filters=filters)

        response = await self._http.post(
            f"/collections/{collection}/query",
            json=request.model_dump(exclude_none=True),
        )

        return [
            SearchResult(
                id=item["id"],
                score=item["score"],
                data=item,
            )
            for item in response.get("results", [])
        ]

    async def get_vectors(self, collection: str, record_id: str) -> List[VectorChunk]:
        """Get vectorized chunks for a record.

        Args:
            collection: Collection name
            record_id: Record ID

        Returns:
            List of vector chunks

        Raises:
            CortexDBNotFoundError: If record doesn't exist
        """
        response = await self._http.get(
            f"/collections/{collection}/records/{record_id}/vectors"
        )

        return [VectorChunk(**chunk) for chunk in response.get("vectors", [])]

    async def download_file(
        self,
        collection: str,
        record_id: str,
        field_name: str,
        output_path: Optional[Union[str, Path]] = None,
    ) -> bytes:
        """Download a file from a record's file field.

        Args:
            collection: Collection name
            record_id: Record ID
            field_name: Name of the file field
            output_path: Optional path to save the file. If not provided, returns bytes.

        Returns:
            File content as bytes (if output_path not provided)

        Raises:
            CortexDBNotFoundError: If record or file doesn't exist

        Example:
            >>> # Download to file
            >>> await client.records.download_file(
            ...     collection="documents",
            ...     record_id="abc-123",
            ...     field_name="pdf",
            ...     output_path="/path/to/save/file.pdf"
            ... )
            >>>
            >>> # Get bytes
            >>> content = await client.records.download_file(
            ...     collection="documents",
            ...     record_id="abc-123",
            ...     field_name="pdf"
            ... )
        """
        # Use direct httpx call for binary download
        response = await self._http._client.get(
            f"/collections/{collection}/records/{record_id}/files/{field_name}"
        )

        # Check for errors
        if response.status_code >= 400:
            self._http._raise_for_status(response)

        content = response.content

        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_bytes(content)

        return content
