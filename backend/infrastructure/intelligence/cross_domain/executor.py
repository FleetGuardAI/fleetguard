"""
Fleet Intelligence Engine - Cross-Domain Executor
"""

import time
import logging
import traceback
from typing import List, Dict

from infrastructure.intelligence.domain_risk.models import DomainRiskProfile
from infrastructure.intelligence.cross_domain.models import FleetInsight, FleetInsightCollection
from infrastructure.intelligence.cross_domain.registry import CrossDomainRegistry


logger = logging.getLogger(__name__)


class CrossDomainExecutor:
    """
    Executes Cross-Domain Analyzers against a collection of DomainRiskProfiles.
    Ensures deterministic execution and failure isolation.
    """
    def __init__(self, registry: CrossDomainRegistry):
        self.registry = registry

    def execute(self, profiles: List[DomainRiskProfile]) -> FleetInsightCollection:
        """
        Runs all registered cross-domain analyzers deterministically.
        Returns a FleetInsightCollection aggregating all discovered insights.
        """
        start_time = time.perf_counter()
        insights: List[FleetInsight] = []
        analyzer_results: Dict[str, str] = {}
        
        analyzers = self.registry.get_all_analyzers()
        
        for analyzer_class in analyzers:
            key = analyzer_class.key()
            try:
                analyzer = analyzer_class()
                discovered_insights = analyzer.execute(profiles)
                insights.extend(discovered_insights)
                analyzer_results[key] = "SUCCESS"
            except Exception as e:
                logger.error(f"Cross-Domain Analyzer '{key}' failed during execution: {str(e)}")
                logger.debug(traceback.format_exc())
                analyzer_results[key] = f"ERROR: {str(e)}"
                
        execution_time = time.perf_counter() - start_time
        
        return FleetInsightCollection(
            insights=insights,
            execution_time=execution_time,
            analyzer_results=analyzer_results
        )
