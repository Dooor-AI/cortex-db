from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from ..core.databases import DatabaseService, get_database_service
from ..models.database import Database, DatabaseCreate

router = APIRouter(prefix="/databases", tags=["databases"])


def get_service() -> DatabaseService:
    return get_database_service()


@router.get("", response_model=List[Database])
async def list_databases(service: DatabaseService = Depends(get_service)) -> List[Database]:
    """List all databases in the CortexDB instance."""
    databases = await service.list_databases()
    return databases


@router.post("", status_code=status.HTTP_201_CREATED, response_model=Database)
async def create_database(
    payload: DatabaseCreate,
    service: DatabaseService = Depends(get_service),
) -> Database:
    """
    Create a new database.

    This creates a physical Postgres database and registers it in CortexDB.
    """
    try:
        database = await service.create_database(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return database


@router.get("/{name}", response_model=Database)
async def get_database(
    name: str,
    service: DatabaseService = Depends(get_service),
) -> Database:
    """Get details about a specific database."""
    database = await service.get_database(name)
    if not database:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Database '{name}' not found",
        )
    return database


@router.delete("/{name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_database(
    name: str,
    service: DatabaseService = Depends(get_service),
):
    """
    Delete a database and all its collections.

    WARNING: This will permanently delete all data in the database.
    """
    try:
        await service.delete_database(name)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
