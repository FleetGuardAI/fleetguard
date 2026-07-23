import unittest
from typing import List
from infrastructure.intelligence.cross_domain.registry import CrossDomainRegistry
from infrastructure.intelligence.cross_domain.executor import CrossDomainExecutor
from infrastructure.intelligence.cross_domain.base import BaseCrossDomainAnalyzer
from infrastructure.intelligence.domain_risk.models import DomainRiskProfile
from infrastructure.intelligence.cross_domain.models import FleetInsight, InsightType, InsightStrength


class SuccessAnalyzer(BaseCrossDomainAnalyzer):
    @classmethod
    def key(cls) -> str:
        return "test.success"

    def execute(self, profiles: List[DomainRiskProfile]) -> List[FleetInsight]:
        return [
            FleetInsight(
                insight_key="test.insight",
                insight_type=InsightType.CORRELATION,
                insight_strength=InsightStrength.LOW,
                summary="Success"
            )
        ]

class FailAnalyzer(BaseCrossDomainAnalyzer):
    @classmethod
    def key(cls) -> str:
        return "test.fail"

    def execute(self, profiles: List[DomainRiskProfile]) -> List[FleetInsight]:
        raise ValueError("Simulated failure")


class TestCrossDomainExecutor(unittest.TestCase):
    def test_executor_isolation_and_aggregation(self):
        registry = CrossDomainRegistry()
        registry.register(SuccessAnalyzer)
        registry.register(FailAnalyzer)
        
        executor = CrossDomainExecutor(registry)
        
        # Execute with empty profiles
        result = executor.execute([])
        
        self.assertEqual(len(result.insights), 1)
        self.assertEqual(result.insights[0].summary, "Success")
        
        self.assertEqual(result.analyzer_results["test.success"], "SUCCESS")
        self.assertTrue(result.analyzer_results["test.fail"].startswith("ERROR"))
