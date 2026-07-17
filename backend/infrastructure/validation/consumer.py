"""
FleetGuard — Validation Consumer
"""

import logging

from dispatchers.event_subscriber import EventSubscriber
from models.operational_event import EventType
from schemas.operational_event import OperationalEventResponse
from schemas.evidence_package import EvidencePackage
from infrastructure.validation.service import ValidationService

logger = logging.getLogger("fleetguard.infrastructure.validation.consumer")


class ValidationConsumer(EventSubscriber):
    """
    Subscribes to EVIDENCE_PACKAGE_READY events.
    Extracts the payload and triggers the ValidationService.
    """
    name = "validation_consumer"
    
    event_filter = frozenset({EventType.EVIDENCE_PACKAGE_READY})

    def __init__(self, validation_service: ValidationService) -> None:
        self.validation_service = validation_service

    async def handle(self, event: OperationalEventResponse) -> None:
        """
        Extract the Evidence Package and process it.
        """
        original_event_id_str = event.entity_id
        if not original_event_id_str:
            logger.error("EVIDENCE_PACKAGE_READY event missing entity_id")
            return
            
        try:
            payload = event.payload or {}
            package = EvidencePackage(**payload)
        except Exception as e:
            logger.error(f"Failed to parse EvidencePackage from event {event.id}: {e}")
            return

        logger.info(f"ValidationConsumer received Evidence Package for Event {original_event_id_str}")
        
        await self.validation_service.process(original_event_id_str, package)
