from collections.abc import Generator
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import settings

database_url = settings.sqlalchemy_database_url

#: Pool arguments that only exist on pooling pool classes; ``create_engine``
#: rejects them outright when ``NullPool``/``StaticPool`` is requested.
_POOL_SIZE_KEYS = ("pool_size", "max_overflow", "pool_timeout")


def build_engine_kwargs(url: str, **overrides: Any) -> dict[str, Any]:
    """Return ``create_engine`` keyword arguments for ``url``.

    Shared by the application engine (pooled, long-lived) and the DDL engine in
    :mod:`app.db.init_db` (``NullPool`` + ``AUTOCOMMIT``), so both talk to
    Neon/Render with the same connect arguments.
    """
    kwargs: dict[str, Any] = {
        # Probe a pooled connection before handing it to a request: hosted
        # Postgres (Neon, Render) silently kills idle sockets, and without this
        # the next request fails with a stale/SSL-closed connection error.
        "pool_pre_ping": True,
        # Recycle connections older than five minutes. Neon's PgBouncer endpoint
        # and Render's managed Postgres both drop idle connections well inside
        # the default 8-hour window.
        "pool_recycle": 300,
    }

    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    else:
        kwargs["pool_size"] = 5
        kwargs["max_overflow"] = 10
        # Never let a request hang forever on a saturated/exhausted pool.
        kwargs["pool_timeout"] = 30
        connect_args: dict[str, Any] = {"connect_timeout": 10}
        if url.startswith("postgresql+psycopg://"):
            # Neon's pooled endpoint runs PgBouncer in transaction mode, which
            # cannot carry psycopg3's server-side prepared statements across a
            # transaction boundary. Disabling preparation avoids
            # "prepared statement ... does not exist" failures.
            connect_args["prepare_threshold"] = None
        kwargs["connect_args"] = connect_args

    kwargs.update(overrides)

    if kwargs.get("poolclass") is not None:
        for key in _POOL_SIZE_KEYS:
            kwargs.pop(key, None)

    return kwargs


def create_db_engine(url: str | None = None, **overrides: Any) -> Engine:
    """Create an engine for ``url`` (defaults to the configured database)."""
    target_url = url or database_url
    return create_engine(target_url, **build_engine_kwargs(target_url, **overrides))


def create_probe_engine(connect_timeout: int = 4) -> Engine:
    """Create an unpooled engine for health probes with a short connect timeout.

    The application engine allows 10s to connect, which is right for user
    requests but far too slow for a liveness probe: Render restarts an instance
    whose health check does not answer in time, so a sleeping Neon compute must
    fail fast instead of stalling the check.
    """
    target_url = database_url
    kwargs = build_engine_kwargs(target_url, poolclass=NullPool)
    if not target_url.startswith("sqlite"):
        connect_args = dict(kwargs.get("connect_args") or {})
        connect_args["connect_timeout"] = connect_timeout
        kwargs["connect_args"] = connect_args
    return create_engine(target_url, **kwargs)


engine = create_db_engine()

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, class_=Session)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
