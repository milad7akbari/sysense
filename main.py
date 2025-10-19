from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from sqlalchemy.sql import text
from app.api.v1.routes import health, auth, user, product as product_router, interaction as interaction_router, collection as collection_router
from app.core.config import settings
from app.core.logging_config import configure_logging
from app.db import session as db_session

# Configure logging at the module's entry point
configure_logging()
log = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(_app: FastAPI):
    log.info(f"Starting up {settings.PROJECT_NAME}...")
    # Initialize and test the database connection pool on startup
    try:
        async with db_session.engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        log.info("Database connection pool established successfully.")
    except Exception as e:
        log.critical(f"Failed to connect to the database on startup: {e}")
    yield
    # Cleanly close the connection pool on shutdown
    log.info("Closing database connection pool...")
    await db_session.engine.dispose()
    log.info("Shutdown complete.")


def create_app() -> FastAPI:
    """
    Application factory to create and configure the FastAPI app instance.
    """
    app_instance = FastAPI(
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
    app_instance.include_router(health.router, prefix="/health", tags=["Health"])
    app_instance.include_router(user.router, prefix="/users")
    app_instance.include_router(product_router.router, prefix="/products")
    app_instance.include_router(auth.router)
    app_instance.include_router(interaction_router.router)
    app_instance.include_router(collection_router.router)
    return app_instance


app = create_app()