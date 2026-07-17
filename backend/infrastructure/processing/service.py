"""
FleetGuard — Processing Service
"""

import time
import logging
from typing import Callable

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from infrastructure.processing.domain_router import DomainRouter
from models.operational_event import OperationalEvent, EventType
from schemas.operational_event import OperationalEventCreate, EntityType, CaptureMethod
from schemas.processing_result import ProcessingResult, ProcessingStatus
from models.processing_record import ProcessingStatus as RecordStatus
from repositories.processing_repository import ProcessingRepository
from services.operational_event_service import OperationalEventService
from infrastructure.uow import SqlAlchemyUnitOfWork, AbstractUnitOfWork

logger = logging.getLogger("fleetguard.infrastructure.processing.service")

class ProcessingService:
    """
    Orchestrates the execution of Business Domains for a given validated Operational Event.
    Emits a PROCESSING_COMPLETED or PROCESSING_FAILED event without mutating original state.
    """
    def __init__(
        self,
        db_session_factory: Callable[[], AsyncSession],
        router: DomainRouter,
        event_service_factory: Callable[[AbstractUnitOfWork], OperationalEventService]
    ) -> None:
        self.db_session_factory = db_session_factory
        self.router = router
        self.event_service_factory = event_service_factory

    async def process(self, original_event_id: str) -> None:
        """
        Process the validated Operational Event.
        Fetches the event, resolves domains, invokes them, records state, 
        and emits the outcome.
        """
        start_time = time.perf_counter()
        
        async with SqlAlchemyUnitOfWork(self.db_session_factory) as uow:
            # 1. Fetch original ORM event
            orm_event = await uow.repositories.operational_event.get_event_by_id(original_event_id)
            
            if not orm_event:
                logger.error(f"Cannot process: Original event {original_event_id} not found.")
                return
                
            # Create Processing Record for tracking DB state
            record = await uow.repositories.processing.create_record(
                event_id=str(orm_event.id), 
                status=RecordStatus.PROCESSING
            )
            await uow.commit() # Commit the 'PROCESSING' status immediately

        # 2. Main Processing Transaction
        # We start a NEW uow session so the Business Domain state changes and Idempotency record 
        # are committed entirely atomically. If a domain fails, we rollback this session without 
        # rolling back the ProcessingRecord's initial 'PROCESSING' state.
        async with SqlAlchemyUnitOfWork(self.db_session_factory) as uow:
            from infrastructure.idempotency.service import IdempotencyService
            idempotency_service = IdempotencyService(uow)
            
            # Re-fetch event inside the new session for relationships/routing
            event_service = self.event_service_factory(uow)
            event_response = await event_service.get_event(original_event_id)
            
            # Re-fetch ORM event for domains
            orm_event = await uow.repositories.operational_event.get_event_by_id(original_event_id)
            
            domain_services = self.router.resolve(event_response, uow)
            
            processed_domains = []
            successful_domains = []
            failed_domains = []
            skipped_domains = []
            
            for service in domain_services:
                processed_domains.append(service.__class__.__name__)
                
            if not domain_services:
                logger.info(f"Processing Engine: No domains registered for {orm_event.event_type.value} event {orm_event.id}")
                has_failure = False
            else:
                # Invoke Domains in sequence
                has_failure = False
                for service in domain_services:
                    domain_name = service.__class__.__name__
                    
                    if has_failure:
                        # If a domain fails, skip subsequent domains to avoid partial corruption
                        skipped_domains.append(domain_name)
                        continue
                        
                    # Idempotency Check
                    try:
                        already_processed = await idempotency_service.has_processed(
                            event_id=str(orm_event.id), 
                            domain_name=domain_name
                        )
                        
                        if already_processed:
                            logger.info(f"Idempotency skip: Domain {domain_name} already processed event {orm_event.id}")
                            skipped_domains.append(f"{domain_name} (Idempotency Skip)")
                            successful_domains.append(domain_name) # Consider it successfully handled
                            continue
                            
                        logger.debug(f"Invoking {domain_name} for event {orm_event.id}")
                        await service.apply_verified_event(orm_event)
                        
                        # Mark Idempotency
                        await idempotency_service.mark_processed(
                            event_id=str(orm_event.id),
                            domain_name=domain_name,
                            result="SUCCESS"
                        )
                        successful_domains.append(domain_name)
                    except Exception as e:
                        logger.exception(f"Domain {domain_name} failed to process event {orm_event.id}: {e}")
                        failed_domains.append({
                            "domain": domain_name,
                            "error": str(e)
                        })
                        has_failure = True

            # If there was a failure in the domain execution, we MUST rollback the Business Domain 
            # transaction to ensure we don't save partial state for the failed domain.
            if has_failure:
                await uow.rollback()
            else:
                # Commit Business Domain changes and Idempotency records atomically
                await uow.commit()

        # 3. Finalize ProcessingRecord and emit Completion/Failure Event
        execution_ms = int((time.perf_counter() - start_time) * 1000)
        final_status = ProcessingStatus.FAILED if has_failure else ProcessingStatus.COMPLETED

        async with SqlAlchemyUnitOfWork(self.db_session_factory) as final_uow:
            event_service = self.event_service_factory(final_uow)
            
            # Build structured ProcessingResult
            processing_result = ProcessingResult(
                processed_domains=processed_domains,
                successful_domains=successful_domains,
                failed_domains=failed_domains,
                skipped_domains=skipped_domains,
                processing_status=final_status,
                processing_time_ms=execution_ms,
                errors=[],
                metadata={}
            )
            
            # Emit new operational event
            target_event_type = EventType.PROCESSING_COMPLETED if final_status == ProcessingStatus.COMPLETED else EventType.PROCESSING_FAILED
            
            processing_event_payload = OperationalEventCreate(
                event_type=target_event_type,
                entity_type=EntityType.OPERATIONAL_EVENT,
                entity_id=original_event_id,
                capture_method=CaptureMethod.SYSTEM,
                created_by="system:processing-engine",
                payload=processing_result.model_dump(mode="json"),
                notes=f"Processing resulted in {final_status.value}."
            )
            
            await event_service.create_event(processing_event_payload)
            
            # Update legacy ProcessingRecord DB state
            from datetime import datetime, timezone
            await final_uow.repositories.processing.update_record(
                record_id=record.id,
                status=RecordStatus.FAILED if has_failure else RecordStatus.COMPLETED,
                domains_invoked=successful_domains,
                domains_failed=failed_domains,
                completed_at=datetime.now(timezone.utc),
                execution_ms=execution_ms
            )
            
            await final_uow.commit()
            
            logger.info(
                f"ProcessingEngine finished event {original_event_id} ({final_status.value}) in {execution_ms}ms. "
                f"Success: {successful_domains}, Failed: {len(failed_domains)}, Skipped: {skipped_domains}"
            )
