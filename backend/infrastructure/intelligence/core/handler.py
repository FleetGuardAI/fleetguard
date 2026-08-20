import logging
from abc import ABC, abstractmethod
from typing import Any, List
from datetime import datetime

from infrastructure.uow import AbstractUnitOfWork
from models.operational_event import EventType

class IntelligenceHandler(ABC):
    """
    Abstract base class for all domain-specific intelligence handlers.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Returns the unique name of the handler (e.g. 'fuel_intelligence_handler')"""
        pass
        
    @abstractmethod
    def supports(self, event_type: EventType) -> bool:
        """
        Determines if this handler is interested in this event type.
        """
        pass
        
    @abstractmethod
    async def check_relevance(
        self, 
        uow: AbstractUnitOfWork, 
        event_type: EventType, 
        entity_id: str, 
        payload: dict, 
        occurred_at: datetime
    ) -> List[Any]:
        """
        Checks if the event is relevant and extracts necessary domain entities.
        Returns a list of contextual entities (e.g. Trips) to process.
        """
        pass
        
    @abstractmethod
    async def process(self, uow: AbstractUnitOfWork, context: Any) -> None:
        """
        Executes the domain-specific intelligence pipeline for a given context entity.
        Must be idempotent and safe to retry.
        """
        pass
