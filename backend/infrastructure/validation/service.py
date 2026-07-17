"""
FleetGuard — Validation Service
"""

import logging
from typing import Callable

from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.validation.engine import ValidationEngine
from schemas.operational_event import OperationalEventCreate, OperationalEventResponse, EventType, EntityType, CaptureMethod
from schemas.evidence_package import EvidencePackage
from schemas.validation_result import ValidationVerdict
from schemas.validation_sdk import ValidationContext
from services.operational_event_service import OperationalEventService
from repositories.evidence_repository import EvidenceRepository

logger = logging.getLogger("fleetguard.infrastructure.validation.service")


class ValidationService:
    """
    Orchestrates the evaluation of an Evidence Package.
    Fetches required state, runs the Validation Engine, and persists
    the resulting trust decision as a new Operational Event.
    """
    def __init__(
        self,
        db_session_factory: Callable[[], AsyncSession],
        engine: ValidationEngine,
        event_service_factory: Callable[[AsyncSession], OperationalEventService]
    ) -> None:
        self.db_session_factory = db_session_factory
        self.engine = engine
        self.event_service_factory = event_service_factory

    async def process(self, original_event_id: str, package: EvidencePackage) -> None:
        """
        Process the Evidence Package.
        Fetches the original event and evidence records from the DB,
        evaluates them, and generates a new VALIDATION_* event.
        """
        async with self.db_session_factory() as db:
            event_service = self.event_service_factory(db)
            evidence_repo = EvidenceRepository(db)
            
            try:
                # 1. Fetch original event
                event_response: OperationalEventResponse = await event_service.get_event(original_event_id)
                if not event_response:
                    logger.error(f"Cannot validate: Original event {original_event_id} not found.")
                    return
                
                # 2. Fetch all evidence records for this event and convert to dicts
                evidence_records_models = await evidence_repo.get_for_event(event_response.id)
                evidence_records = [
                    {"id": str(e.id), "evidence_type": e.evidence_type, "source": e.source, "raw_data": e.raw_data}
                    for e in evidence_records_models
                ]
                
                # Build context
                context = ValidationContext(
                    event=event_response,
                    evidence_package=package,
                    evidence_records=evidence_records,
                    business_state={}, # Fetch business state here if needed
                    configuration={}
                )
                
                # 3. Evaluate using the Validation Engine
                validation_result = await self.engine.evaluate(context)
                
                # 4. Map verdict to event type
                target_event_type = None
                if validation_result.verdict == ValidationVerdict.VERIFIED:
                    target_event_type = EventType.VALIDATION_SUCCEEDED
                elif validation_result.verdict == ValidationVerdict.REJECTED:
                    target_event_type = EventType.VALIDATION_FAILED
                elif validation_result.verdict == ValidationVerdict.DISPUTED:
                    target_event_type = EventType.VALIDATION_DISPUTED
                
                # 5. Emit new operational event
                validation_event_payload = OperationalEventCreate(
                    event_type=target_event_type,
                    entity_type=EntityType.OPERATIONAL_EVENT,
                    entity_id=str(event_response.id),
                    capture_method=CaptureMethod.SYSTEM,
                    created_by="system:validation-engine",
                    payload=validation_result.model_dump(mode="json"),
                    notes=f"Validation resulted in {validation_result.verdict.value}."
                )
                
                await event_service.create_event(validation_event_payload)
                await db.commit()
                
                logger.info(f"Validation completed for Event {original_event_id}. Emitted {target_event_type.value}.")
                
            except Exception as e:
                logger.exception(f"ValidationService failed to process event {original_event_id}: {e}")
                await db.rollback()
