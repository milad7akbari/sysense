from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from pydantic import BaseModel
from sqlalchemy.sql import text
from app.api.v1.routes import health, auth, user
from app.core.config import settings
from app.core.logging_config import configure_logging
from app.db import session as db_session

# Configure logging at the module's entry point
configure_logging()
log = logging.getLogger(__name__)


# Use a Pydantic model for the health check response for automatic validation and documentation
class HealthStatus(BaseModel):
    status: str
    detail: str | None = None


# Use the 'lifespan' context manager for startup and shutdown logic.
# This is the modern replacement for on_event("startup") / on_event("shutdown").
@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info(f"Starting up {settings.PROJECT_NAME}...")
    # Initialize and test the database connection pool on startup
    try:
        async with db_session.engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        log.info("Database connection pool established successfully.")
    except Exception as e:
        log.critical(f"Failed to connect to the database on startup: {e}")
        # In a real-world scenario, you might want the app to fail starting
        # if the DB isn't available.
    yield
    # Cleanly close the connection pool on shutdown
    log.info("Closing database connection pool...")
    await db_session.engine.dispose()
    log.info("Shutdown complete.")


def create_app() -> FastAPI:
    """
    Application factory to create and configure the FastAPI app instance.
    """
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version="1.0.0",
        openapi_prefix=settings.API_V1_STR,
        lifespan=lifespan,
    )

    # app.add_middleware(
    #     CORSMiddleware,
    #     allow_origins=settings.CORS_ORIGINS,
    #     allow_credentials=True,
    #     allow_methods=["*"],
    #     allow_headers=["*"],
    # )
    # app.add_middleware(
    #     TrustedHostMiddleware,
    #     allowed_hosts=settings.TRUSTED_HOSTS
    # )
    # app.add_middleware(
    #     RateLimitMiddleware,
    #     requests_per_minute=settings.RATE_LIMIT
    # )

    # --- API Routers ---
    # Including routers makes the project scalable.
    app.include_router(health.router, prefix="/health", tags=["Health"])
    app.include_router(user.router, prefix="/users")
    app.include_router(auth.router)

    return app


app = create_app()