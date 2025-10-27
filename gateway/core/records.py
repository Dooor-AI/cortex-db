from __future__ import annotations

import io
import json
import uuid
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from fastapi import UploadFile

from ..models.schema import CollectionSchema, ExtractConfig, FieldDefinition, FieldType, StoreLocation
from ..utils.constants import DEFAULT_CHUNK_OVERLAP, DEFAULT_CHUNK_SIZE
from ..utils.logger import get_logger
from .chunking import chunk_text
from .collections import collection_requires_vectors, default_bucket_name, get_collection_service
from .embeddings import GeminiEmbeddingService, get_embedding_service
from .minio import get_minio_service
from .pdf_processor import get_pdf_processor
from .postgres import get_postgres_client
from .qdrant import QdrantPoint, get_qdrant_service

logger = get_logger(__name__)


@dataclass
class PreparedRecord:
    postgres_data: Dict[str, Any]
    array_data: Dict[str, List[Dict[str, Any]]]
    qdrant_points: List[QdrantPoint]
    file_paths: Dict[str, str]
    vectors_created: int


class RecordService:
    def __init__(self) -> None:
        self._postgres = get_postgres_client()
        self._qdrant = get_qdrant_service()
        self._minio = get_minio_service()
        self._collections = get_collection_service()
        self._pdf_processor = get_pdf_processor()

    async def create_record(
        self,
        collection_name: str,
        data: Dict[str, Any],
        files: Dict[str, UploadFile],
    ) -> Dict[str, Any]:
        schema = await self._collections.get_collection_schema(collection_name)
        if not schema:
            raise ValueError(f"Collection {collection_name} not found")

        embedding_service: Optional[GeminiEmbeddingService] = None
        vector_size = None
        if collection_requires_vectors(schema):
            embedding_service = await get_embedding_service(schema.config.embedding_provider_id)
            vector_size = await embedding_service.get_dimension()

        record_id = str(uuid.uuid4())
        prepared = await self._prepare_record(schema, record_id, data, files, embedding_service)
        postgres_data = {"id": record_id, **prepared.postgres_data}

        try:
            await self._postgres.insert_record(schema, postgres_data, prepared.array_data)
            if prepared.qdrant_points:
                # Ensure Qdrant collection exists before upserting points
                if vector_size is not None:
                    await self._qdrant.ensure_collection_exists(collection_name, vector_size)
                await self._qdrant.upsert_points(collection_name, prepared.qdrant_points)
        except Exception:
            # Rollback file uploads if Postgres/Qdrant fails
            for object_path in prepared.file_paths.values():
                bucket = default_bucket_name(collection_name)
                try:
                    await self._minio.remove_object(bucket, object_path)
                except Exception:  # pragma: no cover - best effort cleanup
                    logger.warning("minio_cleanup_failed", extra={"path": object_path})
            raise

        bucket = default_bucket_name(schema.name)
        files_payload: Dict[str, Any] = {}
        for field_name, object_path in prepared.file_paths.items():
            try:
                files_payload[field_name] = await self._minio.generate_presigned_url(bucket, object_path)
            except Exception:
                files_payload[field_name] = object_path

        return {
            "id": record_id,
            "vectors_created": prepared.vectors_created,
            "files": files_payload,
        }

    async def _prepare_record(
        self,
        schema: CollectionSchema,
        record_id: str,
        data: Dict[str, Any],
        files: Dict[str, UploadFile],
        embedding_service: Optional[GeminiEmbeddingService],
    ) -> PreparedRecord:
        postgres_data: Dict[str, Any] = {}
        array_data: Dict[str, List[Dict[str, Any]]] = {}
        qdrant_points: List[QdrantPoint] = []
        file_paths: Dict[str, str] = {}
        payload_base: Dict[str, Any] = {}
        vectors_created = 0

        chunk_size = schema.config.chunk_size or DEFAULT_CHUNK_SIZE
        chunk_overlap = schema.config.chunk_overlap or DEFAULT_CHUNK_OVERLAP

        payload_base.update(self._build_initial_payload_base(schema, data))

        for field in schema.fields:
            value = data.get(field.name)
            upload = files.get(field.name)

            if field.type == FieldType.FILE:
                if upload is None and field.required:
                    raise ValueError(f"File field {field.name} is required")
                if upload is not None:
                    object_path, text_fragments = await self._handle_file_field(
                        schema,
                        record_id,
                        field,
                        upload,
                        chunk_size,
                        chunk_overlap,
                    )
                    file_paths[field.name] = object_path
                    if StoreLocation.POSTGRES in field.store_in:
                        postgres_data[field.name] = object_path
                    if StoreLocation.QDRANT_PAYLOAD in field.store_in:
                        payload_base[field.name] = object_path

                    if text_fragments and (field.vectorize or StoreLocation.QDRANT in field.store_in):
                        if embedding_service is None:
                            raise ValueError("Embedding provider is not configured for vector fields")
                        vectors = await embedding_service.embed_texts(text_fragments)
                        for idx, vector in enumerate(vectors):
                            # Generate deterministic UUID from record_id, field name, and chunk index
                            point_id_str = f"{record_id}:{field.name}:{idx}"
                            point_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, point_id_str)

                            qdrant_points.append(
                                QdrantPoint(
                                    id=str(point_uuid),
                                    vector=vector,
                                    payload={
                                        "record_id": record_id,
                                        "collection": schema.name,
                                        "field": field.name,
                                        "chunk_index": idx,
                                        "text": text_fragments[idx],
                                        **payload_base,
                                    },
                                )
                            )
                        vectors_created += len(vectors)
                continue

            if value is None:
                if field.default is not None:
                    value = field.default
                elif field.required:
                    raise ValueError(f"Field {field.name} is required")
                else:
                    continue

            if field.type == FieldType.ARRAY:
                items = self._validate_array_field(field, value)
                array_data[field.name] = items
                continue

            converted = self._convert_value(field, value)

            if StoreLocation.POSTGRES in field.store_in:
                postgres_data[field.name] = converted

            if StoreLocation.QDRANT_PAYLOAD in field.store_in:
                payload_base[field.name] = self._serialize_for_payload(converted)

            if field.vectorize or StoreLocation.QDRANT in field.store_in:
                text_value = str(converted)
                fragments = chunk_text(text_value, chunk_size, chunk_overlap)
                if embedding_service is None:
                    raise ValueError("Embedding provider is not configured for vector fields")
                vectors = await embedding_service.embed_texts(fragments)
                for idx, vector in enumerate(vectors):
                    # Generate deterministic UUID from record_id, field name, and chunk index
                    point_id_str = f"{record_id}:{field.name}:{idx}"
                    point_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, point_id_str)
                    qdrant_points.append(
                        QdrantPoint(
                            id=str(point_uuid),
                            vector=vector,
                            payload={
                                "record_id": record_id,
                                "collection": schema.name,
                                "field": field.name,
                                "chunk_index": idx,
                                "text": fragments[idx],
                                **payload_base,
                            },
                        )
                    )
                vectors_created += len(vectors)

        return PreparedRecord(
            postgres_data=postgres_data,
            array_data=array_data,
            qdrant_points=qdrant_points,
            file_paths=file_paths,
            vectors_created=vectors_created,
        )

    async def get_record(self, collection: str, record_id: str) -> Optional[Dict[str, Any]]:
        schema = await self._collections.get_collection_schema(collection)
        if not schema:
            raise ValueError(f"Collection {collection} not found")

        row = await self._postgres.fetch_record(collection, record_id)
        if not row:
            return None

        for field in schema.fields:
            if field.type == FieldType.ARRAY:
                items = await self._postgres.fetch_child_items(collection, field.name, record_id)
                cleaned: List[Dict[str, Any]] = []
                for item in items:
                    cleaned.append(
                        {
                            key: value
                            for key, value in item.items()
                            if key not in {"item_id", "parent_id", "item_index"}
                        }
                    )
                row[field.name] = cleaned

        files = await self._generate_file_urls(schema, row)
        serialized = self._serialize_record(row)

        return {
            "id": str(row["id"]),
            "record": serialized,
            "files": files,
        }

    async def get_record_vectors(self, collection: str, record_id: str) -> List[Dict[str, Any]]:
        """Get all vector chunks for a record from Qdrant"""
        schema = await self._collections.get_collection_schema(collection)
        if not schema:
            raise ValueError(f"Collection {collection} not found")

        # Query Qdrant for all points with this record_id
        from qdrant_client.http import models as qmodels

        try:
            response = await self._qdrant._client.scroll(
                collection_name=collection,
                scroll_filter=qmodels.Filter(
                    must=[
                        qmodels.FieldCondition(
                            key="record_id",
                            match=qmodels.MatchValue(value=record_id),
                        )
                    ]
                ),
                limit=100,
                with_payload=True,
                with_vectors=False,
            )

            points = response[0]  # scroll returns (points, next_page_offset)

            # Sort by chunk_index and return
            vectors = []
            for point in points:
                vectors.append({
                    "id": point.id,
                    "field": point.payload.get("field"),
                    "chunk_index": point.payload.get("chunk_index"),
                    "text": point.payload.get("text"),
                })

            # Sort by chunk_index
            vectors.sort(key=lambda x: x.get("chunk_index", 0))
            return vectors
        except Exception:
            # Collection might not exist or no vectors
            return []

    async def delete_record(self, collection: str, record_id: str) -> None:
        schema = await self._collections.get_collection_schema(collection)
        if not schema:
            raise ValueError(f"Collection {collection} not found")

        row = await self._postgres.fetch_record(collection, record_id)
        if not row:
            raise ValueError("Record not found")

        for field in schema.fields:
            if field.type == FieldType.FILE and row.get(field.name):
                bucket = default_bucket_name(collection)
                try:
                    await self._minio.remove_object(bucket, row[field.name])
                except Exception:
                    logger.warning("minio_delete_failed", extra={"path": row[field.name]})

        await self._qdrant.delete_record(collection, record_id)
        await self._postgres.delete_record(collection, record_id)

    async def update_record(
        self,
        collection: str,
        record_id: str,
        data: Dict[str, Any],
        files: Dict[str, UploadFile],
    ) -> Dict[str, Any]:
        schema = await self._collections.get_collection_schema(collection)
        if not schema:
            raise ValueError(f"Collection {collection} not found")

        current = await self._postgres.fetch_record(collection, record_id)
        if not current:
            raise ValueError("Record not found")

        payload_base = {}
        for field in schema.fields:
            if StoreLocation.QDRANT_PAYLOAD in field.store_in:
                payload_base[field.name] = self._serialize_for_payload(current.get(field.name))

        embedding_service: Optional[GeminiEmbeddingService] = None
        if collection_requires_vectors(schema):
            embedding_service = await get_embedding_service(schema.config.embedding_provider_id)

        postgres_updates: Dict[str, Any] = {}
        qdrant_points: List[QdrantPoint] = []
        array_updates: Dict[str, List[Dict[str, Any]]] = {}
        new_file_paths: Dict[str, str] = {}
        vectors_created = 0

        chunk_size = schema.config.chunk_size or DEFAULT_CHUNK_SIZE
        chunk_overlap = schema.config.chunk_overlap or DEFAULT_CHUNK_OVERLAP

        for field in schema.fields:
            has_file_update = field.type == FieldType.FILE and field.name in files
            has_value_update = field.name in data

            if not has_file_update and not has_value_update:
                continue

            if field.type == FieldType.FILE and has_file_update:
                upload = files[field.name]
                old_path = current.get(field.name)
                object_path, text_fragments = await self._handle_file_field(
                    schema,
                    record_id,
                    field,
                    upload,
                    chunk_size,
                    chunk_overlap,
                )
                new_file_paths[field.name] = object_path
                postgres_updates[field.name] = object_path
                if StoreLocation.QDRANT_PAYLOAD in field.store_in:
                    payload_base[field.name] = object_path

                if old_path:
                    try:
                        await self._minio.remove_object(default_bucket_name(collection), old_path)
                    except Exception:
                        logger.warning("minio_delete_failed", extra={"path": old_path})

                await self._qdrant.delete_record_field(collection, record_id, field.name)
                if text_fragments and (field.vectorize or StoreLocation.QDRANT in field.store_in):
                    if embedding_service is None:
                        raise ValueError("Embedding provider is not configured for vector fields")
                    vectors = await embedding_service.embed_texts(text_fragments)
                    for idx, vector in enumerate(vectors):
                        # Generate deterministic UUID from record_id, field name, and chunk index
                        point_id_str = f"{record_id}:{field.name}:{idx}"
                        point_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, point_id_str)
                        qdrant_points.append(
                            QdrantPoint(
                                id=str(point_uuid),
                                vector=vector,
                                payload={
                                    "record_id": record_id,
                                    "collection": collection,
                                    "field": field.name,
                                    "chunk_index": idx,
                                    "text": text_fragments[idx],
                                    **payload_base,
                                },
                            )
                        )
                    vectors_created += len(vectors)
                continue

            if field.type == FieldType.ARRAY and has_value_update:
                items = self._validate_array_field(field, data[field.name])
                array_updates[field.name] = items
                continue

            if has_value_update:
                converted = self._convert_value(field, data[field.name])
                if StoreLocation.POSTGRES in field.store_in:
                    postgres_updates[field.name] = converted
                    payload_base[field.name] = self._serialize_for_payload(converted)
                if field.vectorize or StoreLocation.QDRANT in field.store_in:
                    fragments = chunk_text(str(converted), chunk_size, chunk_overlap)
                    await self._qdrant.delete_record_field(collection, record_id, field.name)
                    if embedding_service is None:
                        raise ValueError("Embedding provider is not configured for vector fields")
                    vectors = await embedding_service.embed_texts(fragments)
                    for idx, vector in enumerate(vectors):
                        # Generate deterministic UUID from record_id, field name, and chunk index
                        point_id_str = f"{record_id}:{field.name}:{idx}"
                        point_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, point_id_str)
                        qdrant_points.append(
                            QdrantPoint(
                                id=str(point_uuid),
                                vector=vector,
                                payload={
                                    "record_id": record_id,
                                    "collection": collection,
                                    "field": field.name,
                                    "chunk_index": idx,
                                    "text": fragments[idx],
                                    **payload_base,
                                },
                            )
                        )
                    vectors_created += len(vectors)

        if postgres_updates:
            await self._postgres.update_record(collection, record_id, postgres_updates)

        for field_name, items in array_updates.items():
            await self._postgres.delete_array_items(collection, field_name, record_id)
            await self._postgres.insert_array_items(collection, field_name, record_id, items)

        if qdrant_points:
            await self._qdrant.upsert_points(collection, qdrant_points)

        return {
            "id": record_id,
            "vectors_created": vectors_created,
            "updated_fields": list(postgres_updates.keys()) + list(array_updates.keys()) + list(new_file_paths.keys()),
        }

    async def _generate_file_urls(self, schema: CollectionSchema, row: Dict[str, Any]) -> Dict[str, str]:
        bucket = default_bucket_name(schema.name)
        urls: Dict[str, str] = {}
        for field in schema.fields:
            if field.type == FieldType.FILE and StoreLocation.MINIO in field.store_in:
                object_path = row.get(field.name)
                if object_path:
                    try:
                        urls[field.name] = await self._minio.generate_presigned_url(bucket, object_path)
                    except Exception:
                        logger.warning("minio_presign_failed", extra={"path": object_path})
        return urls

    def _serialize_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        serialized: Dict[str, Any] = {}
        for key, value in record.items():
            if isinstance(value, uuid.UUID):
                serialized[key] = str(value)
            elif isinstance(value, datetime):
                serialized[key] = value.isoformat()
            elif isinstance(value, date):
                serialized[key] = value.isoformat()
            else:
                serialized[key] = value
        return serialized

    def _build_initial_payload_base(self, schema: CollectionSchema, data: Dict[str, Any]) -> Dict[str, Any]:
        payload: Dict[str, Any] = {}
        for field in schema.fields:
            if StoreLocation.QDRANT_PAYLOAD not in field.store_in:
                continue
            if field.type in {FieldType.FILE, FieldType.ARRAY}:
                continue
            value = data.get(field.name, field.default)
            if value is None:
                continue
            try:
                converted = self._convert_value(field, value)
                payload[field.name] = self._serialize_for_payload(converted)
            except Exception:
                continue
        return payload

    async def _handle_file_field(
        self,
        schema: CollectionSchema,
        record_id: str,
        field: FieldDefinition,
        upload: UploadFile,
        chunk_size: int,
        chunk_overlap: int,
    ) -> tuple[str, List[str]]:
        content = await upload.read()
        buffer = io.BytesIO(content)
        buffer.seek(0)
        await upload.close()

        bucket = default_bucket_name(schema.name)
        object_path = f"{schema.name}/{record_id}/{upload.filename}"

        await self._minio.ensure_bucket(bucket)
        await self._minio.upload_stream(
            bucket,
            object_path,
            buffer,
            length=len(content),
            content_type=upload.content_type,
        )

        text_fragments: List[str] = []
        if field.vectorize:
            if upload.content_type == "application/pdf":
                extracted = await self._pdf_processor.extract_text(
                    content,
                    field.extract_config,
                )
                # Use field config if available, otherwise use defaults
                effective_chunk_size = chunk_size
                effective_chunk_overlap = chunk_overlap
                if field.extract_config:
                    if field.extract_config.chunk_size is not None:
                        effective_chunk_size = field.extract_config.chunk_size
                    if field.extract_config.chunk_overlap is not None:
                        effective_chunk_overlap = field.extract_config.chunk_overlap

                text_fragments = chunk_text(
                    extracted,
                    effective_chunk_size,
                    effective_chunk_overlap,
                ) if extracted else []
            elif upload.content_type and upload.content_type.startswith("image/"):
                from .vision import get_vision_service

                vision = get_vision_service()
                description = await vision.extract_text(content, upload.content_type)
                text_fragments = chunk_text(description, chunk_size, chunk_overlap) if description else []
            else:
                text_fragments = [f"File uploaded: {upload.filename}"]

        return object_path, text_fragments

    def _validate_array_field(self, field: FieldDefinition, value: Any) -> List[Dict[str, Any]]:
        if not isinstance(value, list):
            raise ValueError(f"Array field {field.name} expects a list")
        assert field.schema is not None

        items: List[Dict[str, Any]] = []
        for item in value:
            if not isinstance(item, dict):
                raise ValueError(f"Array field {field.name} expects list of objects")
            processed: Dict[str, Any] = {}
            for nested in field.schema:
                nested_value = item.get(nested.name)
                if nested_value is None:
                    if nested.required:
                        raise ValueError(f"Nested field {nested.name} is required in {field.name}")
                    continue
                processed[nested.name] = self._convert_value(nested, nested_value)
            items.append(processed)
        return items

    def _convert_value(self, field: FieldDefinition, value: Any) -> Any:
        if field.type in {FieldType.STRING, FieldType.TEXT, FieldType.FILE}:
            return str(value)
        if field.type == FieldType.ENUM:
            candidate = str(value)
            if field.values and candidate not in field.values:
                raise ValueError(f"Invalid enum value for field {field.name}")
            return candidate
        if field.type == FieldType.INT:
            return int(value)
        if field.type == FieldType.FLOAT:
            return float(value)
        if field.type == FieldType.BOOLEAN:
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                lowered = value.lower()
                if lowered in {"true", "1", "yes"}:
                    return True
                if lowered in {"false", "0", "no"}:
                    return False
            raise ValueError(f"Invalid boolean value for field {field.name}")
        if field.type == FieldType.DATE:
            if isinstance(value, date) and not isinstance(value, datetime):
                return value
            return datetime.fromisoformat(str(value)).date()
        if field.type == FieldType.DATETIME:
            if isinstance(value, datetime):
                return value
            return datetime.fromisoformat(str(value))
        if field.type == FieldType.JSON:
            if isinstance(value, (dict, list)):
                return value
            return json.loads(value)
        return value

    def _serialize_for_payload(self, value: Any) -> Any:
        if isinstance(value, (date, datetime)):
            return value.isoformat()
        return value


_record_service: Optional[RecordService] = None


def get_record_service() -> RecordService:
    global _record_service
    if _record_service is None:
        _record_service = RecordService()
    return _record_service
