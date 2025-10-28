from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from gateway.api import api_keys, collections, databases, files, health, providers, records, search
from gateway.core.postgres import get_postgres_client
from gateway.core.migrations import run_migrations
from gateway.core.bootstrap import bootstrap_admin_key
from gateway.utils.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    postgres = get_postgres_client()
    await postgres.connect()
    
    # Run database migrations
    logger.info("running_database_migrations")
    await run_migrations(postgres.pool)
    logger.info("migrations_completed")
    
    # Bootstrap admin API key if needed
    logger.info("checking_admin_key")
    await bootstrap_admin_key(postgres.pool)
    logger.info("admin_key_ready")
    
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
    app.include_router(api_keys.router)
    app.include_router(databases.router)
    app.include_router(collections.router)
    app.include_router(collections.database_collections_router)  # Database-scoped collections
    app.include_router(records.router)
    app.include_router(search.router)
    app.include_router(files.router)
    app.include_router(providers.router)

    return app


app = create_app()
