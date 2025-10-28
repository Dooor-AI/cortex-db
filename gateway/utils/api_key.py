"""Utilities for API key generation and validation."""

import hashlib
import secrets
from typing import Tuple

from ..models.api_key import APIKeyType


def generate_api_key(key_type: APIKeyType) -> Tuple[str, str, str]:
    """Generate a new API key.

    Args:
        key_type: Type of key to generate (admin, database, readonly)

    Returns:
        Tuple of (full_key, key_hash, key_prefix)
        - full_key: The actual key to give to user (shown only once)
        - key_hash: SHA-256 hash to store in database
        - key_prefix: First ~25 chars for display purposes

    Example:
        >>> key, hash, prefix = generate_api_key(APIKeyType.ADMIN)
        >>> key
        'cortexdb_admin_abc123xyz456def789ghi012jkl034mno567pqr890'
        >>> prefix
        'cortexdb_admin_abc123...'
    """
    # Generate random part (32 bytes = 64 hex chars)
    random_part = secrets.token_hex(32)

    # Format: cortexdb_[type]_[random]
    type_prefix = _get_type_prefix(key_type)
    full_key = f"cortexdb_{type_prefix}_{random_part}"

    # Hash for storage
    key_hash = hash_api_key(full_key)

    # Prefix for display (first 25 chars)
    key_prefix = full_key[:25] + "..."

    return full_key, key_hash, key_prefix


def hash_api_key(api_key: str) -> str:
    """Hash an API key using SHA-256.

    Args:
        api_key: The API key to hash

    Returns:
        SHA-256 hash as hex string

    Example:
        >>> hash_api_key('cortexdb_admin_abc123')
        'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'
    """
    return hashlib.sha256(api_key.encode()).hexdigest()


def verify_api_key(provided_key: str, stored_hash: str) -> bool:
    """Verify an API key against its stored hash.

    Args:
        provided_key: The key provided by the user
        stored_hash: The hash stored in the database

    Returns:
        True if the key matches the hash, False otherwise

    Example:
        >>> key = "cortexdb_admin_abc123"
        >>> stored = hash_api_key(key)
        >>> verify_api_key(key, stored)
        True
        >>> verify_api_key("wrong_key", stored)
        False
    """
    return hash_api_key(provided_key) == stored_hash


def _get_type_prefix(key_type: APIKeyType) -> str:
    """Get the prefix for a key type.

    Args:
        key_type: The type of API key

    Returns:
        Prefix string (admin, live, test)
    """
    if key_type == APIKeyType.ADMIN:
        return "admin"
    elif key_type == APIKeyType.DATABASE:
        return "live"
    elif key_type == APIKeyType.READONLY:
        return "test"
    return "unknown"


def extract_key_from_header(authorization: str) -> str:
    """Extract API key from Authorization header.

    Args:
        authorization: Authorization header value

    Returns:
        Extracted API key

    Example:
        >>> extract_key_from_header("Bearer cortexdb_admin_abc123")
        'cortexdb_admin_abc123'
        >>> extract_key_from_header("cortexdb_admin_abc123")
        'cortexdb_admin_abc123'
    """
    if not authorization:
        return ""

    # Remove 'Bearer ' prefix if present
    if authorization.startswith("Bearer "):
        return authorization[7:].strip()

    return authorization.strip()

