"""
FleetGuard — Vehicle Repository
Handles database operations for the Vehicle Domain.
"""

from typing import Optional, Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.vehicle_domain import Vehicle, VehicleStatus


class VehicleRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_vehicle_by_id(self, vehicle_id: int) -> Optional[Vehicle]:
        return await self.db.get(Vehicle, vehicle_id)

    async def get_vehicle_by_registration(self, registration_number: str) -> Optional[Vehicle]:
        stmt = select(Vehicle).where(Vehicle.registration_number == registration_number)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def search_vehicles(
        self, 
        is_active: Optional[bool] = None, 
        limit: int = 50, 
        offset: int = 0
    ) -> Sequence[Vehicle]:
        query = select(Vehicle)
        
        if is_active is not None:
            if is_active:
                query = query.where(Vehicle.status == VehicleStatus.ACTIVE)
            else:
                query = query.where(Vehicle.status != VehicleStatus.ACTIVE)

        query = query.order_by(Vehicle.registration_number).offset(offset).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def upsert_vehicle(self, vehicle: Vehicle) -> Vehicle:
        """
        Since this domain is event-driven, the service layer will handle
        reading the existing vehicle and modifying its fields, or creating a new one.
        The repository just persists the ORM object.
        """
        self.db.add(vehicle)
        await self.db.flush()
        await self.db.refresh(vehicle)
        return vehicle
