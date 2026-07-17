"""
FleetGuard — Driver Repository
Handles database operations for the Driver Domain.
"""

from typing import Optional, Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.driver_domain import Driver, DriverStatus


class DriverRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_driver_by_id(self, driver_id: int) -> Optional[Driver]:
        return await self.db.get(Driver, driver_id)

    async def get_driver_by_phone(self, phone_number: str) -> Optional[Driver]:
        stmt = select(Driver).where(Driver.phone_number == phone_number)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_driver_by_employee_id(self, employee_id: str) -> Optional[Driver]:
        stmt = select(Driver).where(Driver.employee_id == employee_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def search_drivers(
        self, 
        is_active: Optional[bool] = None, 
        limit: int = 50, 
        offset: int = 0
    ) -> Sequence[Driver]:
        query = select(Driver)
        
        if is_active is not None:
            if is_active:
                query = query.where(Driver.status == DriverStatus.ACTIVE)
            else:
                query = query.where(Driver.status != DriverStatus.ACTIVE)

        query = query.order_by(Driver.name).offset(offset).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def upsert_driver(self, driver: Driver) -> Driver:
        self.db.add(driver)
        await self.db.flush()
        await self.db.refresh(driver)
        return driver
