from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Dict, Iterable, List, Optional
from uuid import UUID

import google.generativeai as genai

from ..models.providers import EmbeddingProviderType
from ..utils.config import get_settings
from ..utils.logger import get_logger

if TYPE_CHECKING:
    from .providers import ProvidersService

logger = get_logger(__name__)


class GeminiEmbeddingService:
    """Service wrapper for generating embeddings via Gemini."""

    def __init__(self, api_key: str, model: str) -> None:
        self._model_name = model
        self._api_key = api_key
        self._dimension: Optional[int] = None

    async def embed_text(self, text: str) -> List[float]:
        """Generate an embedding vector for a single piece of text."""
        try:
            genai.configure(api_key=self._api_key)
            result = await asyncio.to_thread(
                genai.embed_content,
                model=self._model_name,
                content=text,
            )
            vector = result["embedding"]
            if self._dimension is None:
                self._dimension = len(vector)
            return vector
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("gemini_embedding_failed", extra={"error": str(exc)})
            raise

    async def embed_texts(self, texts: Iterable[str]) -> List[List[float]]:
        embeddings: List[List[float]] = []
        for text in texts:
            embeddings.append(await self.embed_text(text))
        return embeddings

    async def get_dimension(self) -> int:
        if self._dimension is None:
            await self.embed_text("probe")
        assert self._dimension is not None
        return self._dimension


_embedding_services: Dict[str, GeminiEmbeddingService] = {}
_DEFAULT_PROVIDER_KEY = "__default__"


async def get_embedding_service(provider_id: Optional[str] = None) -> GeminiEmbeddingService:
    cache_key = provider_id or _DEFAULT_PROVIDER_KEY
    if cache_key in _embedding_services:
        return _embedding_services[cache_key]

    if provider_id:
        service = await _build_service_from_provider(provider_id)
    else:
        service = _build_default_service()

    _embedding_services[cache_key] = service
    return service


def _build_default_service() -> GeminiEmbeddingService:
    settings = get_settings()
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured")
    return GeminiEmbeddingService(
        api_key=settings.gemini_api_key,
        model=settings.gemini_embedding_model,
    )


async def _build_service_from_provider(provider_id: str) -> GeminiEmbeddingService:
    # Import here to avoid circular dependency
    from .providers import get_providers_service

    try:
        provider_uuid = UUID(provider_id)
    except ValueError as exc:
        raise ValueError("Invalid embedding provider id") from exc

    providers_service = get_providers_service()
    provider = await providers_service.get_embedding_provider(provider_uuid, include_secret=True)
    if provider is None or not provider.enabled:
        raise ValueError("Embedding provider not found or disabled")

    if provider.provider != EmbeddingProviderType.GEMINI:
        raise ValueError(f"Unsupported embedding provider type: {provider.provider}")

    if not provider.api_key:
        raise ValueError("Embedding provider is missing API key")

    return GeminiEmbeddingService(api_key=provider.api_key, model=provider.embedding_model)


def clear_embedding_service_cache(provider_id: Optional[str] = None) -> None:
    if provider_id:
        _embedding_services.pop(provider_id, None)
    else:
        _embedding_services.pop(_DEFAULT_PROVIDER_KEY, None)
