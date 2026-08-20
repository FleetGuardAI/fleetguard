import pytest
from models.operational_event import EventType
from infrastructure.intelligence.core.registry import HandlerRegistry
from infrastructure.intelligence.core.handler import IntelligenceHandler

class MockHandlerA(IntelligenceHandler):
    @property
    def name(self) -> str:
        return "handler_a"
    def supports(self, event_type: EventType) -> bool:
        return event_type == EventType.TRIP_COMPLETED
    async def check_relevance(self, uow, event_type, entity_id, payload, occurred_at):
        return []
    async def process(self, uow, context):
        pass

class MockHandlerB(IntelligenceHandler):
    @property
    def name(self) -> str:
        return "handler_b"
    def supports(self, event_type: EventType) -> bool:
        return event_type in (EventType.TRIP_COMPLETED, EventType.FUEL_FILLED)
    async def check_relevance(self, uow, event_type, entity_id, payload, occurred_at):
        return []
    async def process(self, uow, context):
        pass

def test_handler_registration():
    registry = HandlerRegistry()
    registry.register(MockHandlerA())
    
    handlers = registry.get_handlers(EventType.TRIP_COMPLETED)
    assert len(handlers) == 1
    assert handlers[0].name == "handler_a"

def test_duplicate_registration_protection():
    registry = HandlerRegistry()
    registry.register(MockHandlerA())
    registry.register(MockHandlerA()) # Duplicate
    
    handlers = registry.get_handlers(EventType.TRIP_COMPLETED)
    assert len(handlers) == 1

def test_multiple_handlers_and_deterministic_ordering():
    registry = HandlerRegistry()
    registry.register(MockHandlerA())
    registry.register(MockHandlerB())
    
    handlers = registry.get_handlers(EventType.TRIP_COMPLETED)
    assert len(handlers) == 2
    assert handlers[0].name == "handler_a"
    assert handlers[1].name == "handler_b"
    
    # FUEL_FILLED should only return HandlerB
    fuel_handlers = registry.get_handlers(EventType.FUEL_FILLED)
    assert len(fuel_handlers) == 1
    assert fuel_handlers[0].name == "handler_b"

def test_event_matching_no_handlers():
    registry = HandlerRegistry()
    registry.register(MockHandlerA())
    
    # TRIP_STARTED is not supported by MockHandlerA
    handlers = registry.get_handlers(EventType.TRIP_STARTED)
    assert len(handlers) == 0
