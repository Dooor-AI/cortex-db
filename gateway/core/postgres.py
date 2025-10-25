from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple
from uuid import UUID

import asyncpg

from ..models.schema import CollectionSchema, FieldDefinition, FieldType, StoreLocation
from ..utils.config import get_settings
from ..utils.logger import get_logger

logger = get_logger(__name__)


def sanitize_identifier(identifier: str) -> str:
    """Ensure identifier is safe for interpolation into SQL."""
    return identifier.lower()


@dataclass
class TableDefinition:
    create_sql: str
    index_statements: List[str]
    child_statements: List[str]


class PostgresClient:
    """Async wrapper around asyncpg with schema-aware helpers."""

    def __init__(self, dsn: str) -> None:
        self.dsn = dsn
        self._pool: Optional[asyncpg.Pool] = None

    async def connect(self) -> asyncpg.Pool:
        if self._pool is None:
            logger.info("initializing_postgres_pool", extra={"dsn": self.dsn})
            self._pool = await asyncpg.create_pool(self.dsn, min_size=1, max_size=10)
            await self._ensure_bootstrap()
        return self._pool

    async def close(self) -> None:
        if self._pool:
            await self._pool.close()
            self._pool = None

    async def _ensure_bootstrap(self) -> None:
        pool = await self.connect()
        async with pool.acquire() as conn:
            await conn.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
            # Control table for databases (stored in default 'cortex' database)
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS _cortex_databases (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                """
            )
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS _cortex_collections (
                    name TEXT PRIMARY KEY,
                    database_name TEXT,
                    schema JSONB NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    embedding_model TEXT,
                    embedding_provider_id UUID,
                    chunk_size INTEGER,
                    chunk_overlap INTEGER
                );
                """
            )
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS _cortex_embedding_providers (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    name TEXT NOT NULL UNIQUE,
                    provider TEXT NOT NULL,
                    api_key TEXT NOT NULL,
                    embedding_model TEXT NOT NULL,
                    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
                    enabled BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                """
            )
            await conn.execute(
                "ALTER TABLE _cortex_collections ADD COLUMN IF NOT EXISTS embedding_provider_id UUID;"
            )
            await conn.execute(
                "ALTER TABLE _cortex_collections ADD COLUMN IF NOT EXISTS database_name TEXT;"
            )

    async def create_table_from_schema(self, schema: CollectionSchema) -> None:
        table_def = self._build_table_definition(schema)
        pool = await self.connect()
        async with pool.acquire() as conn, conn.transaction():
            await conn.execute(table_def.create_sql)
            for statement in table_def.child_statements:
                await conn.execute(statement)
            for statement in table_def.index_statements:
                await conn.execute(statement)
            provider_uuid: Optional[UUID] = None
            if schema.config.embedding_provider_id:
                try:
                    provider_uuid = UUID(schema.config.embedding_provider_id)
                except ValueError as exc:
                    raise ValueError("Invalid embedding_provider_id") from exc
            await conn.execute(
                """
                INSERT INTO _cortex_collections (name, database_name, schema, embedding_model, embedding_provider_id, chunk_size, chunk_overlap)
                VALUES ($1, $2, $3::jsonb, $4, $5, $6, $7)
                ON CONFLICT (name) DO UPDATE
                SET database_name = EXCLUDED.database_name,
                    schema = EXCLUDED.schema,
                    embedding_model = EXCLUDED.embedding_model,
                    embedding_provider_id = EXCLUDED.embedding_provider_id,
                    chunk_size = EXCLUDED.chunk_size,
                    chunk_overlap = EXCLUDED.chunk_overlap,
                    updated_at = NOW();
                """,
                schema.name,
                schema.database,
                schema.model_dump_json(),
                schema.config.embedding_model,
                provider_uuid,
                schema.config.chunk_size,
                schema.config.chunk_overlap,
            )

    async def create_embedding_provider(
        self,
        name: str,
        provider: str,
        api_key: str,
        embedding_model: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        pool = await self.connect()
        metadata_value = json.dumps(metadata or {})
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO _cortex_embedding_providers (name, provider, api_key, embedding_model, metadata)
                VALUES ($1, $2, $3, $4, $5::jsonb)
                RETURNING id, name, provider, embedding_model, metadata, enabled, created_at, updated_at;
                """,
                name,
                provider,
                api_key,
                embedding_model,
                metadata_value,
            )
        row_dict = dict(row)
        # Parse metadata JSON string to dict if needed
        if isinstance(row_dict.get("metadata"), str):
            row_dict["metadata"] = json.loads(row_dict["metadata"])
        return row_dict

    async def list_embedding_providers(self) -> List[Dict[str, Any]]:
        pool = await self.connect()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, name, provider, embedding_model, metadata, enabled, created_at, updated_at
                FROM _cortex_embedding_providers
                ORDER BY name ASC;
                """
            )
        result = []
        for row in rows:
            row_dict = dict(row)
            # Parse metadata JSON string to dict if needed
            if isinstance(row_dict.get("metadata"), str):
                row_dict["metadata"] = json.loads(row_dict["metadata"])
            result.append(row_dict)
        return result

    async def get_embedding_provider(
        self,
        provider_id: UUID,
        include_secret: bool = False,
    ) -> Optional[Dict[str, Any]]:
        pool = await self.connect()
        columns = (
            "id, name, provider, embedding_model, metadata, enabled, created_at, updated_at"
        )
        if include_secret:
            columns += ", api_key"
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                f"""
                SELECT {columns}
                FROM _cortex_embedding_providers
                WHERE id = $1;
                """,
                provider_id,
            )
        if not row:
            return None
        row_dict = dict(row)
        # Parse metadata JSON string to dict if needed
        if isinstance(row_dict.get("metadata"), str):
            row_dict["metadata"] = json.loads(row_dict["metadata"])
        return row_dict

    async def delete_embedding_provider(self, provider_id: UUID) -> None:
        pool = await self.connect()
        async with pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM _cortex_embedding_providers WHERE id = $1;",
                provider_id,
            )

    def _build_table_definition(self, schema: CollectionSchema) -> TableDefinition:
        table_name = sanitize_identifier(schema.name)
        column_defs: List[str] = [
            "id UUID PRIMARY KEY DEFAULT uuid_generate_v4()",
            "created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()",
            "updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()",
        ]
        index_statements: List[str] = []
        child_statements: List[str] = []

        for field in schema.fields:
            if field.type == FieldType.ARRAY:
                child_statements.extend(self._build_array_table(schema, field))
                continue

            if StoreLocation.POSTGRES not in field.store_in:
                continue

            column_defs.append(self._column_definition(field))

            if field.indexed:
                index_statements.append(
                    f'CREATE INDEX IF NOT EXISTS idx_{table_name}_{field.name.lower()} ON "{table_name}" ("{field.name}");'
                )

        create_sql = f'CREATE TABLE IF NOT EXISTS "{table_name}" (\n  ' + ",\n  ".join(column_defs) + "\n);"
        return TableDefinition(create_sql=create_sql, index_statements=index_statements, child_statements=child_statements)

    def _column_definition(self, field: FieldDefinition) -> str:
        sql_type = self._map_field_type(field)
        parts = [f'"{field.name}" {sql_type}']
        if field.required:
            parts.append("NOT NULL")
        if field.unique:
            parts.append("UNIQUE")
        if field.type == FieldType.ENUM and field.values:
            allowed = ", ".join(f"'{value}'" for value in field.values)
            parts.append(f"CHECK (\"{field.name}\" IN ({allowed}))")
        return " ".join(parts)

    def _build_array_table(self, schema: CollectionSchema, field: FieldDefinition) -> List[str]:
        table_name = sanitize_identifier(schema.name)
        child_table = f"{table_name}_{field.name.lower()}"
        columns = [
            "item_id UUID PRIMARY KEY DEFAULT uuid_generate_v4()",
            f'parent_id UUID NOT NULL REFERENCES "{table_name}"(id) ON DELETE CASCADE',
            "item_index INTEGER NOT NULL",
        ]

        assert field.schema is not None
        for nested in field.schema:
            if nested.type == FieldType.ARRAY:
                raise ValueError("Nested arrays are not supported")
            if StoreLocation.POSTGRES in nested.store_in:
                columns.append(self._column_definition(nested))

        create_sql = f'CREATE TABLE IF NOT EXISTS "{child_table}" (\n  ' + ",\n  ".join(columns) + "\n);"
        index_sql = f'CREATE INDEX IF NOT EXISTS idx_{child_table}_parent ON "{child_table}" (parent_id);'
        return [create_sql, index_sql]

    def _map_field_type(self, field: FieldDefinition) -> str:
        mapping = {
            FieldType.STRING: "TEXT",
            FieldType.TEXT: "TEXT",
            FieldType.INT: "INTEGER",
            FieldType.FLOAT: "DOUBLE PRECISION",
            FieldType.BOOLEAN: "BOOLEAN",
            FieldType.DATE: "DATE",
            FieldType.DATETIME: "TIMESTAMPTZ",
            FieldType.ENUM: "TEXT",
            FieldType.FILE: "TEXT",
            FieldType.JSON: "JSONB",
        }
        sql_type = mapping.get(field.type)
        if not sql_type:
            raise ValueError(f"Unsupported field type {field.type}")
        return sql_type

    async def drop_collection(self, collection_name: str) -> None:
        table_name = sanitize_identifier(collection_name)
        pool = await self.connect()
        async with pool.acquire() as conn, conn.transaction():
            # Drop child tables first
            child_tables = await conn.fetch(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_name LIKE $1 || '\_%';
                """,
                table_name,
            )
            for record in child_tables:
                await conn.execute(f'DROP TABLE IF EXISTS "{record["table_name"]}" CASCADE;')
            await conn.execute(f'DROP TABLE IF EXISTS "{table_name}" CASCADE;')
            await conn.execute("DELETE FROM _cortex_collections WHERE name = $1;", collection_name)

    async def insert_record(
        self,
        schema: CollectionSchema,
        data: Dict[str, Any],
        child_data: Dict[str, List[Dict[str, Any]]],
    ) -> Any:
        table_name = sanitize_identifier(schema.name)
        pool = await self.connect()
        async with pool.acquire() as conn, conn.transaction():
            columns = []
            values = []
            placeholders = []

            for i, (key, value) in enumerate(data.items(), start=1):
                columns.append(f'"{key}"')
                placeholders.append(f"${i}")
                values.append(value)

            insert_sql = (
                f'INSERT INTO "{table_name}" ({", ".join(columns)}) '
                f'VALUES ({", ".join(placeholders)}) RETURNING id;'
            )
            record_id = await conn.fetchval(insert_sql, *values)

            for field_name, items in child_data.items():
                child_table = f'{table_name}_{field_name.lower()}'
                for idx, item in enumerate(items):
                    child_columns = ['parent_id', 'item_index']
                    child_placeholders = ['$1', '$2']
                    child_values = [record_id, idx]
                    placeholder_index = 3
                    for key, value in item.items():
                        child_columns.append(f'"{key}"')
                        child_placeholders.append(f"${placeholder_index}")
                        child_values.append(value)
                        placeholder_index += 1
                    insert_child_sql = (
                        f'INSERT INTO "{child_table}" ({", ".join(child_columns)}) '
                        f'VALUES ({", ".join(child_placeholders)});'
                    )
                    await conn.execute(insert_child_sql, *child_values)

            return record_id

    async def fetch_record(self, collection: str, record_id: Any) -> Optional[dict[str, Any]]:
        table_name = sanitize_identifier(collection)
        pool = await self.connect()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(f'SELECT * FROM "{table_name}" WHERE id = $1;', record_id)
            if not row:
                return None
            return dict(row)

    async def fetch_child_items(self, collection: str, field: str, record_id: Any) -> List[dict[str, Any]]:
        table_name = sanitize_identifier(collection)
        child_table = f"{table_name}_{field}"
        pool = await self.connect()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                f'SELECT * FROM "{child_table}" WHERE parent_id = $1 ORDER BY item_index ASC;', record_id
            )
        return [dict(row) for row in rows]

    async def delete_record(self, collection: str, record_id: Any) -> None:
        table_name = sanitize_identifier(collection)
        pool = await self.connect()
        async with pool.acquire() as conn:
            await conn.execute(f'DELETE FROM "{table_name}" WHERE id = $1;', record_id)

    async def delete_array_items(self, collection: str, field: str, record_id: Any) -> None:
        table_name = sanitize_identifier(collection)
        child_table = f"{table_name}_{field.lower()}"
        pool = await self.connect()
        async with pool.acquire() as conn:
            await conn.execute(f'DELETE FROM "{child_table}" WHERE parent_id = $1;', record_id)

    async def insert_array_items(
        self,
        collection: str,
        field: str,
        record_id: Any,
        items: List[Dict[str, Any]],
    ) -> None:
        if not items:
            return
        table_name = sanitize_identifier(collection)
        child_table = f"{table_name}_{field.lower()}"
        pool = await self.connect()
        async with pool.acquire() as conn:
            for idx, item in enumerate(items):
                columns = ['parent_id', 'item_index']
                placeholders = ['$1', '$2']
                values = [record_id, idx]
                placeholder_index = 3
                for key, value in item.items():
                    columns.append(f'"{key}"')
                    placeholders.append(f"${placeholder_index}")
                    values.append(value)
                    placeholder_index += 1
                insert_sql = (
                    f'INSERT INTO "{child_table}" ({", ".join(columns)}) '
                    f'VALUES ({", ".join(placeholders)});'
                )
                await conn.execute(insert_sql, *values)

    async def fetch_records_by_ids(self, collection: str, record_ids: List[Any]) -> List[dict[str, Any]]:
        if not record_ids:
            return []
        table_name = sanitize_identifier(collection)
        pool = await self.connect()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                f'SELECT * FROM "{table_name}" WHERE id = ANY($1::uuid[])',
                [UUID(str(rid)) for rid in record_ids],
            )
        return [dict(row) for row in rows]

    async def update_record(self, collection: str, record_id: Any, data: Dict[str, Any]) -> None:
        if not data:
            return
        table_name = sanitize_identifier(collection)
        pool = await self.connect()
        async with pool.acquire() as conn:
            assignments = []
            values = []
            for idx, (key, value) in enumerate(data.items(), start=1):
                assignments.append(f'"{key}" = ${idx}')
                values.append(value)
            assignments.append(f'updated_at = NOW()')
            sql = f'UPDATE "{table_name}" SET ' + ", ".join(assignments) + f" WHERE id = ${len(values) + 1};"
            values.append(record_id)
            await conn.execute(sql, *values)

    async def query_records(
        self,
        collection: str,
        filters: Dict[str, Any],
        limit: int = 100,
        offset: int = 0,
    ) -> List[dict[str, Any]]:
        table_name = sanitize_identifier(collection)
        pool = await self.connect()
        clauses: List[str] = []
        values: List[Any] = []
        param_index = 1
        for key, value in filters.items():
            column = f'"{key}"'
            if isinstance(value, dict):
                for op, val in value.items():
                    match op:
                        case "$gte":
                            clauses.append(f"{column} >= ${param_index}")
                        case "$lte":
                            clauses.append(f"{column} <= ${param_index}")
                        case "$gt":
                            clauses.append(f"{column} > ${param_index}")
                        case "$lt":
                            clauses.append(f"{column} < ${param_index}")
                        case "$ne":
                            clauses.append(f"{column} <> ${param_index}")
                        case _:
                            continue
                    values.append(val)
                    param_index += 1
            else:
                clauses.append(f"{column} = ${param_index}")
                values.append(value)
                param_index += 1

        where_clause = " AND ".join(clauses) if clauses else "TRUE"
        sql = (
            f'SELECT * FROM "{table_name}" WHERE {where_clause} ORDER BY created_at DESC LIMIT {limit} OFFSET {offset};'
        )
        async with pool.acquire() as conn:
            rows = await conn.fetch(sql, *values)
        return [dict(row) for row in rows]

    async def get_collection_schema(self, name: str) -> Optional[CollectionSchema]:
        pool = await self.connect()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT schema FROM _cortex_collections WHERE name = $1;",
                name,
            )
        if not row:
            return None
        data = row["schema"]
        # Parse JSON string to dict if needed
        if isinstance(data, str):
            data = json.loads(data)
        return CollectionSchema.model_validate(data)

    async def list_collections(self) -> List[dict[str, Any]]:
        pool = await self.connect()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT name, database_name, schema, created_at, updated_at FROM _cortex_collections ORDER BY name ASC;"
            )
        result = []
        for row in rows:
            row_dict = dict(row)
            # Parse schema JSON string to dict if needed
            if isinstance(row_dict.get("schema"), str):
                row_dict["schema"] = json.loads(row_dict["schema"])
            result.append(row_dict)
        return result

    async def healthcheck(self) -> bool:
        try:
            pool = await self.connect()
            async with pool.acquire() as conn:
                await conn.execute("SELECT 1;")
            return True
        except Exception:
            return False

    # Database management methods
    async def create_database(
        self,
        name: str,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        # First, register in control table
        pool = await self.connect()
        metadata_value = json.dumps(metadata or {})
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO _cortex_databases (name, description, metadata)
                VALUES ($1, $2, $3::jsonb)
                RETURNING id, name, description, metadata, created_at, updated_at;
                """,
                name,
                description,
                metadata_value,
            )

        # Then create the actual Postgres database
        # Need to use a connection to 'postgres' database (admin)
        admin_dsn = self.dsn.rsplit("/", 1)[0] + "/postgres"
        admin_conn = await asyncpg.connect(admin_dsn)
        try:
            await admin_conn.execute(f'CREATE DATABASE "{name}";')
        finally:
            await admin_conn.close()

        # Initialize the new database with control tables
        db_dsn = self.dsn.rsplit("/", 1)[0] + f"/{name}"
        db_conn = await asyncpg.connect(db_dsn)
        try:
            await db_conn.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
            await db_conn.execute(
                """
                CREATE TABLE IF NOT EXISTS _cortex_collections (
                    name TEXT PRIMARY KEY,
                    schema JSONB NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    embedding_model TEXT,
                    embedding_provider_id UUID,
                    chunk_size INTEGER,
                    chunk_overlap INTEGER
                );
                """
            )
        finally:
            await db_conn.close()

        row_dict = dict(row)
        if isinstance(row_dict.get("metadata"), str):
            row_dict["metadata"] = json.loads(row_dict["metadata"])
        return row_dict

    async def list_databases(self) -> List[Dict[str, Any]]:
        pool = await self.connect()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, name, description, metadata, created_at, updated_at
                FROM _cortex_databases
                ORDER BY name ASC;
                """
            )
        result = []
        for row in rows:
            row_dict = dict(row)
            if isinstance(row_dict.get("metadata"), str):
                row_dict["metadata"] = json.loads(row_dict["metadata"])
            result.append(row_dict)
        return result

    async def get_database(self, name: str) -> Optional[Dict[str, Any]]:
        pool = await self.connect()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, name, description, metadata, created_at, updated_at
                FROM _cortex_databases
                WHERE name = $1;
                """,
                name,
            )
        if not row:
            return None
        row_dict = dict(row)
        if isinstance(row_dict.get("metadata"), str):
            row_dict["metadata"] = json.loads(row_dict["metadata"])
        return row_dict

    async def delete_database(self, name: str) -> None:
        # First remove from control table
        pool = await self.connect()
        async with pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM _cortex_databases WHERE name = $1;",
                name,
            )

        # Then drop the actual Postgres database
        admin_dsn = self.dsn.rsplit("/", 1)[0] + "/postgres"
        admin_conn = await asyncpg.connect(admin_dsn)
        try:
            # Terminate all connections to the database first
            await admin_conn.execute(
                f"""
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = '{name}'
                  AND pid <> pg_backend_pid();
                """
            )
            await admin_conn.execute(f'DROP DATABASE IF EXISTS "{name}";')
        finally:
            await admin_conn.close()


_client: Optional[PostgresClient] = None


def get_postgres_client() -> PostgresClient:
    global _client
    if _client is None:
        settings = get_settings()
        _client = PostgresClient(settings.database_url)
    return _client
