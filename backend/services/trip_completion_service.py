import asyncio
import logging
from sqlalchemy import select, and_, asc
from sqlalchemy.ext.asyncio import AsyncSession
from models.trip_domain import Trip
from models.location_tracking import DriverLocation
from models.fuel_log import FuelLog
from models.fuel_domain import FuelTransaction, FuelTransactionType
from infrastructure.intelligence.route_domain.checks.deviation import haversine_distance

logger = logging.getLogger(__name__)

class TripCompletionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    @classmethod
    async def run_telemetry_finalization_task(cls, trip_id: int):
        """Safe wrapper for BackgroundTasks to manage its own DB session."""
        from database import async_session_factory
        async with async_session_factory() as session:
            svc = cls(session)
            try:
                await svc.finalize_trip_telemetry(trip_id)
            except Exception as e:
                logger.exception(f"Unexpected crash in run_telemetry_finalization_task for trip {trip_id}: {e}")

    async def finalize_trip_telemetry(self, trip_id: int):
        """
        Calculates canonical GPS distance and fuel consumption for a completed trip.
        Must be called during the trip completion lifecycle.
        """
        trip = await self.db.get(Trip, trip_id)
        if not trip:
            return

        if trip.actual_start_time and trip.actual_end_time:
            # 1. GPS Distance Calculation
            try:
                stmt_loc = (
                    select(DriverLocation)
                    .where(
                        and_(
                            DriverLocation.driver_id == trip.driver_id,
                            DriverLocation.company_id == trip.company_id,
                            DriverLocation.timestamp >= trip.actual_start_time,
                            DriverLocation.timestamp <= trip.actual_end_time
                        )
                    )
                    .order_by(asc(DriverLocation.timestamp))
                )
                loc_result = await self.db.execute(stmt_loc)
                locations = loc_result.scalars().all()

                if locations and len(locations) > 1:
                    total_distance_km = 0.0
                    prev_loc = None
                    
                    for loc in locations:
                        # Filter invalid GPS
                        if abs(loc.latitude) < 0.1 and abs(loc.longitude) < 0.1:
                            continue
                        if loc.accuracy and loc.accuracy > 200: # Ignore low accuracy
                            continue
                        
                        if prev_loc:
                            # Haversine distance is in meters -> convert to km
                            dist_m = haversine_distance(
                                prev_loc.latitude, prev_loc.longitude,
                                loc.latitude, loc.longitude
                            )
                            dist_km = dist_m / 1000.0
                            # Filter duplicates and extreme jumps (e.g. > 160 km/h)
                            time_diff_hours = (loc.timestamp - prev_loc.timestamp).total_seconds() / 3600.0
                            if time_diff_hours > 0:
                                speed_kmh = dist_km / time_diff_hours
                                if 0 < dist_km < 1000 and speed_kmh < 160: # Max 160 km/h
                                    total_distance_km += dist_km
                                    prev_loc = loc
                                elif dist_km == 0:
                                    prev_loc = loc
                        else:
                            prev_loc = loc

                    # Only update if we successfully calculated a distance
                    if total_distance_km > 0:
                        trip.actual_distance = total_distance_km
                elif not locations:
                    # If no telemetry, distance cannot be grounded
                    if trip.actual_distance is None:
                        trip.actual_distance = None
            except Exception as e:
                logger.error(f"GPS aggregation failed for trip {trip_id}: {e}")

            # 2. Fuel Consumption Calculation
            try:
                stmt_fuel = (
                    select(FuelLog)
                    .where(
                        and_(
                            FuelLog.vehicle_id == trip.vehicle_id,
                            FuelLog.timestamp >= trip.actual_start_time,
                            FuelLog.timestamp <= trip.actual_end_time
                        )
                    )
                    .order_by(asc(FuelLog.timestamp))
                )
                fuel_result = await self.db.execute(stmt_fuel)
                fuel_logs = fuel_result.scalars().all()
                
                if fuel_logs and len(fuel_logs) > 1:
                    start_level = fuel_logs[0].filtered_level
                    end_level = fuel_logs[-1].filtered_level
                    
                    # We must account for legitimate refuels during the trip
                    stmt_tx = (
                        select(FuelTransaction)
                        .where(
                            and_(
                                FuelTransaction.vehicle_id == trip.vehicle_id,
                                FuelTransaction.company_id == trip.company_id,
                                FuelTransaction.transaction_type == FuelTransactionType.FILL,
                                FuelTransaction.timestamp >= trip.actual_start_time,
                                FuelTransaction.timestamp <= trip.actual_end_time
                            )
                        )
                    )
                    tx_result = await self.db.execute(stmt_tx)
                    refuels = tx_result.scalars().all()
                    total_refuel = sum(t.amount_liters for t in refuels)
                    
                    # Consumed = Start - End + Added
                    consumed = start_level - end_level + total_refuel
                    
                    if consumed > 0:
                        trip.actual_fuel_liters = consumed
                    else:
                        if trip.actual_fuel_liters is None:
                            trip.actual_fuel_liters = None
                else:
                    if trip.actual_fuel_liters is None:
                        trip.actual_fuel_liters = None
            except Exception as e:
                logger.error(f"Fuel aggregation failed for trip {trip_id}: {e}")

        await self.db.commit()
