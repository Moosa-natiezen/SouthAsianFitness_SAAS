from fastapi import APIRouter, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.engine import Engine

from app.core.ai_metrics import ai_metrics
from app.core.logging import get_logger
from app.db.session import create_probe_engine

logger = get_logger(__name__)

router = APIRouter(tags=["health"])

# Keep-alive pinger router: mounted at the application root (no /api prefix)
# so uptime monitors can hit GET /health directly. Zero I/O — it exists purely
# to keep the instance warm on hosting platforms that sleep idle services.
keepalive_router = APIRouter(tags=["health"])

#: Liveness payload shared by both probes. Always ``ok``: these endpoints answer
#: "is the web worker serving HTTP?", and Render kills an instance whose health
#: check does not return 200. Dependency state (DB, warmup) is reported in the
#: separate ``database`` field so a cold Neon compute never fails the probe.
LIVENESS_STATUS = "ok"

#: Cached probe engine: unpooled, 3s connect timeout so a sleeping database
#: cannot make the health check outlast Render's timeout.
_probe_engine: Engine | None = None


def _db_probe_engine() -> Engine:
    global _probe_engine
    if _probe_engine is None:
        _probe_engine = create_probe_engine()
    return _probe_engine


class HealthResponse(BaseModel):
    status: str
    api: str
    database: str

    # AI cost metrics: tokens saved via response cache + local math routing.
    ai_tokens_saved: dict[str, int] | None = None


@keepalive_router.get("/health")
def keepalive_check() -> dict[str, str]:
    """Zero-I/O liveness probe (external uptime pingers + Render fallback).

    Deliberately does NOT touch the database or return any diagnostics — a
    keep-alive ping only needs to prove the Python process is serving HTTP.
    Response is a static JSON body, so it stays fast and cheap even at pinger
    frequency and answers instantly while the database is still warming up.
    """
    return {"status": LIVENESS_STATUS}


@router.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
def health_check() -> HealthResponse:
    """Health probe with diagnostics; always HTTP 200 + ``status: ok``.

    The database probe result is reported in ``database`` instead of downgrading
    ``status``: a sleeping Neon instance or a failed optional seed must not make
    Render consider the worker unhealthy and restart it.
    """
    database = "disconnected"
    try:
        with _db_probe_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
        database = "connected"
    except Exception:
        logger.exception("Database health check failed")

    return HealthResponse(
        status=LIVENESS_STATUS,
        api="ok",
        database=database,
        ai_tokens_saved=ai_metrics.snapshot(),
    )
