from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as qmodels

from ..models.schema import CollectionSchema, FieldDefinition, FieldType, StoreLocation
from ..utils.config import get_settings
from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class QdrantPoint:
    """Payload for inserting vectors into Qdrant."""

    id: str
    vector: List[float]
    payload: Dict[str, Any]


class QdrantService:
    """Wrapper around Qdrant client with collection-aware helpers."""

    def __init__(self, url: str) -> None:
        self._client = AsyncQdrantClient(url)

    async def create_collection(self, schema: CollectionSchema, vector_size: int) -> None:
        collection_name = schema.name
        vectors_config = qmodels.VectorParams(size=vector_size, distance=qmodels.Distance.COSINE)

        payload_schema: Dict[str, qmodels.PayloadSchemaType] = {
            "record_id": qmodels.PayloadSchemaType.KEYWORD,
            "collection": qmodels.PayloadSchemaType.KEYWORD,
            "field": qmodels.PayloadSchemaType.KEYWORD,
            "chunk_index": qmodels.PayloadSchemaType.INTEGER,
        }

        for field in schema.fields:
            if StoreLocation.QDRANT_PAYLOAD in field.store_in or StoreLocation.QDRANT in field.store_in:
                payload_schema[field.name] = self._map_payload_type(field)

        try:
            await self._client.get_collection(collection_name)
            logger.info("qdrant_collection_exists", extra={"collection": collection_name})
        except Exception:
            await self._client.recreate_collection(
                collection_name=collection_name,
                vectors_config=vectors_config,
                on_disk_payload=True,
            )
            await self._client.update_collection(
                collection_name,
                optimizers_config=qmodels.OptimizersConfigDiff(indexing_threshold=20000),
            )
            logger.info("qdrant_collection_created", extra={"collection": collection_name})

            # Create payload indexes for base fields
            try:
                await self._client.create_payload_index(
                    collection_name=collection_name,
                    field_name="record_id",
                    field_schema=qmodels.PayloadSchemaType.KEYWORD,
                )
                await self._client.create_payload_index(
                    collection_name=collection_name,
                    field_name="collection",
                    field_schema=qmodels.PayloadSchemaType.KEYWORD,
                )
                await self._client.create_payload_index(
                    collection_name=collection_name,
                    field_name="field",
                    field_schema=qmodels.PayloadSchemaType.KEYWORD,
                )
                await self._client.create_payload_index(
                    collection_name=collection_name,
                    field_name="chunk_index",
                    field_schema=qmodels.PayloadSchemaType.INTEGER,
                )

                # Create indexes for schema-specific fields
                for field in schema.fields:
                    if StoreLocation.QDRANT_PAYLOAD in field.store_in or StoreLocation.QDRANT in field.store_in:
                        await self._client.create_payload_index(
                            collection_name=collection_name,
                            field_name=field.name,
                            field_schema=self._map_payload_type(field),
                        )
            except Exception as e:
                logger.warning("failed_to_create_payload_indexes", extra={"error": str(e)})

    async def create_collection_by_name(self, collection_name: str, vector_size: int) -> None:
        """Create a Qdrant collection by name (used for database-prefixed collections)."""
        vectors_config = qmodels.VectorParams(size=vector_size, distance=qmodels.Distance.COSINE)

        try:
            await self._client.get_collection(collection_name)
            logger.info("qdrant_collection_exists", extra={"collection": collection_name})
        except Exception:
            await self._client.recreate_collection(
                collection_name=collection_name,
                vectors_config=vectors_config,
                on_disk_payload=True,
            )
            await self._client.update_collection(
                collection_name,
                optimizers_config=qmodels.OptimizersConfigDiff(indexing_threshold=20000),
            )
            logger.info("qdrant_collection_created", extra={"collection": collection_name})

            # Create payload indexes for better filtering performance
            try:
                await self._client.create_payload_index(
                    collection_name=collection_name,
                    field_name="record_id",
                    field_schema=qmodels.PayloadSchemaType.KEYWORD,
                )
                await self._client.create_payload_index(
                    collection_name=collection_name,
                    field_name="collection",
                    field_schema=qmodels.PayloadSchemaType.KEYWORD,
                )
                await self._client.create_payload_index(
                    collection_name=collection_name,
                    field_name="field",
                    field_schema=qmodels.PayloadSchemaType.KEYWORD,
                )
                await self._client.create_payload_index(
                    collection_name=collection_name,
                    field_name="chunk_index",
                    field_schema=qmodels.PayloadSchemaType.INTEGER,
                )
            except Exception as e:
                logger.warning("failed_to_create_payload_indexes", extra={"error": str(e)})

    async def ensure_collection_exists(self, collection_name: str, vector_size: int) -> None:
        """Ensure a Qdrant collection exists, create it if it doesn't."""
        try:
            await self._client.get_collection(collection_name)
            logger.info("qdrant_collection_exists", extra={"collection": collection_name})
        except Exception:
            logger.info("creating_missing_qdrant_collection", extra={"collection": collection_name})
            await self.create_collection_by_name(collection_name, vector_size)

    async def upsert_points(self, collection: str, points: Iterable[QdrantPoint]) -> None:
        qdrant_points = [
            qmodels.PointStruct(id=point.id, vector=point.vector, payload=point.payload)
            for point in points
        ]
        if not qdrant_points:
            return
        await self._client.upsert(collection_name=collection, points=qdrant_points)

    async def delete_record(self, collection: str, record_id: str) -> None:
        await self._client.delete(
            collection_name=collection,
            points_selector=qmodels.FilterSelector(
                filter=qmodels.Filter(
                    must=[qmodels.FieldCondition(key="record_id", match=qmodels.MatchValue(value=record_id))]
                )
            ),
        )

    async def delete_record_field(self, collection: str, record_id: str, field: str) -> None:
        await self._client.delete(
            collection_name=collection,
            points_selector=qmodels.FilterSelector(
                filter=qmodels.Filter(
                    must=[
                        qmodels.FieldCondition(key="record_id", match=qmodels.MatchValue(value=record_id)),
                        qmodels.FieldCondition(key="field", match=qmodels.MatchValue(value=field)),
                    ]
                )
            ),
        )

    async def delete_collection(self, collection: str) -> None:
        await self._client.delete_collection(collection_name=collection)

    async def healthcheck(self) -> bool:
        try:
            await self._client.get_collections()
            return True
        except Exception as exc:
            logger.warning("qdrant_healthcheck_failed", extra={"error": str(exc)})
            return False

    async def search(
        self,
        collection: str,
        query_vector: List[float],
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10,
    ) -> List[qmodels.ScoredPoint]:
        filter_obj = self._build_filter(filters)
        results = await self._client.search(
            collection_name=collection,
            query_vector=query_vector,
            query_filter=filter_obj,
            limit=limit,
            with_payload=True,
        )
        return results

    def _build_filter(self, filters: Optional[Dict[str, Any]]) -> Optional[qmodels.Filter]:
        if not filters:
            return None

        conditions: List[qmodels.Condition] = []
        for key, value in filters.items():
            if isinstance(value, dict):
                # Range filters
                range_params = {}
                for op, val in value.items():
                    if op == "$gte":
                        range_params["gte"] = val
                    elif op == "$lte":
                        range_params["lte"] = val
                    elif op == "$gt":
                        range_params["gt"] = val
                    elif op == "$lt":
                        range_params["lt"] = val
                if range_params:
                    conditions.append(qmodels.FieldCondition(key=key, range=qmodels.Range(**range_params)))
            else:
                conditions.append(qmodels.FieldCondition(key=key, match=qmodels.MatchValue(value=value)))

        if not conditions:
            return None

        return qmodels.Filter(must=conditions)

    def _map_payload_type(self, field: FieldDefinition) -> qmodels.PayloadSchemaType:
        if field.type == FieldType.INT:
            return qmodels.PayloadSchemaType.INTEGER
        if field.type == FieldType.FLOAT:
            return qmodels.PayloadSchemaType.FLOAT
        if field.type == FieldType.BOOLEAN:
            return qmodels.PayloadSchemaType.BOOL
        return qmodels.PayloadSchemaType.KEYWORD


_service: Optional[QdrantService] = None


def get_qdrant_service() -> QdrantService:
    global _service
    if _service is None:
        settings = get_settings()
        _service = QdrantService(settings.qdrant_url)
    return _service
