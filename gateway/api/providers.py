from __future__ import annotations

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from ..core.providers import ProvidersService, get_providers_service
from ..models.providers import EmbeddingProvider, EmbeddingProviderCreate

router = APIRouter(prefix="/providers/embeddings", tags=["embedding-providers"])


def get_service() -> ProvidersService:
    return get_providers_service()


@router.get("", response_model=List[EmbeddingProvider])
async def list_embedding_providers(service: ProvidersService = Depends(get_service)) -> List[EmbeddingProvider]:
    providers = await service.list_embedding_providers()
    return providers


@router.post("", status_code=status.HTTP_201_CREATED, response_model=EmbeddingProvider)
async def create_embedding_provider(
    payload: EmbeddingProviderCreate,
    service: ProvidersService = Depends(get_service),
) -> EmbeddingProvider:
    try:
        provider = await service.create_embedding_provider(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return provider


@router.delete("/{provider_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_embedding_provider(
    provider_id: UUID,
    service: ProvidersService = Depends(get_service),
):
    await service.delete_embedding_provider(provider_id)
