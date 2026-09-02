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

    async def get_vehicle_by_id(self, vehicle_id: int, company_id: Optional[int] = None) -> Optional[Vehicle]:
        stmt = select(Vehicle).where(Vehicle.id == vehicle_id)
        if company_id is not None:
            stmt = stmt.where(Vehicle.company_id == company_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_vehicle_by_registration(self, registration_number: str, company_id: Optional[int] = None) -> Optional[Vehicle]:
        stmt = select(Vehicle).where(Vehicle.registration_number == registration_number)
        if company_id is not None:
            stmt = stmt.where(Vehicle.company_id == company_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def search_vehicles(
        self, 
        is_active: Optional[bool] = None, 
        limit: int = 50, 
        offset: int = 0,
        company_id: Optional[int] = None,
        search: Optional[str] = None,
        status: Optional[str] = None
    ) -> Sequence[Vehicle]:
        from sqlalchemy import or_
        query = select(Vehicle)
        if company_id is not None:
            query = query.where(Vehicle.company_id == company_id)
        
        if is_active is not None:
            if is_active:
                query = query.where(Vehicle.status == VehicleStatus.ACTIVE)
            else:
                query = query.where(Vehicle.status != VehicleStatus.ACTIVE)
                
        if status is not None and status.strip().upper() != 'ALL':
            try:
                query = query.where(Vehicle.status == VehicleStatus(status.strip().upper()))
            except ValueError:
                pass
                
        if search is not None and search.strip():
            search_term = f"%{search.strip()}%"
            query = query.where(
                or_(
                    Vehicle.registration_number.ilike(search_term),
                    Vehicle.make.ilike(search_term),
                    Vehicle.model.ilike(search_term)
                )
            )

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
