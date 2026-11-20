from fastapi import APIRouter, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from app.core.ai_metrics import ai_metrics
from app.core.logging import get_logger
from app.db.session import create_probe_engine

logger = get_logger(__name__)

router = APIRouter(tags=["health"])

# Keep-alive pinger router: mounted at the application root (no /api prefix)
# so uptime monitors can hit GET/HEAD /health directly. It touches the database
# with a cheap SELECT 1 so a 5-minute pinger cadence keeps Neon's compute from
# suspending, not just Render's web service.
keepalive_router = APIRouter(tags=["health"])

#: Liveness payload shared by both probes. Always ``ok``: these endpoints answer
#: "is the web worker serving HTTP?", and Render kills an instance whose health
#: check does not return 200. Dependency state (DB, warmup) is reported in the
#: separate ``database`` field so a cold Neon compute never fails the probe.
LIVENESS_STATUS = "ok"

#: Cached probe engine: unpooled, 4s connect timeout so a sleeping database
#: cannot make the health check outlast Render's timeout.
_probe_engine: Engine | None = None


def _db_probe_engine() -> Engine:
    global _probe_engine
    if _probe_engine is None:
        _probe_engine = create_probe_engine(connect_timeout=4)
    return _probe_engine


class HealthResponse(BaseModel):
    status: str
    api: str
    database: str

    # AI cost metrics: tokens saved via response cache + local math routing.
    ai_tokens_saved: dict[str, int] | None = None


@keepalive_router.api_route("/health", methods=["GET", "HEAD"])
def keepalive_check() -> dict[str, str]:
    """Liveness probe that also keeps Neon PostgreSQL from suspending.

    Accepts GET and HEAD so both UptimeRobot monitor types answer 200. Render
    stays awake by serving the request; Neon only stays awake if its compute is
    actually queried, so the probe issues a cheap ``SELECT 1``. The probe is
    best-effort: a sleeping or failed database is logged and still answered
    with 200 -- Render must never recycle a worker because Neon was asleep.
    """
    try:
        with _db_probe_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
    except (SQLAlchemyError, RuntimeError, OSError):
        logger.warning("Keep-alive database ping failed; answering 200 anyway")

    return {"status": LIVENESS_STATUS}


@router.api_route(
    "/health",
    methods=["GET", "HEAD"],
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
)
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
