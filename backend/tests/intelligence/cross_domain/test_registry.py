import unittest
from typing import List
from infrastructure.intelligence.cross_domain.registry import CrossDomainRegistry
from infrastructure.intelligence.cross_domain.base import BaseCrossDomainAnalyzer
from infrastructure.intelligence.domain_risk.models import DomainRiskProfile
from infrastructure.intelligence.cross_domain.models import FleetInsight


class DummyAnalyzerA(BaseCrossDomainAnalyzer):
    @classmethod
    def key(cls) -> str:
        return "dummy.a"

    def execute(self, profiles: List[DomainRiskProfile]) -> List[FleetInsight]:
        return []

class DummyAnalyzerB(BaseCrossDomainAnalyzer):
    @classmethod
    def key(cls) -> str:
        return "dummy.b"

    def execute(self, profiles: List[DomainRiskProfile]) -> List[FleetInsight]:
        return []


class TestCrossDomainRegistry(unittest.TestCase):
    def setUp(self):
        self.registry = CrossDomainRegistry()

    def test_registration_and_lookup(self):
        self.registry.register(DummyAnalyzerA)
        analyzer = self.registry.get_analyzer("dummy.a")
        self.assertEqual(analyzer, DummyAnalyzerA)

    def test_duplicate_registration(self):
        self.registry.register(DummyAnalyzerA)
        with self.assertRaises(ValueError):
            self.registry.register(DummyAnalyzerA)

    def test_missing_lookup(self):
        with self.assertRaises(KeyError):
            self.registry.get_analyzer("missing")

    def test_deterministic_ordering(self):
        self.registry.register(DummyAnalyzerB)
        self.registry.register(DummyAnalyzerA)
        
        analyzers = self.registry.get_all_analyzers()
        self.assertEqual(analyzers[0], DummyAnalyzerB)
        self.assertEqual(analyzers[1], DummyAnalyzerA)
