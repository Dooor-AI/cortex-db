from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..core.postgres import get_postgres_client
from ..core.search import SearchService, get_search_service
from ..models.record import QueryRequest, SearchRequest

router = APIRouter(prefix="/collections/{collection}", tags=["search"])


def get_service() -> SearchService:
    return get_search_service()


@router.post("/search")
async def hybrid_search(collection: str, request: SearchRequest, service: SearchService = Depends(get_service)):
    try:
        return await service.hybrid_search(collection, request.query, request.filters, request.limit)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/query")
async def query_records(collection: str, request: QueryRequest):
    postgres = get_postgres_client()
    results = await postgres.query_records(collection, request.filters, request.limit, request.offset)
    return {
        "results": results,
        "total": len(results),
    }
