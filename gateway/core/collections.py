from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..models.schema import CollectionSchema, FieldDefinition, StoreLocation
from ..utils.logger import get_logger
from .embeddings import get_embedding_service
from .minio import get_minio_service
from .postgres import PostgresClient, get_postgres_client
from .qdrant import QdrantService, get_qdrant_service

logger = get_logger(__name__)


def collection_requires_vectors(schema: CollectionSchema) -> bool:
    return any(
        (field.vectorize or StoreLocation.QDRANT in field.store_in)
        for field in schema.fields
    )


def collection_requires_minio(schema: CollectionSchema) -> bool:
    return any(StoreLocation.MINIO in field.store_in for field in schema.fields)


def default_bucket_name(collection: str, database: Optional[str] = None) -> str:
    if database:
        return f"{database}-{collection}".lower()
    return f"cortex-{collection}".lower()


def get_qdrant_collection_name(collection: str, database: Optional[str] = None) -> str:
    if database:
        return f"{database}__{collection}"
    return collection


@dataclass
class CollectionCreationResult:
    postgres_table: str
    qdrant_collection: Optional[str]
    minio_bucket: Optional[str]


class CollectionService:
    def __init__(
        self,
        postgres: Optional[PostgresClient] = None,
        qdrant: Optional[QdrantService] = None,
        minio=None,
    ) -> None:
        self._postgres = postgres or get_postgres_client()
        self._qdrant = qdrant or get_qdrant_service()
        self._minio = minio or get_minio_service()

    async def create_collection(self, schema: CollectionSchema) -> CollectionCreationResult:
        await self._postgres.create_table_from_schema(schema)

        qdrant_collection = None
        if collection_requires_vectors(schema):
            embedding_service = await get_embedding_service(schema.config.embedding_provider_id)
            vector_size = await embedding_service.get_dimension()
            qdrant_name = get_qdrant_collection_name(schema.name, schema.database)
            await self._qdrant.create_collection_by_name(qdrant_name, vector_size)
            qdrant_collection = qdrant_name

        minio_bucket = None
        if collection_requires_minio(schema):
            bucket = default_bucket_name(schema.name, schema.database)
            await self._minio.ensure_bucket(bucket)
            minio_bucket = bucket

        return CollectionCreationResult(
            postgres_table=schema.name,
            qdrant_collection=qdrant_collection,
            minio_bucket=minio_bucket,
        )

    async def delete_collection(self, name: str) -> None:
        schema = await self._postgres.get_collection_schema(name)
        if not schema:
            return
        await self._postgres.drop_collection(name)
        if collection_requires_vectors(schema):
            qdrant_name = get_qdrant_collection_name(schema.name, schema.database)
            await self._qdrant.delete_collection(qdrant_name)
        if collection_requires_minio(schema):
            bucket = default_bucket_name(schema.name, schema.database)
            # MinIO does not support force delete with contents easily; skip automatic removal.
            logger.warning(
                "minio_bucket_not_deleted",
                extra={"bucket": bucket, "reason": "manual_cleanup_required"},
            )

    async def list_collections(self):
        return await self._postgres.list_collections()

    async def get_collection_schema(self, name: str) -> Optional[CollectionSchema]:
        return await self._postgres.get_collection_schema(name)


_collection_service: Optional[CollectionService] = None


def get_collection_service() -> CollectionService:
    global _collection_service
    if _collection_service is None:
        _collection_service = CollectionService()
    return _collection_service
