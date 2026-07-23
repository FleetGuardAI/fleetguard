import unittest
from infrastructure.intelligence.domain_risk.models import DomainRiskProfile, DomainRiskStatus, RiskLevel
from infrastructure.intelligence.global_decision.models import DecisionStatus, RecommendationStatus
from infrastructure.intelligence.fuel_domain.decision.transaction_decision import FuelDecisionEngine

class TestFuelDecision(unittest.TestCase):
    def test_decision_low_risk(self):
        profile = DomainRiskProfile(
            risk_engine_key="fuel.transaction_risk",
            risk_engine_name="", risk_engine_version="", status=DomainRiskStatus.COMPLETE,
            risk_level=RiskLevel.LOW, summary="", findings=[], supporting_assessments=[]
        )
        
        engine = FuelDecisionEngine()
        res = engine.execute([profile])
        
        self.assertEqual(res.status, DecisionStatus.COMPLETE)
        self.assertEqual(res.recommendation, RecommendationStatus.APPROVE)

    def test_decision_medium_risk(self):
        profile = DomainRiskProfile(
            risk_engine_key="fuel.transaction_risk",
            risk_engine_name="", risk_engine_version="", status=DomainRiskStatus.COMPLETE,
            risk_level=RiskLevel.MEDIUM, summary="", findings=[], supporting_assessments=[]
        )
        
        engine = FuelDecisionEngine()
        res = engine.execute([profile])
        
        self.assertEqual(res.status, DecisionStatus.COMPLETE)
        self.assertEqual(res.recommendation, RecommendationStatus.APPROVE_WITH_REVIEW)

    def test_decision_high_risk(self):
        profile = DomainRiskProfile(
            risk_engine_key="fuel.transaction_risk",
            risk_engine_name="", risk_engine_version="", status=DomainRiskStatus.COMPLETE,
            risk_level=RiskLevel.HIGH, summary="", findings=[], supporting_assessments=[]
        )
        
        engine = FuelDecisionEngine()
        res = engine.execute([profile])
        
        self.assertEqual(res.status, DecisionStatus.COMPLETE)
        self.assertEqual(res.recommendation, RecommendationStatus.REVIEW_REQUIRED)

    def test_decision_critical_risk(self):
        profile = DomainRiskProfile(
            risk_engine_key="fuel.transaction_risk",
            risk_engine_name="", risk_engine_version="", status=DomainRiskStatus.COMPLETE,
            risk_level=RiskLevel.CRITICAL, summary="", findings=[], supporting_assessments=[]
        )
        
        engine = FuelDecisionEngine()
        res = engine.execute([profile])
        
        self.assertEqual(res.status, DecisionStatus.COMPLETE)
        self.assertEqual(res.recommendation, RecommendationStatus.REJECT)

    def test_decision_inconclusive(self):
        profile = DomainRiskProfile(
            risk_engine_key="fuel.transaction_risk",
            risk_engine_name="", risk_engine_version="", status=DomainRiskStatus.INCONCLUSIVE,
            risk_level=RiskLevel.UNKNOWN, summary="", findings=[], supporting_assessments=[]
        )
        
        engine = FuelDecisionEngine()
        res = engine.execute([profile])
        
        self.assertEqual(res.status, DecisionStatus.INCONCLUSIVE)
        self.assertIsNone(res.recommendation)
