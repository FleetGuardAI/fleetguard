import logging
from datetime import datetime
from typing import Optional

from infrastructure.uow import AbstractUnitOfWork
from models.operational_event import EventType

from infrastructure.intelligence.core.registry import HandlerRegistry
from infrastructure.intelligence.core.orchestrator import GenericIntelligenceOrchestrator
from infrastructure.intelligence.fuel_domain.handler import FuelIntelligenceHandler

logger = logging.getLogger("fleetguard.intelligence.fuel_orchestrator")


class FuelIntelligenceOrchestrator(GenericIntelligenceOrchestrator):
    """
    Backward-compatible alias/wrapper for the Generic Intelligence Orchestrator.
    It automatically registers the FuelIntelligenceHandler to preserve existing behavior.
    """
    def __init__(self):
        registry = HandlerRegistry()
        registry.register(FuelIntelligenceHandler())
        super().__init__(registry=registry)
