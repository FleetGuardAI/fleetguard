import logging
from datetime import datetime, timezone, timedelta
from typing import Sequence, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.vehicle_domain import Vehicle
from models.notification import Notification, NotificationCategory

logger = logging.getLogger("fleetguard.maintenance_due")

MAINTENANCE_DUE_SOON_KM = 500.0
MAINTENANCE_DUE_SOON_DAYS = 7
MAINTENANCE_OVERDUE_GRACE_KM = 500.0
MAINTENANCE_OVERDUE_GRACE_DAYS = 7

class MaintenanceDueService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def evaluate_vehicle(self, vehicle: Vehicle) -> str:
        # Evaluate by Odometer
        odometer_status = None
        if vehicle.current_odometer and vehicle.last_service_odometer and vehicle.maintenance_interval_km:
            next_service_km = vehicle.last_service_odometer + vehicle.maintenance_interval_km
            remaining_km = next_service_km - vehicle.current_odometer
            
            if remaining_km > MAINTENANCE_DUE_SOON_KM:
                odometer_status = "NOT_DUE"
            elif remaining_km > 0 and remaining_km <= MAINTENANCE_DUE_SOON_KM:
                odometer_status = "DUE_SOON"
            elif remaining_km <= 0 and remaining_km > -MAINTENANCE_OVERDUE_GRACE_KM:
                odometer_status = "DUE"
            else:
                odometer_status = "OVERDUE"
                
        # Evaluate by Date
        date_status = None
        if vehicle.last_service_date and vehicle.maintenance_interval_days:
            next_service_date = vehicle.last_service_date + timedelta(days=vehicle.maintenance_interval_days)
            now = datetime.now(timezone.utc)
            if next_service_date.tzinfo is None:
                next_service_date = next_service_date.replace(tzinfo=timezone.utc)
            
            diff_days = (next_service_date - now).days
            
            if diff_days > MAINTENANCE_DUE_SOON_DAYS:
                date_status = "NOT_DUE"
            elif diff_days > 0 and diff_days <= MAINTENANCE_DUE_SOON_DAYS:
                date_status = "DUE_SOON"
            elif diff_days <= 0 and diff_days > -MAINTENANCE_OVERDUE_GRACE_DAYS:
                date_status = "DUE"
            else:
                date_status = "OVERDUE"

        statuses = [s for s in [odometer_status, date_status] if s is not None]
        if not statuses:
            return "UNKNOWN"
        if "OVERDUE" in statuses:
            return "OVERDUE"
        if "DUE" in statuses:
            return "DUE"
        if "DUE_SOON" in statuses:
            return "DUE_SOON"
        return "NOT_DUE"

    async def sweep_maintenance_status(self, company_id: Optional[int] = None):
        query = select(Vehicle).where(Vehicle.status == 'ACTIVE')
        if company_id is not None:
            query = query.where(Vehicle.company_id == company_id)
        result = await self.db.execute(query)
        vehicles = result.scalars().all()
        
        for vehicle in vehicles:
            new_status = await self.evaluate_vehicle(vehicle)
            
            if new_status != vehicle.maintenance_status:
                logger.info(f"Vehicle {vehicle.registration_number} status changed from {vehicle.maintenance_status} to {new_status}")
                if new_status in ["DUE_SOON", "DUE", "OVERDUE"]:
                    notif = Notification(
                        category=NotificationCategory.VEHICLE,
                        title=f"Maintenance {new_status}: {vehicle.registration_number}",
                        description=f"Vehicle {vehicle.registration_number} is now {new_status} for maintenance.",
                        company_id=vehicle.company_id
                    )
                    self.db.add(notif)
                
                vehicle.maintenance_status = new_status
                
        await self.db.commit()
