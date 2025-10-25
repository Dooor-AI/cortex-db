from __future__ import annotations

from typing import List, Optional

import asyncpg

from ..models.database import Database, DatabaseCreate
from ..utils.logger import get_logger
from .postgres import get_postgres_client

logger = get_logger(__name__)


class DatabaseService:
    def __init__(self) -> None:
        self._postgres = get_postgres_client()

    async def create_database(self, payload: DatabaseCreate) -> Database:
        try:
            record = await self._postgres.create_database(
                name=payload.name,
                description=payload.description,
                metadata=payload.metadata or {},
            )
        except asyncpg.UniqueViolationError as exc:
            logger.warning(
                "database_conflict",
                extra={"database_name": payload.name},
            )
            raise ValueError(f"A database with name '{payload.name}' already exists") from exc
        except asyncpg.DuplicateDatabaseError as exc:
            logger.warning(
                "postgres_database_exists",
                extra={"database_name": payload.name},
            )
            raise ValueError(f"Database '{payload.name}' already exists in Postgres") from exc

        # Serialize datetime to ISO string
        if record.get("created_at"):
            record["created_at"] = record["created_at"].isoformat()
        if record.get("updated_at"):
            record["updated_at"] = record["updated_at"].isoformat()

        return Database.model_validate(record)

    async def list_databases(self) -> List[Database]:
        rows = await self._postgres.list_databases()
        databases = []
        for row in rows:
            # Serialize datetime to ISO string
            if row.get("created_at"):
                row["created_at"] = row["created_at"].isoformat()
            if row.get("updated_at"):
                row["updated_at"] = row["updated_at"].isoformat()
            databases.append(Database.model_validate(row))
        return databases

    async def get_database(self, name: str) -> Optional[Database]:
        row = await self._postgres.get_database(name)
        if not row:
            return None

        # Serialize datetime to ISO string
        if row.get("created_at"):
            row["created_at"] = row["created_at"].isoformat()
        if row.get("updated_at"):
            row["updated_at"] = row["updated_at"].isoformat()

        return Database.model_validate(row)

    async def delete_database(self, name: str) -> None:
        # Verify database exists
        db = await self.get_database(name)
        if not db:
            raise ValueError(f"Database '{name}' not found")

        await self._postgres.delete_database(name)
        logger.info("database_deleted", extra={"database_name": name})


_service: Optional[DatabaseService] = None


def get_database_service() -> DatabaseService:
    global _service
    if _service is None:
        _service = DatabaseService()
    return _service
