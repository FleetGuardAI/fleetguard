import logging
from datetime import datetime

from infrastructure.uow import AbstractUnitOfWork
from models.operational_event import EventType
from infrastructure.intelligence.core.registry import HandlerRegistry

logger = logging.getLogger("fleetguard.intelligence.generic_orchestrator")

class GenericIntelligenceOrchestrator:
    """
    Generic Intelligence Orchestrator that routes operational events to registered domain handlers.
    Currently maintains a single Unit of Work across all handlers (as per V1 semantics).
    """
    def __init__(self, registry: HandlerRegistry):
        self._registry = registry
        
    async def execute_from_event(self, uow: AbstractUnitOfWork, event_type: EventType, entity_id: str, payload: dict, occurred_at: datetime) -> None:
        """
        Receives an OperationalEvent and dispatches it to relevant domain handlers.
        """
        handlers = self._registry.get_handlers(event_type)
        if not handlers:
            logger.debug(f"No intelligence handlers registered for {event_type.name}")
            return
            
        for handler in handlers:
            # Check relevance and fetch domain context
            contexts = await handler.check_relevance(
                uow=uow,
                event_type=event_type,
                entity_id=entity_id,
                payload=payload,
                occurred_at=occurred_at
            )
            
            if not contexts:
                continue
                
            for context in contexts:
                try:
                    await handler.process(uow, context)
                except Exception as e:
                    logger.error(f"Handler {handler.name} failed during process for event {event_type.name}: {e}")
                    raise # Rethrow to preserve existing transaction / DLQ retry semantics
