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



def _sync_sqlite_columns(sync_conn):
    """Inspects existing SQLite tables and adds any missing ORM columns automatically."""
    for table_name, table in Base.metadata.tables.items():
        # Fetch PRAGMA info to discover existing columns (safe — never references ORM metadata)
        cursor_res = sync_conn.exec_driver_sql(f"PRAGMA table_info('{table_name}')")
        existing_cols = {row[1] for row in cursor_res.fetchall()}
        
        for col in table.columns:
            if col.name not in existing_cols:
                type_str = str(col.type).upper()
                col_type = "INTEGER" if "INT" in type_str else "REAL" if ("FLOAT" in type_str or "REAL" in type_str) else "BOOLEAN" if "BOOL" in type_str else "VARCHAR"
                try:
                    sync_conn.exec_driver_sql(f"ALTER TABLE {table_name} ADD COLUMN {col.name} {col_type}")
                except Exception:
                    pass

# --- Table Management ---
async def create_all_tables() -> None:
    """Create all tables defined by ORM models and sync columns. Called on app startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        if settings.DATABASE_URL.startswith("sqlite"):
            await conn.run_sync(_sync_sqlite_columns)



async def drop_all_tables() -> None:
    """Drop all tables. Use with caution — for dev/testing only."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
