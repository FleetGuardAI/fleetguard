"""
FleetGuard — Database Engine & Session Management
Async SQLAlchemy setup with session dependency injection for FastAPI.
"""

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from typing import AsyncGenerator, Any

from config import settings


from sqlalchemy.pool import NullPool
import os
import uuid

import sys
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import JSONB

@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(type_, compiler, **kw):
    return "JSON"

# --- Hard Safety Guard for Testing ---
import re

def _mask_db_url(url: str) -> str:
    if not url:
        return ""
    return re.sub(r"://([^:@]+):([^@]+)@", r"://\1:***@", url)

def _validate_approved_test_database(url: str) -> None:
    masked = _mask_db_url(url)
    url_lower = url.lower()
    forbidden = [
        "supabase",
        "pooler",
        "aws-",
        "rds.amazonaws",
        "azure",
        "gcp",
        "neon.tech",
        "elephantsql",
        "render.com",
        "railway.app",
        "lckabcseysgzlvkjpgtg",
    ]
    for f in forbidden:
        if f in url_lower:
            raise RuntimeError(
                f"CRITICAL SAFETY VIOLATION: Refusing to create database engine pointing to cloud/production ({masked}) during tests!"
            )
    is_approved_sqlite = "sqlite" in url_lower and ("test" in url_lower or ":memory:" in url_lower)
    is_approved_local_pg = (
        ("postgresql" in url_lower or "asyncpg" in url_lower)
        and ("localhost" in url_lower or "127.0.0.1" in url_lower)
        and "test" in url_lower
    )
    if not (is_approved_sqlite or is_approved_local_pg):
        raise RuntimeError(
            f"CRITICAL SAFETY VIOLATION: Database URL '{masked}' is not an approved isolated test database! "
            "Tests are strictly restricted to isolated test databases (e.g. SQLite test_db or local localhost test DB)."
        )

db_url = settings.DATABASE_URL
if os.environ.get("TESTING") == "True" or "pytest" in sys.modules:
    _validate_approved_test_database(db_url)

# --- Engine ---
connect_args = {}
if "postgresql" in db_url or "asyncpg" in db_url:
    connect_args = {
        "statement_cache_size": 0,
        "prepared_statement_name_func": lambda: f"__asyncpg_{uuid.uuid4()}__",
    }
elif "sqlite" in db_url:
    connect_args = {
        "check_same_thread": False,
        "timeout": 30,
    }

# Automatically use Supabase pooler transaction mode (port 6543) if session mode (port 5432) is configured
if ".pooler.supabase.com:5432" in db_url:
    db_url = db_url.replace(".pooler.supabase.com:5432", ".pooler.supabase.com:6543")

engine_kwargs = {
    "echo": settings.DEBUG,
    "pool_pre_ping": True,
}
if connect_args:
    engine_kwargs["connect_args"] = connect_args

if "sqlite" in db_url:
    from sqlalchemy.pool import StaticPool
    engine_kwargs["poolclass"] = StaticPool
elif os.environ.get("OTP_MOCK_MODE") == "True":
    engine_kwargs["poolclass"] = NullPool
else:
    # Cap connection pool to avoid exhausting Supabase limits under burst traffic
    engine_kwargs["pool_size"] = 5
    engine_kwargs["max_overflow"] = 4
    engine_kwargs["pool_timeout"] = 30
    engine_kwargs["pool_recycle"] = 1800

engine = create_async_engine(
    db_url,
    **engine_kwargs
)

# --- Session Factory ---
async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
AsyncSessionLocal = async_session_factory



# --- Declarative Base ---
class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass


# --- Dependency ---
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields an async database session.
    Automatically commits on success, rolls back on exception, and closes.
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def get_uow() -> AsyncGenerator[Any, None]:
    """
    FastAPI dependency that yields a UnitOfWork.
    """
    from infrastructure.uow import SqlAlchemyUnitOfWork
    async with SqlAlchemyUnitOfWork(async_session_factory) as uow:
        yield uow
        # We DO NOT auto-commit UoW here to force explicit commits by services/routers
        # Note: Depending on strategy, some teams auto-commit. For now, we yield UoW.


async def get_read_uow() -> AsyncGenerator[Any, None]:
    """
    FastAPI dependency that yields a UnitOfWork for read-only routes.
    Creates a session, wraps it in a RepositoryRegistry-compatible UoW,
    and auto-commits on success (like get_db).
    """
    from infrastructure.uow import AbstractUnitOfWork, RepositoryRegistry

    class _SessionUoW(AbstractUnitOfWork):
        """Lightweight UoW wrapping a single session for read-only API endpoints."""
        def __init__(self, session: AsyncSession):
            self._session = session
            self.session = session
            self.repositories = RepositoryRegistry(session)

        async def commit(self):
            await self._session.commit()

        async def rollback(self):
            await self._session.rollback()

    async with async_session_factory() as session:
        uow = _SessionUoW(session)
        try:
            yield uow
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()





# --- Table Management ---
async def create_all_tables() -> None:
    """Create all tables defined by ORM models. Primarily used for isolated test environments."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)



async def drop_all_tables() -> None:
    """Drop all tables. Use with caution — for dev/testing only."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
