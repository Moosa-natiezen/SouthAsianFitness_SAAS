from fastapi import APIRouter, status
from pydantic import BaseModel
from sqlalchemy import text

from app.core.logging import get_logger
from app.db.session import engine

logger = get_logger(__name__)

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    api: str
    database: str


@router.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
def health_check() -> HealthResponse:
    database = "disconnected"
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        database = "connected"
    except Exception:
        logger.exception("Database health check failed")

    return HealthResponse(
        status="ok" if database == "connected" else "degraded",
        api="ok",
        database=database,
    )
