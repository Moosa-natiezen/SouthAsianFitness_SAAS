from logging.config import fileConfig

import app.models  # noqa: F401
from alembic import context
from app.core.config import settings
from app.db.base import Base
from sqlalchemy import create_engine, pool

config = context.config
config.set_main_option("sqlalchemy.url", settings.sqlalchemy_database_url.replace("%", "%%"))

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=settings.sqlalchemy_database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def _run_migrations_on(connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    # Migrations are DDL. Neon's ``-pooler`` endpoint is PgBouncer in transaction
    # mode, which cannot carry multi-statement DDL or Alembic's advisory locks,
    # so migrations always run on an unpooled AUTOCOMMIT connection. Callers
    # such as ``app.db.init_db`` pass one in via ``config.attributes``.
    shared_connection = config.attributes.get("connection")
    if shared_connection is not None:
        _run_migrations_on(shared_connection)
        return

    connectable = create_engine(
        settings.sqlalchemy_database_url,
        poolclass=pool.NullPool,
        isolation_level="AUTOCOMMIT",
    )

    try:
        with connectable.connect() as connection:
            _run_migrations_on(connection)
    finally:
        connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
