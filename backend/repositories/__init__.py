"""
FleetGuard — Repositories Package

The repository layer provides all database read/write access for FleetGuard.

Responsibilities
----------------
• Translate application-level queries into SQLAlchemy statements.
• Abstract the database from services and routers.
• Raise domain-level exceptions (not HTTP exceptions).

Usage
-----
Repositories accept an ``AsyncSession`` injected via FastAPI's ``Depends(get_db)``
or passed directly from a service.

    from repositories import OperationalEventRepository

    async def my_service(db: AsyncSession = Depends(get_db)):
        repo = OperationalEventRepository(db)
        events = await repo.list_events(limit=20)
"""

from repositories.operational_event_repository import OperationalEventRepository

__all__ = [
    "OperationalEventRepository",
]
