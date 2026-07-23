import unittest

from infrastructure.intelligence.domain_risk.models import DomainRiskProfile, RiskLevel, DomainRiskStatus
from infrastructure.intelligence.global_decision.models import DecisionStatus, RecommendationStatus
from infrastructure.intelligence.tyre_domain.decision.health_decision import TyreHealthDecisionEngine


class TestTyreDecision(unittest.TestCase):
    def setUp(self):
        self.engine = TyreHealthDecisionEngine()

    def _make_profile(self, risk_level: RiskLevel) -> DomainRiskProfile:
        return DomainRiskProfile(
            risk_engine_key="tyre.health_risk",
            risk_engine_name="test",
            risk_engine_version="1.0",
            status=DomainRiskStatus.COMPLETE,
            risk_level=risk_level,
            summary="test",
            findings=[],
            supporting_assessments=[]
        )

    def test_decision_low(self):
        profile = self._make_profile(RiskLevel.LOW)
        res = self.engine.execute([profile])
        
        self.assertEqual(res.status, DecisionStatus.COMPLETE)
        self.assertEqual(res.recommendation, RecommendationStatus.APPROVE)

    def test_decision_medium(self):
        profile = self._make_profile(RiskLevel.MEDIUM)
        res = self.engine.execute([profile])
        
        self.assertEqual(res.status, DecisionStatus.COMPLETE)
        self.assertEqual(res.recommendation, RecommendationStatus.APPROVE_WITH_REVIEW)

    def test_decision_high(self):
        profile = self._make_profile(RiskLevel.HIGH)
        res = self.engine.execute([profile])
        
        self.assertEqual(res.status, DecisionStatus.COMPLETE)
        self.assertEqual(res.recommendation, RecommendationStatus.REVIEW_REQUIRED)

    def test_decision_critical(self):
        profile = self._make_profile(RiskLevel.CRITICAL)
        res = self.engine.execute([profile])
        
        self.assertEqual(res.status, DecisionStatus.COMPLETE)
        self.assertEqual(res.recommendation, RecommendationStatus.REJECT)

    def test_decision_missing(self):
        res = self.engine.execute([])
        self.assertEqual(res.status, DecisionStatus.INCONCLUSIVE)
