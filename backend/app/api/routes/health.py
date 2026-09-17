from fastapi import APIRouter, status
from pydantic import BaseModel
from sqlalchemy import text

from app.core.ai_metrics import ai_metrics
from app.core.logging import get_logger
from app.db.session import engine

logger = get_logger(__name__)

router = APIRouter(tags=["health"])

# Keep-alive pinger router: mounted at the application root (no /api prefix)
# so uptime monitors can hit GET /health directly. Zero I/O — it exists purely
# to keep the instance warm on hosting platforms that sleep idle services.
keepalive_router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    api: str
    database: str

    # AI cost metrics: tokens saved via response cache + local math routing.
    ai_tokens_saved: dict[str, int] | None = None


@keepalive_router.get("/health")
def keepalive_check() -> dict[str, str]:
    """Zero-I/O liveness probe for external uptime pingers.

    Deliberately does NOT touch the database or return any diagnostics —
    a keep-alive ping only needs to prove the Python process is serving
    HTTP. Response is a static JSON body, so it stays fast and cheap even
    at pinger frequency.
    """
    return {"status": "healthy"}


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
        ai_tokens_saved=ai_metrics.snapshot(),
    )
