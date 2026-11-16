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

Every step is retried a few times because a freshly provisioned Neon database
can refuse the first connection while the compute instance wakes up.
"""

from __future__ import annotations

import time
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

import app.models  # noqa: F401  (registers every model on Base.metadata)
from app.core.logging import get_logger
from app.db.base import Base
from app.db.session import engine

logger = get_logger(__name__)

BACKEND_DIR = Path(__file__).resolve().parents[2]
ALEMBIC_INI = BACKEND_DIR / "alembic.ini"
ALEMBIC_DIR = BACKEND_DIR / "alembic"


def _alembic_config() -> Config:
    """Build an Alembic config that works regardless of the process cwd."""
    config = Config(str(ALEMBIC_INI))
    config.set_main_option("script_location", str(ALEMBIC_DIR))
    return config


def _current_revision() -> str | None:
    """Return the revision the database is stamped at, or None if untracked."""
    with engine.connect() as connection:
        return MigrationContext.configure(connection).get_current_revision()


def _ensure_extensions() -> None:
    """Install the pgvector extension before the ``user_memories`` table."""
    if engine.dialect.name != "postgresql":
        return
    try:
        with engine.begin() as connection:
            connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        logger.info("pgvector extension is available")
    except SQLAlchemyError as exc:
        raise RuntimeError(
            "pgvector extension could not be enabled; the user_memories table "
            "cannot be created. Enable the vector extension on the database "
            "(Neon: `CREATE EXTENSION vector` via a superuser/SQL editor)."
        ) from exc


def _bootstrap_from_metadata() -> None:
    """Create the full schema from ORM metadata and stamp Alembic at head."""
    _ensure_extensions()
    Base.metadata.create_all(bind=engine)
    logger.info(
        "Bootstrapped schema from ORM metadata: %d tables created",
        len(Base.metadata.sorted_tables),
    )

    # Stamp the baseline so future `alembic upgrade head` runs apply only the
    # migrations newer than this schema instead of replaying from scratch.
    try:
        command.stamp(_alembic_config(), "head")
        logger.info("Stamped Alembic version table at head")
    except Exception:  # pragma: no cover - non-fatal bookkeeping step
        logger.exception(
            "Could not stamp Alembic after schema bootstrap; "
            "run `alembic stamp head` manually before future migrations"
        )


def init_db(max_attempts: int = 4, initial_delay: float = 2.0) -> None:
    """Create or migrate the database schema. Safe to call on every startup."""
    delay = initial_delay
    for attempt in range(1, max_attempts + 1):
        try:
            revision = _current_revision()
            if revision:
                logger.info(
                    "Database is versioned at %s; applying pending migrations", revision
                )
                command.upgrade(_alembic_config(), "head")
                logger.info("Database migrations are up to date")
            else:
                logger.info(
                    "No Alembic revision found; bootstrapping schema from ORM metadata"
                )
                _bootstrap_from_metadata()
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
