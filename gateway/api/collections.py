from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status

from ..core.collections import CollectionService, CollectionCreationResult, get_collection_service
from ..core.databases import get_database_service, DatabaseService
from ..core.schema import SchemaParseError, parse_schema

router = APIRouter(prefix="/collections", tags=["collections"])
# New router for database-scoped collections
database_collections_router = APIRouter(tags=["collections"])


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
            "database_name": row.get("database_name"),
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


# Database-scoped collection endpoints


@database_collections_router.post("/databases/{database}/collections", status_code=status.HTTP_201_CREATED)
async def create_database_collection(
    database: str,
    request: Request,
    service: CollectionService = Depends(get_service),
    db_service: DatabaseService = Depends(get_database_service),
):
    """Create a collection within a specific database."""
    # Verify database exists
    db = await db_service.get_database(database)
    if not db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Database '{database}' not found",
        )

    body = await request.body()
    try:
        schema = parse_schema(body.decode("utf-8"))
        # Set the database context
        schema.database = database
    except SchemaParseError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    result: CollectionCreationResult = await service.create_collection(schema)
    return {
        "status": "created",
        "database": database,
        "collection": schema.name,
        "postgres_table": result.postgres_table,
        "qdrant_collection": result.qdrant_collection,
        "minio_bucket": result.minio_bucket,
    }


@database_collections_router.get("/databases/{database}/collections")
async def list_database_collections(
    database: str,
    service: CollectionService = Depends(get_service),
    db_service: DatabaseService = Depends(get_database_service),
):
    """List all collections in a specific database."""
    # Verify database exists
    db = await db_service.get_database(database)
    if not db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Database '{database}' not found",
        )

    rows = await service.list_collections()
    # Filter by database
    filtered = [row for row in rows if row.get("database_name") == database]
    return [
        {
            "name": row["name"],
            "schema": row["schema"],
            "created_at": row["created_at"].isoformat() if row.get("created_at") else None,
            "updated_at": row["updated_at"].isoformat() if row.get("updated_at") else None,
        }
        for row in filtered
    ]


@database_collections_router.get("/databases/{database}/collections/{name}")
async def get_database_collection(
    database: str,
    name: str,
    service: CollectionService = Depends(get_service),
    db_service: DatabaseService = Depends(get_database_service),
):
    """Get details about a specific collection within a database."""
    # Verify database exists
    db = await db_service.get_database(database)
    if not db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Database '{database}' not found",
        )

    schema = await service.get_collection_schema(name)
    if not schema or schema.database != database:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found")
    return schema.model_dump()


@database_collections_router.delete("/databases/{database}/collections/{name}")
async def delete_database_collection(
    database: str,
    name: str,
    service: CollectionService = Depends(get_service),
    db_service: DatabaseService = Depends(get_database_service),
):
    """Delete a collection from a specific database."""
    # Verify database exists
    db = await db_service.get_database(database)
    if not db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Database '{database}' not found",
        )

    schema = await service.get_collection_schema(name)
    if not schema or schema.database != database:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found")
    await service.delete_collection(name)
    return {"status": "deleted"}
