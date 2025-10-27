"""HTTP client wrapper for CortexDB API."""

from typing import Any, Dict, Optional

import httpx

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


class HTTPClient:
    """HTTP client for CortexDB API with error handling."""

    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        timeout: float = 30.0,
    ):
        """Initialize HTTP client.

        Args:
            base_url: Base URL of CortexDB gateway
            api_key: Optional API key for authentication
            timeout: Request timeout in seconds
        """
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        self._client = httpx.AsyncClient(
            base_url=base_url,
            headers=headers,
            timeout=timeout,
        )

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    async def request(
        self,
        method: str,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Make HTTP request with error handling.

        Args:
            method: HTTP method (GET, POST, etc.)
            path: API path
            json: JSON body
            data: Form data
            files: Files to upload
            params: Query parameters

        Returns:
            Response JSON data

        Raises:
            CortexDBError: On any error
        """
        try:
            response = await self._client.request(
                method=method,
                url=path,
                json=json,
                data=data,
                files=files,
                params=params,
            )

            # Check for HTTP errors
            if response.status_code >= 400:
                self._raise_for_status(response)

            # Parse JSON response
            if response.content:
                return response.json()
            return None

        except httpx.TimeoutException as e:
            raise CortexDBTimeoutError(f"Request timed out: {e}") from e
        except httpx.ConnectError as e:
            raise CortexDBConnectionError(f"Connection failed: {e}") from e
        except httpx.HTTPError as e:
            raise CortexDBError(f"HTTP error occurred: {e}") from e

    def _raise_for_status(self, response: httpx.Response) -> None:
        """Raise appropriate exception based on status code.

        Args:
            response: HTTP response

        Raises:
            Specific CortexDBError subclass based on status code
        """
        status_code = response.status_code
        message = response.text

        # Try to extract error message from JSON
        try:
            error_data = response.json()
            if "detail" in error_data:
                message = error_data["detail"]
        except Exception:
            pass

        if status_code == 400:
            raise CortexDBValidationError(message, status_code, response)
        elif status_code == 401:
            raise CortexDBAuthenticationError(message, status_code, response)
        elif status_code == 403:
            raise CortexDBPermissionError(message, status_code, response)
        elif status_code == 404:
            raise CortexDBNotFoundError(message, status_code, response)
        elif status_code >= 500:
            raise CortexDBServerError(message, status_code, response)
        else:
            raise CortexDBError(message, status_code, response)

    async def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """GET request."""
        return await self.request("GET", path, params=params)

    async def post(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """POST request."""
        return await self.request("POST", path, json=json, data=data, files=files)

    async def patch(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """PATCH request."""
        return await self.request("PATCH", path, json=json, data=data, files=files)

    async def delete(self, path: str) -> Any:
        """DELETE request."""
        return await self.request("DELETE", path)
