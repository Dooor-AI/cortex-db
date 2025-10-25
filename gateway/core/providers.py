from __future__ import annotations

import json
from typing import Any, Dict, List, Optional
from uuid import UUID

import asyncpg

from ..models.providers import EmbeddingProvider, EmbeddingProviderCreate, EmbeddingProviderRecord
from ..utils.logger import get_logger
from .embeddings import clear_embedding_service_cache
from .postgres import get_postgres_client

logger = get_logger(__name__)


def _serialize_provider_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """Convert database record to format expected by Pydantic models."""
    result = dict(record)

    # Parse metadata JSON string to dict
    if "metadata" in result and isinstance(result["metadata"], str):
        result["metadata"] = json.loads(result["metadata"])

    # Convert datetime objects to ISO strings
    if "created_at" in result and result["created_at"]:
        result["created_at"] = result["created_at"].isoformat()
    if "updated_at" in result and result["updated_at"]:
        result["updated_at"] = result["updated_at"].isoformat()

    return result


class ProvidersService:
    def __init__(self) -> None:
        self._postgres = get_postgres_client()

    async def create_embedding_provider(self, payload: EmbeddingProviderCreate) -> EmbeddingProvider:
        try:
            record = await self._postgres.create_embedding_provider(
                name=payload.name,
                provider=payload.provider.value,
                api_key=payload.api_key,
                embedding_model=payload.embedding_model,
                metadata=payload.metadata or {},
            )
        except asyncpg.UniqueViolationError as exc:  # pragma: no cover - defensive
            logger.warning(
                "embedding_provider_conflict",
                extra={"provider_name": payload.name, "provider_type": payload.provider.value},
            )
            raise ValueError("An embedding provider with this name already exists") from exc

        serialized = _serialize_provider_record(record)
        serialized["has_api_key"] = True
        provider = EmbeddingProvider.model_validate(serialized)
        clear_embedding_service_cache(str(provider.id))
        return provider

    async def list_embedding_providers(self) -> List[EmbeddingProvider]:
        rows = await self._postgres.list_embedding_providers()
        providers = []
        for row in rows:
            serialized = _serialize_provider_record(row)
            serialized["has_api_key"] = True
            providers.append(EmbeddingProvider.model_validate(serialized))
        return providers

    async def get_embedding_provider(
        self,
        provider_id: UUID,
        include_secret: bool = False,
    ) -> Optional[EmbeddingProviderRecord]:
        row = await self._postgres.get_embedding_provider(provider_id, include_secret=include_secret)
        if not row:
            return None

        serialized = _serialize_provider_record(row)
        serialized["has_api_key"] = bool(row.get("api_key"))

        if include_secret and "api_key" in row:
            return EmbeddingProviderRecord.model_validate(serialized)
        return EmbeddingProviderRecord.model_validate(serialized | {"api_key": ""})

    async def delete_embedding_provider(self, provider_id: UUID) -> None:
        await self._postgres.delete_embedding_provider(provider_id)
        clear_embedding_service_cache(str(provider_id))


_service: Optional[ProvidersService] = None


def get_providers_service() -> ProvidersService:
    global _service
    if _service is None:
        _service = ProvidersService()
    return _service
