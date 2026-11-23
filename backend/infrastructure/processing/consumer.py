"""
FleetGuard — Processing Consumer
"""

import logging

from dispatchers.event_subscriber import EventSubscriber
from models.operational_event import EventType
from schemas.operational_event import OperationalEventResponse
from infrastructure.processing.service import ProcessingService

logger = logging.getLogger("fleetguard.infrastructure.processing.consumer")


class ProcessingConsumer(EventSubscriber):
    """
    Subscribes to VALIDATION_SUCCEEDED events and direct domain operational events.
    Triggers domain processing via ProcessingService.
    """
    name = "processing_consumer"
    
    event_filter = frozenset({
        EventType.VALIDATION_SUCCEEDED,
        # Trip
        EventType.TRIP_CREATED,
        EventType.TRIP_STARTED,
        EventType.TRIP_PAUSED,
        EventType.TRIP_RESUMED,
        EventType.TRIP_COMPLETED,
        EventType.TRIP_CANCELLED,
        EventType.TRIP_DRIVER_ASSIGNED,
        EventType.TRIP_VEHICLE_ASSIGNED,
        # Vehicle
        EventType.VEHICLE_REGISTERED,
        EventType.VEHICLE_ASSIGNED,
        EventType.VEHICLE_UNASSIGNED,
        EventType.VEHICLE_STATUS_CHANGED,
        # Driver
        EventType.DRIVER_REGISTERED,
        EventType.DRIVER_ASSIGNED,
        EventType.DRIVER_UNASSIGNED,
        EventType.DRIVER_STATUS_CHANGED,
        # Maintenance
        EventType.MAINTENANCE_CREATED,
        EventType.MAINTENANCE_SCHEDULED,
        EventType.MAINTENANCE_STARTED,
        EventType.MAINTENANCE_COMPLETED,
        EventType.MAINTENANCE_CANCELLED,
        EventType.MAINTENANCE_OVERDUE,
        EventType.MAINTENANCE_TASK_ADDED,
        EventType.MAINTENANCE_TASK_COMPLETED,
        # Tyre
        EventType.TYRE_REGISTERED,
        EventType.TYRE_INSTALLED,
        EventType.TYRE_REMOVED,
        EventType.TYRE_ROTATED,
        EventType.TYRE_REPAIRED,
        EventType.TYRE_RETREADED,
        EventType.TYRE_RETIRED,
        EventType.TYRE_REPLACED,
        EventType.TYRE_PRESSURE_ALERT,
        # Asset
        EventType.ASSET_REGISTERED,
        EventType.ASSET_INSTALLED,
        EventType.ASSET_REMOVED,
        EventType.ASSET_CALIBRATED,
        EventType.ASSET_REPAIRED,
        EventType.ASSET_REPLACED,
        EventType.ASSET_RETIRED,
        # Expense
        EventType.EXPENSE_ADDED,
        EventType.EXPENSE_APPROVED,
        EventType.EXPENSE_REJECTED,
    })

    def __init__(self, processing_service: ProcessingService) -> None:
        self.processing_service = processing_service

    async def handle(self, event: OperationalEventResponse) -> None:
        """
        Extract the original event ID from VALIDATION_SUCCEEDED or direct domain event,
        and trigger the processing service.
        """
        if event.event_type == EventType.VALIDATION_SUCCEEDED:
            original_event_id_str = event.entity_id
        else:
            original_event_id_str = str(event.id)

        if not original_event_id_str:
            logger.error(f"{event.event_type.value} event missing entity_id or id")
            return
            
        logger.info(f"ProcessingConsumer received {event.event_type.value} -> processing Event {original_event_id_str}")
        
        await self.processing_service.process(original_event_id_str)
