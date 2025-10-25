from __future__ import annotations

from fastapi import APIRouter

from ..core.minio import get_minio_service
from ..core.postgres import get_postgres_client
from ..core.qdrant import get_qdrant_service


router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health_root():
    return {"status": "ok"}


@router.get("/postgres")
async def health_postgres():
    postgres = get_postgres_client()
    healthy = await postgres.healthcheck()
    return {"status": "ok" if healthy else "error"}


@router.get("/qdrant")
async def health_qdrant():
    qdrant = get_qdrant_service()
    healthy = await qdrant.healthcheck()
    return {"status": "ok" if healthy else "error"}


@router.get("/minio")
async def health_minio():
    minio = get_minio_service()
    healthy = await minio.healthcheck()
    return {"status": "ok" if healthy else "error"}


@router.get("/all")
async def health_all():
    postgres = get_postgres_client()
    qdrant = get_qdrant_service()
    minio = get_minio_service()

    pg = await postgres.healthcheck()
    qd = await qdrant.healthcheck()
    mn = await minio.healthcheck()

    status = pg and qd and mn
    return {
        "status": "ok" if status else "error",
        "details": {
            "postgres": pg,
            "qdrant": qd,
            "minio": mn,
        },
    }
