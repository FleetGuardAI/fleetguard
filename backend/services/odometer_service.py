import logging
from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from models.vehicle_domain import Vehicle

logger = logging.getLogger("fleetguard.odometer_service")

class OdometerService:
    @staticmethod
    def update_odometer_if_valid(vehicle: Vehicle, new_odometer: float, timestamp: datetime) -> bool:
        """
        Updates the vehicle's current odometer if the reading is valid and newer.
        Returns True if updated, False otherwise.
        """
        if new_odometer is None or new_odometer < 0:
            return False
            
        # If we have a previous update timestamp, ensure this reading is newer or equal
        if vehicle.last_odometer_update_at and timestamp < vehicle.last_odometer_update_at:
            logger.debug(f"Ignoring stale odometer reading for vehicle {vehicle.id} (timestamp: {timestamp} < {vehicle.last_odometer_update_at})")
            return False

        # Only move forward (no rollback) unless it's the first reading
        if vehicle.current_odometer is not None and new_odometer < vehicle.current_odometer:
            logger.warning(f"Ignoring odometer rollback for vehicle {vehicle.id} ({vehicle.current_odometer} -> {new_odometer})")
            return False
            
        vehicle.current_odometer = new_odometer
        vehicle.last_odometer_update_at = timestamp
        return True
