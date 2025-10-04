from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy.sql import text

from app.db import session as db_session

router = APIRouter()

class HealthStatus(BaseModel):
    status: str
    detail: str | None = None

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
        # In a real app, you might want to log this error
        return HealthStatus(status="unhealthy", detail=str(exc))