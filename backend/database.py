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


# --- Engine ---
# For SQLite: connect_args needed to allow multi-thread access
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    connect_args=connect_args,
    pool_pre_ping=True,
)

# --- Session Factory ---
async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


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


# --- Table Management ---
async def create_all_tables() -> None:
    """Create all tables defined by ORM models. Called on app startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_all_tables() -> None:
    """Drop all tables. Use with caution — for dev/testing only."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
