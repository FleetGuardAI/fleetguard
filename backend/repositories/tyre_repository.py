"""
FleetGuard — Tyre Repository
Handles database operations for the Tyre Domain.
"""

from typing import Optional, Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.tyre_domain import Tyre, TyreLifecycleRecord, TyreStatus


class TyreRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_tyre_by_id(self, tyre_id: int) -> Optional[Tyre]:
        return await self.db.get(Tyre, tyre_id)

    async def get_tyre_by_serial_number(self, serial_number: str) -> Optional[Tyre]:
        stmt = select(Tyre).where(Tyre.serial_number == serial_number)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_tyres_by_vehicle(self, vehicle_id: int, limit: int = 50, offset: int = 0) -> Sequence[Tyre]:
        stmt = select(Tyre).where(Tyre.current_vehicle_id == vehicle_id).order_by(Tyre.id.desc()).offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def search_tyres(
        self, 
        status: Optional[TyreStatus] = None, 
        limit: int = 50, 
        offset: int = 0
    ) -> Sequence[Tyre]:
        query = select(Tyre)
        
        if status is not None:
            query = query.where(Tyre.current_status == status)

        query = query.order_by(Tyre.id.desc()).offset(offset).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def upsert_tyre(self, tyre: Tyre) -> Tyre:
        self.db.add(tyre)
        await self.db.flush()
        await self.db.refresh(tyre)
        return tyre
        
    async def add_lifecycle_record(self, record: TyreLifecycleRecord) -> TyreLifecycleRecord:
        self.db.add(record)
        await self.db.flush()
        await self.db.refresh(record)
        return record
