"""
FleetGuard — Driver Intelligence Service
Derives driver operational data: availability, suitability, performance history.
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from models.driver_domain import Driver
from models.trip_domain import Trip, TripStatus
from schemas.pre_trip_intelligence import SuitabilityAssessment, SuitabilityStatus
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class DriverIntelligence:
    def __init__(self, db: AsyncSession, config):
        self.db = db
        self.config = config

    async def evaluate_suitability(
        self, 
        driver: Driver, 
        planned_start: Optional[datetime],
        planned_end: Optional[datetime],
        route_distance_km: Optional[float]
    ) -> SuitabilityAssessment:
        reasons = []
        status = SuitabilityStatus.SUITABLE
        
        # Check active trips (Availability)
        active_stmt = select(Trip).where(
            and_(
                Trip.driver_id == driver.id,
                Trip.status.in_([TripStatus.CREATED, TripStatus.IN_PROGRESS])
            )
        )
        active_res = await self.db.execute(active_stmt)
        active_trips = active_res.scalars().all()
        
        if active_trips:
            status = SuitabilityStatus.UNSUITABLE
            reasons.append("Driver is currently assigned to an active trip.")
            
        # Check Driver Status
        if driver.status.lower() != "active":
            status = SuitabilityStatus.UNSUITABLE
            reasons.append(f"Driver status is {driver.status}.")
            
        if driver.duty_status and driver.duty_status.lower() in ["off_duty", "on_leave"]:
            status = SuitabilityStatus.UNSUITABLE
            reasons.append(f"Driver duty status is {driver.duty_status}.")

        if not reasons:
            reasons.append("Driver is available and suitable for the trip.")
            
        return SuitabilityAssessment(status=status, reasons=reasons)
