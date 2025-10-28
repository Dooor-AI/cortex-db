"""API Key management endpoints."""

import json
from datetime import datetime
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from ..core.postgres import get_postgres_client
from ..middleware.auth import get_current_api_key, require_admin
from ..models.api_key import (
    APIKey,
    APIKeyCreate,
    APIKeyCreated,
    APIKeyPermissions,
    APIKeyResponse,
    APIKeyType,
    APIKeyUpdate,
)
from ..utils.api_key import generate_api_key, hash_api_key
from ..utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api-keys", tags=["API Keys"])


@router.get("", response_model=List[APIKeyResponse])
async def list_api_keys(
    current_key: APIKey = Depends(get_current_api_key),
):
    """List all API keys (admin only).

    Returns:
        List of API keys (without sensitive data)
    """
    # Check admin permission manually
    if not current_key or not current_key.permissions.admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    postgres = get_postgres_client()

    async with postgres.pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, key_prefix, name, description, type, permissions,
                   created_at, created_by, last_used_at, expires_at, enabled
            FROM api_keys
            ORDER BY created_at DESC
            """
        )

    keys = []
    for row in rows:
        # Parse permissions from JSON string if needed
        permissions_data = row["permissions"]
        if isinstance(permissions_data, str):
            permissions_data = json.loads(permissions_data)

        keys.append(
            APIKeyResponse(
                id=row["id"],
                key_prefix=row["key_prefix"],
                name=row["name"],
                description=row["description"],
                type=APIKeyType(row["type"]),
                permissions=APIKeyPermissions(**permissions_data),
                created_at=row["created_at"],
                created_by=row["created_by"],
                last_used_at=row["last_used_at"],
                expires_at=row["expires_at"],
                enabled=row["enabled"],
            )
        )

    logger.info("api_keys_listed", extra={"count": len(keys), "by_key_id": str(current_key.id)})
    return keys


@router.post("", response_model=APIKeyCreated, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    request: APIKeyCreate,
    current_key: APIKey = Depends(get_current_api_key),
    _: APIKey = Depends(require_admin),
):
    """Create a new API key (admin only).

    Args:
        request: API key creation request

    Returns:
        Created API key with full key (shown only once!)
    """
    # Build permissions based on type
    permissions = _build_permissions(request)

    # Generate the API key
    full_key, key_hash, key_prefix = generate_api_key(request.type)

    # Store in database
    postgres = get_postgres_client()

    async with postgres.pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO api_keys (
                key_hash, key_prefix, name, description, type, permissions,
                created_by, expires_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id, key_prefix, name, type, permissions, created_at, expires_at
            """,
            key_hash,
            key_prefix,
            request.name,
            request.description,
            request.type.value,
            permissions.model_dump(),
            current_key.id,
            request.expires_at,
        )

    logger.info(
        "api_key_created",
        extra={
            "key_id": str(row["id"]),
            "key_type": request.type.value,
            "created_by": str(current_key.id),
        },
    )

    # Parse permissions from JSON string if needed
    permissions_data = row["permissions"]
    if isinstance(permissions_data, str):
        permissions_data = json.loads(permissions_data)

    return APIKeyCreated(
        id=row["id"],
        key=full_key,  # Full key - only shown once!
        key_prefix=row["key_prefix"],
        name=row["name"],
        type=APIKeyType(row["type"]),
        permissions=APIKeyPermissions(**permissions_data),
        created_at=row["created_at"],
        expires_at=row["expires_at"],
    )


@router.get("/{key_id}", response_model=APIKeyResponse)
async def get_api_key(
    key_id: UUID,
    current_key: APIKey = Depends(get_current_api_key),
    _: APIKey = Depends(require_admin),
):
    """Get API key details (admin only).

    Args:
        key_id: ID of the API key

    Returns:
        API key details
    """
    postgres = get_postgres_client()

    async with postgres.pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT id, key_prefix, name, description, type, permissions,
                   created_at, created_by, last_used_at, expires_at, enabled
            FROM api_keys
            WHERE id = $1
            """,
            key_id,
        )

    if not row:
        raise HTTPException(status_code=404, detail="API key not found")

    # Parse permissions from JSON string if needed
    permissions_data = row["permissions"]
    if isinstance(permissions_data, str):
        permissions_data = json.loads(permissions_data)

    return APIKeyResponse(
        id=row["id"],
        key_prefix=row["key_prefix"],
        name=row["name"],
        description=row["description"],
        type=APIKeyType(row["type"]),
        permissions=APIKeyPermissions(**permissions_data),
        created_at=row["created_at"],
        created_by=row["created_by"],
        last_used_at=row["last_used_at"],
        expires_at=row["expires_at"],
        enabled=row["enabled"],
    )


@router.patch("/{key_id}", response_model=APIKeyResponse)
async def update_api_key(
    key_id: UUID,
    request: APIKeyUpdate,
    current_key: APIKey = Depends(get_current_api_key),
    _: APIKey = Depends(require_admin),
):
    """Update API key (admin only).

    Args:
        key_id: ID of the API key
        request: Update request

    Returns:
        Updated API key
    """
    postgres = get_postgres_client()

    # Build update query dynamically
    updates = []
    values = []
    param_idx = 1

    if request.name is not None:
        updates.append(f"name = ${param_idx}")
        values.append(request.name)
        param_idx += 1

    if request.description is not None:
        updates.append(f"description = ${param_idx}")
        values.append(request.description)
        param_idx += 1

    if request.databases is not None:
        # Update permissions.databases
        updates.append(f"permissions = jsonb_set(permissions, '{{databases}}', ${param_idx}::jsonb)")
        values.append(json.dumps(request.databases))
        param_idx += 1

    if request.expires_at is not None:
        updates.append(f"expires_at = ${param_idx}")
        values.append(request.expires_at)
        param_idx += 1

    if request.enabled is not None:
        updates.append(f"enabled = ${param_idx}")
        values.append(request.enabled)
        param_idx += 1

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    # Add key_id as last parameter
    values.append(key_id)

    async with postgres.pool.acquire() as conn:
        row = await conn.fetchrow(
            f"""
            UPDATE api_keys
            SET {", ".join(updates)}
            WHERE id = ${param_idx}
            RETURNING id, key_prefix, name, description, type, permissions,
                      created_at, created_by, last_used_at, expires_at, enabled
            """,
            *values,
        )

    if not row:
        raise HTTPException(status_code=404, detail="API key not found")

    logger.info("api_key_updated", extra={"key_id": str(key_id), "updated_by": str(current_key.id)})

    # Parse permissions from JSON string if needed
    permissions_data = row["permissions"]
    if isinstance(permissions_data, str):
        permissions_data = json.loads(permissions_data)

    return APIKeyResponse(
        id=row["id"],
        key_prefix=row["key_prefix"],
        name=row["name"],
        description=row["description"],
        type=APIKeyType(row["type"]),
        permissions=APIKeyPermissions(**permissions_data),
        created_at=row["created_at"],
        created_by=row["created_by"],
        last_used_at=row["last_used_at"],
        expires_at=row["expires_at"],
        enabled=row["enabled"],
    )


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    key_id: UUID,
    current_key: APIKey = Depends(get_current_api_key),
    _: APIKey = Depends(require_admin),
):
    """Delete (revoke) an API key (admin only).

    Args:
        key_id: ID of the API key to delete
    """
    # Prevent deleting yourself
    if key_id == current_key.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own API key")

    postgres = get_postgres_client()

    async with postgres.pool.acquire() as conn:
        result = await conn.execute(
            "DELETE FROM api_keys WHERE id = $1",
            key_id,
        )

    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="API key not found")

    logger.info("api_key_deleted", extra={"key_id": str(key_id), "deleted_by": str(current_key.id)})


def _build_permissions(request: APIKeyCreate) -> APIKeyPermissions:
    """Build permissions object based on key type and request.

    Args:
        request: API key creation request

    Returns:
        APIKeyPermissions object
    """
    if request.type == APIKeyType.ADMIN:
        return APIKeyPermissions(
            admin=True,
            manage_keys=True,
            manage_databases=True,
            manage_collections=True,
            manage_providers=True,
            databases=[],
            readonly=False,
        )
    elif request.type == APIKeyType.DATABASE:
        return APIKeyPermissions(
            admin=False,
            manage_keys=False,
            manage_databases=False,
            manage_collections=True,
            manage_providers=False,
            databases=request.databases or [],
            readonly=False,
        )
    elif request.type == APIKeyType.READONLY:
        return APIKeyPermissions(
            admin=False,
            manage_keys=False,
            manage_databases=False,
            manage_collections=False,
            manage_providers=False,
            databases=request.databases or [],
            readonly=True,
        )

    # Fallback (shouldn't reach here)
    return APIKeyPermissions()

