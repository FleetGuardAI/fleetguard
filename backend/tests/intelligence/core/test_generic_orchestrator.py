import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from models.operational_event import EventType
from infrastructure.intelligence.core.registry import HandlerRegistry
from infrastructure.intelligence.core.orchestrator import GenericIntelligenceOrchestrator
from infrastructure.intelligence.core.handler import IntelligenceHandler

class MockHandler(IntelligenceHandler):
    def __init__(self, name: str, contexts: list):
        self._name = name
        self.contexts = contexts
        self.processed_contexts = []
        self.process_fails = False
        
    @property
    def name(self) -> str:
        return self._name
        
    def supports(self, event_type: EventType) -> bool:
        return True
        
    async def check_relevance(self, uow, event_type, entity_id, payload, occurred_at):
        return self.contexts
        
    async def process(self, uow, context):
        if self.process_fails:
            raise ValueError("Simulated processing failure")
        self.processed_contexts.append(context)

@pytest.fixture
def uow():
    return AsyncMock()

@pytest.mark.asyncio
async def test_orchestrator_routes_to_relevant_handler(uow):
    registry = HandlerRegistry()
    handler = MockHandler("test_handler", contexts=["context_1"])
    registry.register(handler)
    
    orchestrator = GenericIntelligenceOrchestrator(registry)
    await orchestrator.execute_from_event(
        uow=uow,
        event_type=EventType.TRIP_COMPLETED,
        entity_id="trip_123",
        payload={},
        occurred_at=datetime.now()
    )
    
    assert len(handler.processed_contexts) == 1
    assert handler.processed_contexts[0] == "context_1"

@pytest.mark.asyncio
async def test_orchestrator_handles_irrelevant_events(uow):
    registry = HandlerRegistry()
    # Returns empty contexts list
    handler = MockHandler("test_handler", contexts=[])
    registry.register(handler)
    
    orchestrator = GenericIntelligenceOrchestrator(registry)
    await orchestrator.execute_from_event(
        uow=uow,
        event_type=EventType.TRIP_COMPLETED,
        entity_id="trip_123",
        payload={},
        occurred_at=datetime.now()
    )
    
    assert len(handler.processed_contexts) == 0

@pytest.mark.asyncio
async def test_orchestrator_propagates_unexpected_failures(uow):
    registry = HandlerRegistry()
    handler = MockHandler("test_handler", contexts=["context_1"])
    handler.process_fails = True
    registry.register(handler)
    
    orchestrator = GenericIntelligenceOrchestrator(registry)
    
    with pytest.raises(ValueError, match="Simulated processing failure"):
        await orchestrator.execute_from_event(
            uow=uow,
            event_type=EventType.TRIP_COMPLETED,
            entity_id="trip_123",
            payload={},
            occurred_at=datetime.now()
        )
