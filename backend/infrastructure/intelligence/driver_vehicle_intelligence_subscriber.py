"""
FleetGuard — Driver Vehicle Intelligence Event Subscriber
Consumes LOCATION_UPDATED events to drive Phase 4 deterministic intelligence.
"""

import logging
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from dispatchers.event_subscriber import EventSubscriber
from models.operational_event import EventType
from schemas.operational_event import OperationalEventResponse
from services.driver_vehicle_intelligence import DriverVehicleIntelligenceService

logger = logging.getLogger(__name__)

class DriverVehicleIntelligenceSubscriber(EventSubscriber):
    name = "driver_vehicle_intelligence"
    event_filter = frozenset({EventType.LOCATION_UPDATED})
    
    def __init__(self, async_session_maker):
        self.async_session_maker = async_session_maker

    async def handle(self, event: OperationalEventResponse) -> None:
        vehicle_id = event.payload.get("vehicle_id")
        company_id = event.payload.get("company_id")
        
        if not vehicle_id or not company_id:
            logger.warning(f"LOCATION_UPDATED event {event.id} missing vehicle/company_id")
            return

        async with self.async_session_maker() as session:
            try:
                service = DriverVehicleIntelligenceService(session)
                signals = await service.compute_signals(vehicle_id, company_id)
                now = datetime.now(timezone.utc)
                await service.process_conditions(signals, now)
                await session.commit()
            except Exception as e:
                logger.error(f"Intelligence subscriber error for event {event.id}: {e}")
                await session.rollback()
                raise
