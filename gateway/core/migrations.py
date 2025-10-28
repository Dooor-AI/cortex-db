"""Database migrations manager."""

import asyncpg
from pathlib import Path
from typing import Optional

from ..utils.logger import get_logger

logger = get_logger(__name__)


class MigrationManager:
    """Manages database schema migrations."""

    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool
        self.migrations_dir = Path(__file__).parent.parent / "migrations"

    async def initialize(self) -> None:
        """Initialize migrations table and run pending migrations."""
        await self._create_migrations_table()
        await self.run_migrations()

    async def _create_migrations_table(self) -> None:
        """Create table to track applied migrations."""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    id SERIAL PRIMARY KEY,
                    filename VARCHAR(255) UNIQUE NOT NULL,
                    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """)
            logger.info("schema_migrations_table_ready")

    async def get_applied_migrations(self) -> set[str]:
        """Get list of already applied migrations."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("SELECT filename FROM schema_migrations")
            return {row["filename"] for row in rows}

    async def run_migrations(self) -> None:
        """Run all pending migrations."""
        if not self.migrations_dir.exists():
            logger.warning("migrations_directory_not_found", extra={"path": str(self.migrations_dir)})
            return

        applied = await self.get_applied_migrations()
        migration_files = sorted(self.migrations_dir.glob("*.sql"))

        pending = [f for f in migration_files if f.name not in applied]

        if not pending:
            logger.info("no_pending_migrations", extra={"total_applied": len(applied)})
            return

        logger.info(
            "running_migrations",
            extra={"pending_count": len(pending), "applied_count": len(applied)}
        )

        for migration_file in pending:
            await self._run_migration(migration_file)

    async def _run_migration(self, migration_file: Path) -> None:
        """Run a single migration file."""
        logger.info("applying_migration", extra={"file_name": migration_file.name})

        try:
            sql = migration_file.read_text()

            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    # Run the migration SQL
                    await conn.execute(sql)

                    # Record that we applied it
                    await conn.execute(
                        "INSERT INTO schema_migrations (filename) VALUES ($1)",
                        migration_file.name
                    )

            logger.info("migration_applied", extra={"file_name": migration_file.name})

        except Exception as exc:
            logger.exception(
                "migration_failed",
                extra={"file_name": migration_file.name, "error": str(exc)}
            )
            raise


async def run_migrations(pool: asyncpg.Pool) -> None:
    """Run all pending database migrations."""
    manager = MigrationManager(pool)
    await manager.initialize()

