"""
FleetGuard — Trip Repository
Handles database operations for the Trip Domain.
"""

from typing import Optional, Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.trip_domain import Trip, TripStatus


class TripRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_trip_by_id(self, trip_id: int) -> Optional[Trip]:
        return await self.db.get(Trip, trip_id)

    async def get_trip_by_business_id(self, trip_business_id: str) -> Optional[Trip]:
        stmt = select(Trip).where(Trip.trip_id == trip_business_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_trips_by_vehicle(self, vehicle_id: int, limit: int = 50, offset: int = 0) -> Sequence[Trip]:
        stmt = select(Trip).where(Trip.vehicle_id == vehicle_id).order_by(Trip.id.desc()).offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_trips_by_driver(self, driver_id: int, limit: int = 50, offset: int = 0) -> Sequence[Trip]:
        stmt = select(Trip).where(Trip.driver_id == driver_id).order_by(Trip.id.desc()).offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def search_trips(
        self, 
        status: Optional[TripStatus] = None, 
        limit: int = 50, 
        offset: int = 0,
        company_id: Optional[int] = None,
        search: Optional[str] = None
    ) -> Sequence[Trip]:
        from sqlalchemy import or_
        query = select(Trip)
        
        if company_id is not None:
            query = query.where(Trip.company_id == company_id)

        if status is not None:
            query = query.where(Trip.status == status)

        if search is not None and search.strip():
            search_term = f"%{search.strip()}%"
            query = query.where(
                or_(
                    Trip.trip_id.ilike(search_term),
                    Trip.origin_location.ilike(search_term),
                    Trip.destination_location.ilike(search_term)
                )
            )

        query = query.order_by(Trip.id.desc()).offset(offset).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def upsert_trip(self, trip: Trip) -> Trip:
        self.db.add(trip)
        await self.db.flush()
        await self.db.refresh(trip)
        return trip
