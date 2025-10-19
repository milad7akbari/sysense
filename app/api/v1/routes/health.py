from fastapi import APIRouter
from sqlalchemy.sql import text

from app.db import session as db_session
from app.schemas.common import HealthStatus

router = APIRouter()

@router.get(
    "",
    tags=["Health"],
    response_model=HealthStatus,
    summary="Check application and database health"
)
async def health_check():
    try:
        async with db_session.engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return HealthStatus(status="ok")
    except Exception as exc:
        return HealthStatus(status="unhealthy", detail=str(exc))