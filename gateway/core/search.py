from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from ..models.schema import CollectionSchema, StoreLocation
from .collections import collection_requires_vectors
from ..utils.config import get_settings
from ..utils.logger import get_logger
from .collections import CollectionService, default_bucket_name, get_collection_service
from .embeddings import get_embedding_service
from .minio import get_minio_service
from .postgres import get_postgres_client
from .qdrant import get_qdrant_service

logger = get_logger(__name__)


class SearchService:
    def __init__(self) -> None:
        self._collections: CollectionService = get_collection_service()
        self._qdrant = get_qdrant_service()
        self._postgres = get_postgres_client()
        self._minio = get_minio_service()
        self._settings = get_settings()

    async def hybrid_search(
        self,
        collection: str,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10,
    ) -> Dict[str, Any]:
        schema = await self._collections.get_collection_schema(collection)
        if not schema:
            raise ValueError(f"Collection {collection} not found")

        if not collection_requires_vectors(schema):
            raise ValueError("Collection does not have vector search enabled")

        embedding_service = await get_embedding_service(schema.config.embedding_provider_id)

        started = time.perf_counter()
        query_vector = await embedding_service.embed_text(query)
        qdrant_results = await self._qdrant.search(collection, query_vector, filters, limit=limit * 5)

        aggregated: Dict[str, Dict[str, Any]] = {}
        for point in qdrant_results:
            payload = point.payload or {}
            record_id = payload.get("record_id")
            if not record_id:
                continue
            entry = aggregated.setdefault(
                record_id,
                {
                    "score": point.score,
                    "highlights": [],
                },
            )
            entry["score"] = max(entry["score"], point.score)
            entry["highlights"].append(
                {
                    "field": payload.get("field"),
                    "text": payload.get("text"),
                    "chunk_index": payload.get("chunk_index"),
                    "score": point.score,
                }
            )

        ordered = sorted(aggregated.items(), key=lambda item: item[1]["score"], reverse=True)
        record_ids = [record_id for record_id, _ in ordered[:limit]]
        records = await self._postgres.fetch_records_by_ids(collection, record_ids)
        record_map = {str(record["id"]): record for record in records}

        results: List[Dict[str, Any]] = []
        for record_id in record_ids:
            record = record_map.get(record_id)
            if not record:
                continue
            entry = aggregated[record_id]
            files_payload = await self._generate_file_urls(schema.name, record, schema)
            results.append(
                {
                    "id": record_id,
                    "score": entry["score"],
                    "record": self._serialize_record(record),
                    "files": files_payload,
                    "highlights": entry["highlights"],
                }
            )

        took_ms = (time.perf_counter() - started) * 1000

        return {
            "results": results,
            "total": len(results),
            "took_ms": round(took_ms, 2),
        }

    async def _generate_file_urls(self, collection: str, record: Dict[str, Any], schema: "CollectionSchema") -> Dict[str, str]:
        bucket = default_bucket_name(collection)
        urls: Dict[str, str] = {}
        for field in schema.fields:
            if field.type == field.type.FILE and StoreLocation.MINIO in field.store_in:
                object_path = record.get(field.name)
                if object_path:
                    urls[field.name] = await self._minio.generate_presigned_url(bucket, object_path)
        return urls

    def _serialize_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        serialized: Dict[str, Any] = {}
        for key, value in record.items():
            if key in {"created_at", "updated_at"} and value is not None:
                serialized[key] = value.isoformat()
            else:
                serialized[key] = value
        return serialized


_search_service: Optional[SearchService] = None


def get_search_service() -> SearchService:
    global _search_service
    if _search_service is None:
        _search_service = SearchService()
    return _search_service
