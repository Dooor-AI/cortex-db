from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from gateway.api import collections, files, health, providers, records, search
from gateway.core.postgres import get_postgres_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    postgres = get_postgres_client()
    await postgres.connect()
    yield
    await postgres.close()


def create_app() -> FastAPI:
    """Initialize the FastAPI application."""
    app = FastAPI(title="CortexDB Gateway", version="0.1.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(collections.router)
    app.include_router(records.router)
    app.include_router(search.router)
    app.include_router(files.router)
    app.include_router(providers.router)

    return app


app = create_app()
