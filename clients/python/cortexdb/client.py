"""CortexDB client."""

from typing import Optional

from .collections import CollectionsAPI
from .http_client import HTTPClient
from .records import RecordsAPI


class CortexClient:
    """Main client for interacting with CortexDB.

    Example:
        >>> import asyncio
        >>> from cortexdb import CortexClient
        >>>
        >>> async def main():
        ...     async with CortexClient("http://localhost:8000") as client:
        ...         # List collections
        ...         collections = await client.collections.list()
        ...
        ...         # Create a record
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

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        api_key: Optional[str] = None,
        timeout: float = 30.0,
    ):
        """Initialize CortexDB client.

        Args:
            base_url: Base URL of CortexDB gateway (default: http://localhost:8000)
            api_key: Optional API key for authentication
            timeout: Request timeout in seconds (default: 30.0)

        Example:
            >>> client = CortexClient("http://localhost:8000")
            >>> client = CortexClient("https://api.cortexdb.com", api_key="your-key")
        """
        self._http = HTTPClient(base_url=base_url, api_key=api_key, timeout=timeout)

        # API modules
        self.collections = CollectionsAPI(self._http)
        self.records = RecordsAPI(self._http)

    async def close(self) -> None:
        """Close the client and cleanup resources.

        Example:
            >>> client = CortexClient()
            >>> try:
            ...     # Use client
            ...     pass
            ... finally:
            ...     await client.close()
        """
        await self._http.close()

    async def __aenter__(self) -> "CortexClient":
        """Context manager entry."""
        return self

    async def __aexit__(self, *args: any) -> None:
        """Context manager exit."""
        await self.close()

    async def healthcheck(self) -> bool:
        """Check if CortexDB gateway is healthy.

        Returns:
            True if healthy, False otherwise

        Example:
            >>> is_healthy = await client.healthcheck()
            >>> if is_healthy:
            ...     print("CortexDB is running!")
        """
        try:
            await self._http.get("/health")
            return True
        except Exception:
            return False
