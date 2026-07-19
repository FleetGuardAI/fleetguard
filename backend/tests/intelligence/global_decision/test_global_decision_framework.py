import unittest
from typing import List
from pydantic import ValidationError

from infrastructure.intelligence.domain_risk.models import DomainRiskProfile, DomainRiskStatus, RiskLevel
from infrastructure.intelligence.global_decision.models import (
    DecisionStatus, RecommendationStatus, RecommendationFinding, Recommendation
)
from infrastructure.intelligence.global_decision.base import BaseDecisionEngine
from infrastructure.intelligence.global_decision.registry import DecisionRegistry
from infrastructure.intelligence.global_decision.executor import DecisionExecutor


# Dummy Decision Engines for Testing
class ValidDecisionEngine(BaseDecisionEngine):
    @classmethod
    def key(cls) -> str:
        return "global.test_policy"

    def execute(self, profiles: List[DomainRiskProfile]) -> Recommendation:
        # Require a profile from test.risk_engine
        relevant = [p for p in profiles if p.risk_engine_key == "test.risk_engine"]
        
        if not relevant:
            return Recommendation(
                decision_engine_key=self.key(),
                decision_engine_name=self.name(),
                decision_engine_version=self.version(),
                status=DecisionStatus.INCONCLUSIVE,
                recommendation=None,
                summary="Missing test.risk_engine profile",
                supporting_profiles=profiles
            )
            
        risk_profile = relevant[0]
        
        # Policy: if high risk -> REJECT, otherwise -> APPROVE
        rec = RecommendationStatus.REJECT if risk_profile.risk_level == RiskLevel.HIGH else RecommendationStatus.APPROVE
        
        finding = RecommendationFinding(
            finding_key="global.test_policy.finding",
            category="Test",
            summary=f"Decision made based on {risk_profile.risk_level} risk.",
            details="See supporting profiles."
        )
        
        return Recommendation(
            decision_engine_key=self.key(),
            decision_engine_name=self.name(),
            decision_engine_version=self.version(),
            status=DecisionStatus.COMPLETE,
            recommendation=rec,
            summary="Decision complete.",
            findings=[finding],
            supporting_profiles=profiles
        )

class FaultyDecisionEngine(BaseDecisionEngine):
    @classmethod
    def key(cls) -> str:
        return "global.faulty_policy"

    def execute(self, profiles: List[DomainRiskProfile]) -> Recommendation:
        raise ValueError("Unexpected failure in decision engine!")


class TestGlobalDecisionFramework(unittest.TestCase):
    
    def setUp(self):
        self.registry = DecisionRegistry()
        self.executor = DecisionExecutor(self.registry)
        
        self.risk_high = DomainRiskProfile(
            risk_engine_key="test.risk_engine",
            risk_engine_name="Test Risk Engine",
            risk_engine_version="1.0",
            status=DomainRiskStatus.COMPLETE,
            risk_level=RiskLevel.HIGH,
            summary="High risk",
            findings=[],
            supporting_assessments=[]
        )
        
        self.risk_low = DomainRiskProfile(
            risk_engine_key="test.risk_engine",
            risk_engine_name="Test Risk Engine",
            risk_engine_version="1.0",
            status=DomainRiskStatus.COMPLETE,
            risk_level=RiskLevel.LOW,
            summary="Low risk",
            findings=[],
            supporting_assessments=[]
        )

    def test_decision_engine_registration_and_lookup(self):
        self.registry.register(ValidDecisionEngine)
        
        with self.assertRaises(ValueError):
            self.registry.register(ValidDecisionEngine)
            
        cls = self.registry.get_engine("global.test_policy")
        self.assertEqual(cls, ValidDecisionEngine)
        
        with self.assertRaises(ValueError):
            self.registry.get_engine("unknown")
            
        self.registry.register(FaultyDecisionEngine)
        engines = self.registry.enumerate_engines()
        self.assertEqual(engines[0].key(), "global.faulty_policy")
        self.assertEqual(engines[1].key(), "global.test_policy")

    def test_executor_with_missing_profiles(self):
        self.registry.register(ValidDecisionEngine)
        
        results = self.executor.execute_all([])
        
        self.assertEqual(len(results), 1)
        res = results[0]
        self.assertEqual(res.status, DecisionStatus.INCONCLUSIVE)
        self.assertIsNone(res.recommendation)

    def test_executor_with_profiles(self):
        self.registry.register(ValidDecisionEngine)
        
        # Test HIGH risk
        results_high = self.executor.execute_all([self.risk_high])
        self.assertEqual(len(results_high), 1)
        self.assertEqual(results_high[0].status, DecisionStatus.COMPLETE)
        self.assertEqual(results_high[0].recommendation, RecommendationStatus.REJECT)
        self.assertEqual(len(results_high[0].supporting_profiles), 1)
        
        # Test LOW risk
        results_low = self.executor.execute_all([self.risk_low])
        self.assertEqual(len(results_low), 1)
        self.assertEqual(results_low[0].status, DecisionStatus.COMPLETE)
        self.assertEqual(results_low[0].recommendation, RecommendationStatus.APPROVE)
        self.assertEqual(len(results_low[0].supporting_profiles), 1)

    def test_executor_isolates_faults(self):
        self.registry.register(ValidDecisionEngine)
        self.registry.register(FaultyDecisionEngine)
        
        results = self.executor.execute_all([self.risk_low])
        
        self.assertEqual(len(results), 2)
        
        faulty_res = next(r for r in results if r.decision_engine_key == "global.faulty_policy")
        valid_res = next(r for r in results if r.decision_engine_key == "global.test_policy")
        
        # Faulty should have ERROR status and None recommendation
        self.assertEqual(faulty_res.status, DecisionStatus.ERROR)
        self.assertIsNone(faulty_res.recommendation)
        self.assertIn("Unhandled exception", faulty_res.summary)
        self.assertIn("traceback", faulty_res.metadata)
        
        # Valid should still complete successfully
        self.assertEqual(valid_res.status, DecisionStatus.COMPLETE)
        self.assertEqual(valid_res.recommendation, RecommendationStatus.APPROVE)
