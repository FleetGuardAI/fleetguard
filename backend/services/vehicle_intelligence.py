"""
FleetGuard — Vehicle Intelligence Service
Derives vehicle operational data: historical mileage, availability, suitability.
"""

from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, text
from models.vehicle_domain import Vehicle
from models.trip_domain import Trip, TripStatus
from models.maintenance_domain import MaintenanceRecord, MaintenanceStatus
from schemas.pre_trip_intelligence import SuitabilityAssessment, SuitabilityStatus, Assumption
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class VehicleIntelligence:
    def __init__(self, db: AsyncSession, config):
        self.db = db
        self.config = config

    async def get_mileage_estimate(self, vehicle_id: int) -> Tuple[Optional[float], Assumption]:
        """
        Derives expected mileage (km/L) for a vehicle.
        Priority: 
        1. Vehicle's historical average (if sufficient trips)
        2. Fleet average for similar fuel type
        3. System default
        """
        try:
            # 1. Vehicle Historical
            stmt = select(func.avg(Trip.actual_distance / Trip.actual_fuel_liters)).where(
                and_(
                    Trip.vehicle_id == vehicle_id,
                    Trip.status == TripStatus.COMPLETED,
                    Trip.actual_distance > 0,
                    Trip.actual_fuel_liters > 0
                )
            )
            result = await self.db.execute(stmt)
            avg_mileage = result.scalar()
            
            if avg_mileage and avg_mileage > 0:
                # Need to know sample size for confidence
                count_stmt = select(func.count(Trip.id)).where(
                    and_(
                        Trip.vehicle_id == vehicle_id,
                        Trip.status == TripStatus.COMPLETED,
                        Trip.actual_distance > 0,
                        Trip.actual_fuel_liters > 0
                    )
                )
                count_res = await self.db.execute(count_stmt)
                count = count_res.scalar() or 0
                
                confidence = "HIGH" if count >= 5 else "MEDIUM"
                
                return avg_mileage, Assumption(
                    metric="Fuel Efficiency",
                    value=round(avg_mileage, 2),
                    unit="km/L",
                    source="vehicle_historical",
                    confidence=confidence,
                    sample_size=count
                )
        except Exception as e:
            logger.error(f"Error calculating vehicle historical mileage: {e}")
            
        # Fallback to system default
        return self.config.default_fuel_efficiency_kmpl, Assumption(
            metric="Fuel Efficiency",
            value=self.config.default_fuel_efficiency_kmpl,
            unit="km/L",
            source="system_default",
            confidence="LOW"
        )

    async def evaluate_suitability(
        self, 
        vehicle: Vehicle, 
        planned_start: Optional[datetime],
        planned_end: Optional[datetime],
        route_distance_km: Optional[float]
    ) -> SuitabilityAssessment:
        reasons = []
        status = SuitabilityStatus.SUITABLE
        
        # Check active trips (Availability)
        active_stmt = select(Trip).where(
            and_(
                Trip.vehicle_id == vehicle.id,
                Trip.status.in_([TripStatus.CREATED, TripStatus.IN_PROGRESS])
            )
        )
        active_res = await self.db.execute(active_stmt)
        active_trips = active_res.scalars().all()
        
        if active_trips:
            # Simple conflict check (if dates provided, check overlap)
            # If no dates, just flag as potentially busy
            status = SuitabilityStatus.UNSUITABLE
            reasons.append("Vehicle is currently assigned to an active trip.")
            
        # Check Maintenance
        maint_stmt = select(MaintenanceRecord).where(
            and_(
                MaintenanceRecord.vehicle_id == vehicle.id,
                MaintenanceRecord.status.in_([MaintenanceStatus.SCHEDULED, MaintenanceStatus.STARTED])
            )
        )
        maint_res = await self.db.execute(maint_stmt)
        maint_tasks = maint_res.scalars().all()
        
        if maint_tasks:
            # Again, simple check
            for task in maint_tasks:
                if task.status == MaintenanceStatus.STARTED:
                    status = SuitabilityStatus.UNSUITABLE
                    reasons.append("Vehicle is currently under maintenance.")
                    break
                else:
                    status = SuitabilityStatus.MARGINAL if status != SuitabilityStatus.UNSUITABLE else status
                    if "Vehicle has scheduled maintenance" not in reasons:
                        reasons.append("Vehicle has scheduled maintenance.")

        # Check basic properties
        if vehicle.status.lower() != "active":
            status = SuitabilityStatus.UNSUITABLE
            reasons.append(f"Vehicle status is {vehicle.status}.")

        if not reasons:
            reasons.append("Vehicle is available and suitable for the trip.")
            
        return SuitabilityAssessment(status=status, reasons=reasons)
