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
    Subscribes to VALIDATION_SUCCEEDED events.
    Extracts the original event ID and triggers the ProcessingService.
    """
    name = "processing_consumer"
    
    event_filter = frozenset({EventType.VALIDATION_SUCCEEDED})

    def __init__(self, processing_service: ProcessingService) -> None:
        self.processing_service = processing_service

    async def handle(self, event: OperationalEventResponse) -> None:
        """
        Extract the original event ID from VALIDATION_SUCCEEDED and process it.
        """
        original_event_id_str = event.entity_id
        if not original_event_id_str:
            logger.error("VALIDATION_SUCCEEDED event missing entity_id")
            return
            
        logger.info(f"ProcessingConsumer received VALIDATION_SUCCEEDED for Event {original_event_id_str}")
        
        await self.processing_service.process(original_event_id_str)
