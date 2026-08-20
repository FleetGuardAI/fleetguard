import logging
from datetime import datetime, timezone

from dispatchers.event_subscriber import EventSubscriber
from models.operational_event import EventType
from schemas.operational_event import OperationalEventResponse
from infrastructure.uow import SqlAlchemyUnitOfWork
from infrastructure.intelligence.core.orchestrator import GenericIntelligenceOrchestrator
from database import async_session_factory

logger = logging.getLogger("fleetguard.intelligence.fuel_consumer")


class IntelligenceConsumer(EventSubscriber):
    """
    Subscribes to operational events that might trigger Intelligence Engine execution.
    """
    name = "fuel_intelligence_consumer" # DO NOT CHANGE to preserve consumer group offsets
    
    event_filter = frozenset({
        EventType.TRIP_COMPLETED,
        EventType.FUEL_FILLED
    })

    def __init__(self, orchestrator: GenericIntelligenceOrchestrator) -> None:
        self.orchestrator = orchestrator

    async def handle(self, event: OperationalEventResponse) -> None:
        """
        Processes events by opening a single UoW and executing the intelligence pipeline.
        """
        logger.info(f"IntelligenceConsumer received {event.event_type.name} for Entity {event.entity_id}")
        
        uow = SqlAlchemyUnitOfWork(async_session_factory)
        async with uow:
            occurred_at = event.occurred_at
            if isinstance(occurred_at, str):
                try:
                    occurred_at = datetime.fromisoformat(occurred_at)
                except ValueError:
                    occurred_at = datetime.now(timezone.utc)
                        
                # Event processing must either fully succeed or fail the transaction.
                await self.orchestrator.execute_from_event(
                    uow=uow,
                    event_type=event.event_type,
                    entity_id=event.entity_id,
                    payload=event.payload or {},
                    occurred_at=occurred_at
                )
                await uow.commit()

# Backward compatibility alias
FuelIntelligenceConsumer = IntelligenceConsumer
