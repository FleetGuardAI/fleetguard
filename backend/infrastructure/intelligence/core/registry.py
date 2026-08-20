from typing import List, Dict
from models.operational_event import EventType
from infrastructure.intelligence.core.handler import IntelligenceHandler

class HandlerRegistry:
    """
    Maintains a deterministic list of intelligence domain handlers and matches them to events.
    """
    def __init__(self):
        # Using a list to preserve insertion order (deterministic)
        self._handlers: List[IntelligenceHandler] = []
        
    def register(self, handler: IntelligenceHandler) -> None:
        """
        Registers a handler. Ignores duplicates.
        """
        for existing in self._handlers:
            if existing.name == handler.name:
                return
        self._handlers.append(handler)
        
    def get_handlers(self, event_type: EventType) -> List[IntelligenceHandler]:
        """
        Returns all registered handlers that support the given event type.
        """
        return [h for h in self._handlers if h.supports(event_type)]
