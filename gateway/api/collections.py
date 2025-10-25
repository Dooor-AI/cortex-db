from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status

from ..core.collections import CollectionService, CollectionCreationResult, get_collection_service
from ..core.schema import SchemaParseError, parse_schema

router = APIRouter(prefix="/collections", tags=["collections"])


def get_service() -> CollectionService:
    return get_collection_service()


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_collection(request: Request, service: CollectionService = Depends(get_service)):
    body = await request.body()
    try:
        schema = parse_schema(body.decode("utf-8"))
    except SchemaParseError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    result: CollectionCreationResult = await service.create_collection(schema)
    return {
        "status": "created",
        "collection": schema.name,
        "postgres_table": result.postgres_table,
        "qdrant_collection": result.qdrant_collection,
        "minio_bucket": result.minio_bucket,
    }


@router.get("")
async def list_collections(service: CollectionService = Depends(get_service)):
    rows = await service.list_collections()
    return [
        {
            "name": row["name"],
            "schema": row["schema"],
            "created_at": row["created_at"].isoformat() if row.get("created_at") else None,
            "updated_at": row["updated_at"].isoformat() if row.get("updated_at") else None,
        }
        for row in rows
    ]


@router.get("/{name}")
async def get_collection(name: str, service: CollectionService = Depends(get_service)):
    schema = await service.get_collection_schema(name)
    if not schema:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found")
    return schema.model_dump()


@router.delete("/{name}")
async def delete_collection(name: str, service: CollectionService = Depends(get_service)):
    schema = await service.get_collection_schema(name)
    if not schema:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found")
    await service.delete_collection(name)
    return {"status": "deleted"}
