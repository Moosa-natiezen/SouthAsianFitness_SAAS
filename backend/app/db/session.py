from collections.abc import Generator
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

database_url = settings.sqlalchemy_database_url

engine_kwargs: dict[str, Any] = {
    # Probe a pooled connection before handing it to a request: hosted
    # Postgres (Neon, Render) silently kills idle sockets, and without this
    # the next request fails with a stale/SSL-closed connection error.
    "pool_pre_ping": True,
    # Recycle connections older than five minutes. Neon's PgBouncer endpoint
    # and Render's managed Postgres both drop idle connections well inside
    # the default 8-hour window.
    "pool_recycle": 300,
}

if database_url.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    engine_kwargs["pool_size"] = 5
    engine_kwargs["max_overflow"] = 10
    # Never let a request hang forever on a saturated/exhausted pool.
    engine_kwargs["pool_timeout"] = 30
    connect_args: dict[str, Any] = {"connect_timeout": 10}
    if database_url.startswith("postgresql+psycopg://"):
        # Neon's pooled endpoint runs PgBouncer in transaction mode, which
        # cannot carry psycopg3's server-side prepared statements across a
        # transaction boundary. Disabling preparation avoids
        # "prepared statement ... does not exist" failures.
        connect_args["prepare_threshold"] = None
    engine_kwargs["connect_args"] = connect_args

engine = create_engine(database_url, **engine_kwargs)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, class_=Session)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
