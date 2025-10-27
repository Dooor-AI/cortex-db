"""CortexDB exceptions."""

from typing import Any, Optional


class CortexDBError(Exception):
    """Base exception for all CortexDB errors."""

    def __init__(self, message: str, status_code: Optional[int] = None, response: Any = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response = response


class CortexDBConnectionError(CortexDBError):
    """Raised when connection to CortexDB fails."""


class CortexDBTimeoutError(CortexDBError):
    """Raised when request times out."""


class CortexDBNotFoundError(CortexDBError):
    """Raised when resource is not found (404)."""


class CortexDBValidationError(CortexDBError):
    """Raised when request validation fails (400)."""


class CortexDBAuthenticationError(CortexDBError):
    """Raised when authentication fails (401)."""


class CortexDBPermissionError(CortexDBError):
    """Raised when permission is denied (403)."""


class CortexDBServerError(CortexDBError):
    """Raised when server returns 5xx error."""
