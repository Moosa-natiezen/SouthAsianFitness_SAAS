"""Startup schema initialisation.

Render provisions a brand-new Neon PostgreSQL database with *no* tables, so the
backend has to be able to build its own schema on boot instead of relying on a
manual ``alembic upgrade head`` before the first request.

Strategy:

* If Alembic has already stamped the database (``alembic_version`` holds a
  revision), the migrations are authoritative — apply anything pending with
  ``upgrade head``.
* Otherwise the database is new or untracked: create every table from the ORM
  metadata (installing the ``vector`` extension that ``user_memories`` needs,
  which ``create_all`` cannot do by itself) and stamp Alembic at head so later
  ``alembic upgrade`` runs continue from a consistent baseline.

Every DDL step runs on a dedicated ``NullPool`` + ``AUTOCOMMIT`` engine. Neon's
``-pooler`` endpoint is PgBouncer in transaction mode: it multiplexes sessions
onto shared server backends and commits transactions behind the client's back,
which breaks multi-statement DDL and Alembic's advisory locks. An unpooled
autocommit connection issues each DDL statement straight to the server and is
torn down immediately afterwards.

Every step is retried a few times because a freshly provisioned Neon database
can refuse the first connection while the compute instance wakes up.
"""

from __future__ import annotations

import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from pgvector.sqlalchemy import Vector
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import NullPool

import app.models  # noqa: F401  (registers every model on Base.metadata)
from app.core.logging import get_logger
from app.db.base import Base
from app.db.session import create_db_engine

logger = get_logger(__name__)

BACKEND_DIR = Path(__file__).resolve().parents[2]
ALEMBIC_INI = BACKEND_DIR / "alembic.ini"
ALEMBIC_DIR = BACKEND_DIR / "alembic"


def _alembic_config() -> Config:
    """Build an Alembic config that works regardless of the process cwd."""
    config = Config(str(ALEMBIC_INI))
    config.set_main_option("script_location", str(ALEMBIC_DIR))
    return config


@contextmanager
def _ddl_engine() -> Iterator[Engine]:
    """Yield a dedicated DDL engine: no pool, no implicit transaction."""
    connection_engine = create_db_engine(
        poolclass=NullPool,
        isolation_level="AUTOCOMMIT",
    )
    try:
        yield connection_engine
    finally:
        connection_engine.dispose()


def _current_revision(connection_engine: Engine) -> str | None:
    """Return the revision the database is stamped at, or None if untracked."""
    with connection_engine.connect() as connection:
        return MigrationContext.configure(connection).get_current_revision()


def _ensure_vector_extension(connection_engine: Engine) -> bool:
    """Try to enable pgvector; report whether the extension is usable.

    Isolated on purpose: on a Neon free-tier database the application role may
    lack permission to ``CREATE EXTENSION``. That must not abort startup — the
    tables without vector columns are still perfectly usable.
    """
    if connection_engine.dialect.name != "postgresql":
        return True

    try:
        with connection_engine.connect() as connection:
            connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        logger.info("pgvector extension is available")
        return True
    except SQLAlchemyError as exc:
        logger.warning(
            "Could not enable the pgvector extension (%s: %s); continuing without "
            "vector-backed tables. Grant the role permission to CREATE EXTENSION "
            "and restart to create them.",
            type(exc).__name__,
            exc,
        )
        return False


def _vector_backed_tables() -> set[str]:
    """Table names holding a pgvector column (cannot exist without the extension)."""
    return {
        table.name
        for table in Base.metadata.sorted_tables
        if any(isinstance(column.type, Vector) for column in table.columns)
    }


def _bootstrap_from_metadata(connection_engine: Engine) -> None:
    """Create the schema from ORM metadata and stamp Alembic at head."""
    vector_available = _ensure_vector_extension(connection_engine)

    skipped = set() if vector_available else _vector_backed_tables()
    tables = [table for table in Base.metadata.sorted_tables if table.name not in skipped]

    Base.metadata.create_all(bind=connection_engine, tables=tables)
    logger.info(
        "Bootstrapped schema from ORM metadata: %d tables created", len(tables)
    )

    if skipped:
        # Do not stamp: the schema is deliberately incomplete, so Alembic must
        # stay free to replay the migration that adds these tables later.
        logger.warning(
            "Skipped vector-backed tables because pgvector is unavailable: %s",
            ", ".join(sorted(skipped)),
        )
        logger.warning(
            "Alembic left unstamped; run `alembic upgrade head` after enabling pgvector"
        )
        return

    # Stamp the baseline so future `alembic upgrade head` runs apply only the
    # migrations newer than this schema instead of replaying from scratch.
    try:
        with connection_engine.connect() as connection:
            config = _alembic_config()
            config.attributes["connection"] = connection
            command.stamp(config, "head")
        logger.info("Stamped Alembic version table at head")
    except Exception:  # pragma: no cover - non-fatal bookkeeping step
        logger.exception(
            "Could not stamp Alembic after schema bootstrap; "
            "run `alembic stamp head` manually before future migrations"
        )


def _apply_migrations(connection_engine: Engine) -> None:
    """Run ``alembic upgrade head`` on the dedicated DDL connection."""
    with connection_engine.connect() as connection:
        config = _alembic_config()
        config.attributes["connection"] = connection
        command.upgrade(config, "head")


def init_db(max_attempts: int = 4, initial_delay: float = 2.0) -> None:
    """Create or migrate the database schema. Safe to call on every startup."""
    delay = initial_delay
    for attempt in range(1, max_attempts + 1):
        try:
            with _ddl_engine() as connection_engine:
                revision = _current_revision(connection_engine)
                if revision:
                    logger.info(
                        "Database is versioned at %s; applying pending migrations",
                        revision,
                    )
                    _apply_migrations(connection_engine)
                    logger.info("Database migrations are up to date")
                else:
                    logger.info(
                        "No Alembic revision found; bootstrapping schema from ORM metadata"
                    )
                    _bootstrap_from_metadata(connection_engine)
            return
        except Exception as exc:
            if attempt == max_attempts:
                logger.exception(
                    "Database initialisation failed after %d attempts", max_attempts
                )
                raise
            logger.warning(
                "Database initialisation attempt %d/%d failed (%s: %s); retrying in %.0fs",
                attempt,
                max_attempts,
                type(exc).__name__,
                exc,
                delay,
            )
            time.sleep(delay)
            delay *= 2
