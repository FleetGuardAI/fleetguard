"""
FleetGuard — Evidence Orchestrator
"""

import asyncio
import logging
from typing import Callable

from sqlalchemy.ext.asyncio import AsyncSession

from dispatchers.event_subscriber import EventSubscriber
from models.operational_event import EventType, EntityType, CaptureMethod
from schemas.operational_event import OperationalEventCreate, OperationalEventResponse
from services.operational_event_service import OperationalEventService
from services.evidence_service import EvidenceService
from schemas.evidence import EvidenceCreate

from infrastructure.evidence.registry import EvidenceProviderRegistry
from schemas.evidence_sdk import EvidenceRequest, EvidenceResult, ProviderStatus
from infrastructure.evidence.builder import EvidencePackageBuilder
from models.evidence import EvidenceType

logger = logging.getLogger("fleetguard.infrastructure.evidence.orchestrator")


class EvidenceOrchestrator(EventSubscriber):
    """
    Coordinates Evidence Collection for Operational Events.
    Triggers applicable Evidence Providers concurrently, handles timeouts,
    builds an Evidence Package, and emits EVIDENCE_PACKAGE_READY.
    """
    name = "evidence_orchestrator"
    
    # Subscribe to business events that might require evidence.
    event_filter = frozenset({EventType.FUEL_FILLED, EventType.DOCUMENT_UPLOADED})

    def __init__(
        self,
        session_factory: Callable[[], AsyncSession],
        registry: EvidenceProviderRegistry,
        event_service_factory: Callable[[AsyncSession], OperationalEventService],
        provider_timeout_seconds: float = 10.0
    ) -> None:
        self.session_factory = session_factory
        self.registry = registry
        self.event_service_factory = event_service_factory
        self.provider_timeout_seconds = provider_timeout_seconds

    async def handle(self, event: OperationalEventResponse) -> None:
        """
        Determine applicable providers, execute them concurrently with a timeout,
        persist the collected evidence, build the Evidence Package, and emit EVIDENCE_PACKAGE_READY.
        """
        request = EvidenceRequest(event=event)
        
        applicable_providers = []
        for provider in self.registry.list():
            try:
                if await provider.applies_to(request):
                    applicable_providers.append(provider)
            except Exception as e:
                logger.error(f"Error checking applicability of provider '{provider.name}': {e}")
        
        builder = EvidencePackageBuilder(event.id)
        for p in applicable_providers:
            builder.expect_provider(p.name)

        if applicable_providers:
            logger.info(f"EvidenceOrchestrator triggering {len(applicable_providers)} providers for Event {event.id}")

            async def _run_with_timeout(provider) -> EvidenceResult:
                try:
                    return await asyncio.wait_for(
                        provider.collect(request),
                        timeout=self.provider_timeout_seconds
                    )
                except asyncio.TimeoutError:
                    logger.warning(f"Provider {provider.name} timed out for Event {event.id}")
                    return EvidenceResult(
                        status=ProviderStatus.TIMED_OUT, 
                        provider_name=provider.name,
                        evidence_type=EvidenceType.OTHER,
                        errors=["Timeout"]
                    )
                except Exception as e:
                    logger.exception(f"Provider {provider.name} failed for Event {event.id}: {e}")
                    return EvidenceResult(
                        status=ProviderStatus.FAILED, 
                        provider_name=provider.name,
                        evidence_type=EvidenceType.OTHER,
                        errors=[str(e)]
                    )

            # Run concurrently
            tasks = [_run_with_timeout(p) for p in applicable_providers]
            results = await asyncio.gather(*tasks)
            
            # Persist collected evidence and record results
            async with self.session_factory() as db:
                evidence_svc = EvidenceService(db)
                for res in results:
                    evidence_id = None
                    if res.status == ProviderStatus.COMPLETED:
                        try:
                            # Provider returned raw evidence. Orchestrator handles persistence.
                            create_payload = EvidenceCreate(
                                evidence_type=res.evidence_type,
                                source=res.provider_name,
                                summary=res.summary or f"Evidence from {res.provider_name}",
                                details=res.details,
                                raw_data=res.raw_data
                            )
                            ev_record = await evidence_svc.add_evidence(event.id, create_payload)
                            evidence_id = ev_record.id
                        except Exception as e:
                            logger.error(f"Failed to persist evidence from {res.provider_name}: {e}")
                            res.status = ProviderStatus.FAILED
                            res.errors.append(f"Persistence failed: {e}")
                    
                    builder.record_result(res, evidence_id=evidence_id)
                
                await db.commit()

        package = builder.build()
        logger.info(f"Evidence Package built for Event {event.id} with status {package.collection_status}")

        async with self.session_factory() as db:
            event_service = self.event_service_factory(db)
            
            completion_payload = OperationalEventCreate(
                event_type=EventType.EVIDENCE_PACKAGE_READY,
                entity_type=EntityType.OPERATIONAL_EVENT,
                entity_id=str(event.id),
                capture_method=CaptureMethod.SYSTEM,
                created_by="system:evidence-framework",
                payload=package.model_dump(mode="json"),
                notes=f"Evidence package ready (Status: {package.collection_status})"
            )
            
            await event_service.create_event(completion_payload)
            await db.commit()
