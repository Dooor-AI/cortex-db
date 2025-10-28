"""Authentication middleware for API key validation."""

import json
from datetime import datetime
from typing import Optional

from fastapi import Header, HTTPException, status
from fastapi import Request

from ..core.postgres import get_postgres_client
from ..core.auth_cache import get_api_key_cache
from ..models.api_key import APIKey, APIKeyPermissions, APIKeyType
from ..utils.api_key import extract_key_from_header, hash_api_key
from ..utils.logger import get_logger

logger = get_logger(__name__)


class AuthenticationError(HTTPException):
    """Raised when authentication fails."""

    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class PermissionError(HTTPException):
    """Raised when user doesn't have required permissions."""

    def __init__(self, detail: str = "Permission denied"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


async def get_current_api_key(
    authorization: Optional[str] = Header(None)
) -> Optional[APIKey]:
    """Get the current API key from Authorization header.

    Args:
        authorization: Authorization header value

    Returns:
        APIKey if valid, None if no authorization provided

    Raises:
        AuthenticationError: If API key is invalid or expired
    """
    if not authorization:
        return None

    # Extract key from header
    key = extract_key_from_header(authorization)
    if not key:
        return None

    # Hash the key
    key_hash = hash_api_key(key)

    # Check cache first
    cache = get_api_key_cache()
    cached_key = cache.get(key_hash)
    
    if cached_key:
        logger.info("api_key_cache_hit", extra={"key_id": str(cached_key.id)})
        return cached_key

    # Cache miss - query database
    logger.info("api_key_cache_miss", extra={"key_prefix": key[:20]})
    postgres = get_postgres_client()

    async with postgres.pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT id, key_hash, key_prefix, name, description, type, permissions,
                   created_at, created_by, last_used_at, expires_at, enabled
            FROM api_keys
            WHERE key_hash = $1
            """,
            key_hash
        )

    if not row:
        logger.warning("invalid_api_key_attempt", extra={"key_prefix": key[:20]})
        raise AuthenticationError("Invalid API key")

    # Parse the API key
    # Parse permissions from JSON string if needed
    permissions_data = row["permissions"]
    if isinstance(permissions_data, str):
        permissions_data = json.loads(permissions_data)

    api_key = APIKey(
        id=row["id"],
        key_hash=row["key_hash"],
        key_prefix=row["key_prefix"],
        name=row["name"],
        description=row["description"],
        type=APIKeyType(row["type"]),
        permissions=APIKeyPermissions(**permissions_data),
        created_at=row["created_at"],
        created_by=row["created_by"],
        last_used_at=row["last_used_at"],
        expires_at=row["expires_at"],
        enabled=row["enabled"]
    )

    # Check if key is enabled
    if not api_key.enabled:
        logger.warning("disabled_api_key_attempt", extra={"key_id": str(api_key.id)})
        raise AuthenticationError("API key is disabled")

    # Check if key is expired
    if api_key.expires_at and api_key.expires_at < datetime.now(api_key.expires_at.tzinfo):
        logger.warning("expired_api_key_attempt", extra={"key_id": str(api_key.id)})
        raise AuthenticationError("API key has expired")

    # Cache the API key for future requests
    cache.set(key_hash, api_key, ttl=300.0)  # 5 minutes TTL

    # Update last_used_at (fire and forget)
    async with postgres.pool.acquire() as conn:
        await conn.execute(
            "UPDATE api_keys SET last_used_at = NOW() WHERE id = $1",
            api_key.id
        )

    logger.info("api_key_authenticated", extra={"key_id": str(api_key.id), "type": api_key.type.value})

    return api_key


async def require_api_key(api_key: Optional[APIKey] = None) -> APIKey:
    """Require a valid API key.

    Args:
        api_key: Optional API key from get_current_api_key dependency

    Returns:
        Validated APIKey

    Raises:
        AuthenticationError: If no API key provided
    """
    if not api_key:
        raise AuthenticationError("API key required")
    return api_key


async def require_admin(api_key: APIKey) -> APIKey:
    """Require admin API key.

    Args:
        api_key: Current API key

    Returns:
        APIKey if admin

    Raises:
        PermissionError: If not admin
    """
    if not api_key.permissions.admin:
        logger.warning(
            "admin_permission_denied",
            extra={"key_id": str(api_key.id), "type": api_key.type.value}
        )
        raise PermissionError("Admin access required")
    return api_key


async def check_database_access(api_key: APIKey, database: str) -> None:
    """Check if API key has access to a specific database.

    Args:
        api_key: Current API key
        database: Database name to check access for

    Raises:
        PermissionError: If access is denied
    """
    # Admin has access to everything
    if api_key.permissions.admin:
        return

    # Check if database is in allowed list
    if database not in api_key.permissions.databases:
        logger.warning(
            "database_access_denied",
            extra={
                "key_id": str(api_key.id),
                "database": database,
                "allowed_databases": api_key.permissions.databases
            }
        )
        raise PermissionError(f"Access denied to database '{database}'")


async def check_readonly(api_key: APIKey, operation: str) -> None:
    """Check if operation is allowed for readonly keys.

    Args:
        api_key: Current API key
        operation: Operation name (create, update, delete, etc.)

    Raises:
        PermissionError: If readonly key tries to write
    """
    # Admin and regular keys can do anything
    if not api_key.permissions.readonly:
        return

    # Readonly keys can only read and search
    allowed_operations = ["read", "search", "list", "get"]
    if operation not in allowed_operations:
        logger.warning(
            "readonly_write_attempt",
            extra={"key_id": str(api_key.id), "operation": operation}
        )
        raise PermissionError(f"Read-only API key cannot perform '{operation}' operation")

