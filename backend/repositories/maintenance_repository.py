"""
FleetGuard — Maintenance Repository
Handles database operations for the Maintenance Domain.
"""

from typing import Optional, Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.maintenance_domain import MaintenanceRecord, MaintenanceTask, MaintenanceStatus


class MaintenanceRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_maintenance_by_id(self, maintenance_id: int) -> Optional[MaintenanceRecord]:
        return await self.db.get(MaintenanceRecord, maintenance_id)

    async def get_maintenance_by_business_id(self, business_id: str) -> Optional[MaintenanceRecord]:
        stmt = select(MaintenanceRecord).where(MaintenanceRecord.business_id == business_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_maintenance_by_vehicle(self, vehicle_id: int, limit: int = 50, offset: int = 0) -> Sequence[MaintenanceRecord]:
        stmt = select(MaintenanceRecord).where(MaintenanceRecord.vehicle_id == vehicle_id).order_by(MaintenanceRecord.id.desc()).offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def search_maintenance(
        self, 
        status: Optional[MaintenanceStatus] = None, 
        limit: int = 50, 
        offset: int = 0
    ) -> Sequence[MaintenanceRecord]:
        query = select(MaintenanceRecord)
        
        if status is not None:
            query = query.where(MaintenanceRecord.status == status)

        query = query.order_by(MaintenanceRecord.id.desc()).offset(offset).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def upsert_maintenance_record(self, record: MaintenanceRecord) -> MaintenanceRecord:
        self.db.add(record)
        await self.db.flush()
        await self.db.refresh(record)
        return record
        
    async def get_task_by_id(self, task_id: int) -> Optional[MaintenanceTask]:
        return await self.db.get(MaintenanceTask, task_id)
        
    async def upsert_maintenance_task(self, task: MaintenanceTask) -> MaintenanceTask:
        self.db.add(task)
        await self.db.flush()
        await self.db.refresh(task)
        return task
