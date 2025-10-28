"""Bootstrap initial setup for CortexDB."""

import os
from datetime import datetime

import asyncpg

from ..models.api_key import APIKeyPermissions, APIKeyType
from ..utils.api_key import generate_api_key
from ..utils.logger import get_logger

logger = get_logger(__name__)


async def bootstrap_admin_key(pool: asyncpg.Pool) -> None:
    """Bootstrap admin API key if none exists.

    This runs on first startup to create an initial admin key.
    The key is either:
    1. Read from CORTEXDB_ADMIN_KEY environment variable
    2. Auto-generated and logged to console

    Args:
        pool: PostgreSQL connection pool
    """
    async with pool.acquire() as conn:
        # Check if any admin keys exist
        admin_count = await conn.fetchval(
            "SELECT COUNT(*) FROM api_keys WHERE type = 'admin'"
        )

        if admin_count > 0:
            logger.info("admin_key_exists", extra={"count": admin_count})
            return

        # No admin keys - create one
        logger.info("bootstrapping_admin_key")

        # Check environment variable
        env_key = os.getenv("CORTEXDB_ADMIN_KEY")

        if env_key:
            # Use provided key
            from ..utils.api_key import hash_api_key
            
            full_key = env_key
            key_hash = hash_api_key(env_key)
            key_prefix = env_key[:25] + "..."
            
            logger.info("using_env_admin_key")
        else:
            # Generate new key
            full_key, key_hash, key_prefix = generate_api_key(APIKeyType.ADMIN)
            logger.info("generated_new_admin_key")

        # Admin permissions
        permissions = APIKeyPermissions(
            admin=True,
            manage_keys=True,
            manage_databases=True,
            manage_collections=True,
            manage_providers=True,
            databases=[],
            readonly=False,
        )

        # Insert admin key
        await conn.execute(
            """
            INSERT INTO api_keys (
                key_hash, key_prefix, name, description, type, permissions, enabled
            )
            VALUES ($1, $2, $3, $4, $5, $6, TRUE)
            """,
            key_hash,
            key_prefix,
            "Admin Key (Bootstrap)",
            "Initial admin key created on first startup",
            APIKeyType.ADMIN.value,
            permissions.model_dump_json(),
        )

        # Log the key prominently
        logger.info(
            "admin_key_created",
            extra={
                "key": full_key,
                "key_prefix": key_prefix,
            },
        )

        # Print to console (visible in logs)
        print("\n" + "=" * 80)
        print("🔑 CORTEXDB ADMIN API KEY CREATED")
        print("=" * 80)
        print(f"\nAPI Key: {full_key}")
        print(f"\nConnection String: cortexdb://{full_key}@localhost:8000")
        print("\n⚠️  IMPORTANT:")
        print("   • Save this key now - it won't be shown again!")
        print("   • Use this key to access the dashboard and create other keys")
        print("   • Set CORTEXDB_ADMIN_KEY env var to use a custom key")
        print("\n" + "=" * 80 + "\n")

