"""
Fleet Intelligence Engine - Event Processor
"""

from typing import List
from infrastructure.intelligence.event_processing.models import BaseOperationalEvent
from infrastructure.intelligence.event_processing.correlator import EventCorrelator
from infrastructure.intelligence.event_processing.builder import EvidenceBuilder
from infrastructure.intelligence.orchestrator.base import IntelligenceOrchestrator
from infrastructure.intelligence.orchestrator.models import IntelligenceExecutionResult


class EventProcessor:
    """
    Orchestrates the ingestion of asynchronous events, correlation into transactions,
    conversion to evidence, and synchronous execution of the Intelligence Engine.
    """
    
    def __init__(
        self,
        correlator: EventCorrelator,
        builder: EvidenceBuilder,
        orchestrator: IntelligenceOrchestrator
    ):
        self.correlator = correlator
        self.builder = builder
        self.orchestrator = orchestrator

    def process_event(self, event: BaseOperationalEvent) -> List[IntelligenceExecutionResult]:
        """
        Ingests a new event and immediately returns any IntelligenceExecutionResults
        triggered by newly completed transactions.
        """
        self.correlator.add_event(event)
        
        results = []
        ready_transactions = self.correlator.get_ready_transactions()
        
        for transaction_events in ready_transactions:
            package = self.builder.build_package(transaction_events)
            result = self.orchestrator.execute(package)
            results.append(result)
            
        return results
