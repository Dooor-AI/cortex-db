"""CortexDB client."""

from typing import Optional, Union

from .collections import CollectionsAPI
from .connection_string import parse_connection_string
from .http_client import HTTPClient
from .records import RecordsAPI


class CortexClient:
    """Main client for interacting with CortexDB.

    Example:
        >>> import asyncio
        >>> from cortexdb import CortexClient
        >>>
        >>> async def main():
        ...     # Using options
        ...     async with CortexClient("http://localhost:8000") as client:
        ...         collections = await client.collections.list()
        ...
        ...     # Using connection string
        ...     async with CortexClient("cortexdb://my-key@localhost:8000") as client:
        ...         record = await client.records.create(
        ...             collection="documents",
        ...             data={"title": "Hello", "content": "World"}
        ...         )
        >>>
        >>> asyncio.run(main())
    """

    def __init__(
        self,
        base_url: Union[str, None] = None,
        api_key: Optional[str] = None,
        timeout: float = 30.0,
    ):
        """Initialize CortexDB client.

        Args:
            base_url: Base URL of CortexDB gateway or connection string.
                      If starts with "cortexdb://", it's parsed as a connection string.
                      Examples:
                          - "http://localhost:8000" (regular URL)
                          - "cortexdb://localhost:8000" (connection string)
                          - "cortexdb://my-key@localhost:8000" (connection string with API key)
            api_key: Optional API key for authentication (ignored if using connection string with key)
            timeout: Request timeout in seconds (default: 30.0)

        Example:
            >>> client = CortexClient("http://localhost:8000")
            >>> client = CortexClient("https://api.cortexdb.com", api_key="your-key")
            >>> client = CortexClient("cortexdb://my-key@localhost:8000")
        """
        # Handle connection string
        if base_url and base_url.startswith("cortexdb://"):
            parsed = parse_connection_string(base_url)
            base_url = parsed.base_url
            # Connection string api_key takes precedence
            if parsed.api_key:
                api_key = parsed.api_key
        
        # Default base_url if not provided
        if not base_url:
            base_url = "http://localhost:8000"
        
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
