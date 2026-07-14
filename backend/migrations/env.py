"""
FleetGuard — Alembic Migration Environment

Configured for:
  • Async SQLAlchemy (asyncpg / aiosqlite)
  • URL injected from FleetGuard's pydantic-settings (reads .env)
  • Autogenerate support — all ORM models are imported via models package

Usage
-----
Apply migrations:
    alembic upgrade head

Roll back one step:
    alembic downgrade -1

Generate a new migration:
    alembic revision --autogenerate -m "description"

Show current revision:
    alembic current
"""

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# ---------------------------------------------------------------------------
# FleetGuard: import application config and all ORM models so that
# Base.metadata is fully populated for autogenerate.
# ---------------------------------------------------------------------------
from config import settings  # noqa: E402 — must come after sys.path is set

# Import models package — this registers every model with Base.metadata
import models  # noqa: F401, E402

from database import Base  # noqa: E402

# ---------------------------------------------------------------------------
# Alembic Config
# ---------------------------------------------------------------------------
config = context.config

# Override sqlalchemy.url from pydantic-settings so credentials never
# live in alembic.ini.
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Autogenerate target — all tables registered on Base.metadata
target_metadata = Base.metadata


# ---------------------------------------------------------------------------
# Offline mode (generates SQL without a live DB connection)
# ---------------------------------------------------------------------------

def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    Generates SQL scripts without connecting to the database.
    Useful for reviewing what Alembic will do, or for DBAs who apply
    migrations manually.

    Run with:
        alembic upgrade head --sql
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


# ---------------------------------------------------------------------------
# Online mode (connects to DB and applies migrations directly)
# ---------------------------------------------------------------------------

def do_run_migrations(connection: Connection) -> None:
    """Execute migrations on an active synchronous connection."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    Run migrations using an async engine.

    Creates a transient sync connection from the async engine so that
    Alembic (which is synchronous) can execute DDL statements.
    """
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """
    Entry point for online migration mode.

    Bridges Alembic's synchronous interface with the project's async engine.
    """
    asyncio.run(run_async_migrations())


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
