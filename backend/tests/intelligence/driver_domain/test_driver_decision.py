import unittest

from infrastructure.intelligence.domain_risk.models import DomainRiskProfile, DomainRiskStatus, RiskLevel
from infrastructure.intelligence.global_decision.models import DecisionStatus, RecommendationStatus
from infrastructure.intelligence.driver_domain.decision.driver_decision import DriverBehaviourDecisionEngine


class TestDriverDecision(unittest.TestCase):
    def test_decision_low(self):
        profiles = [
            DomainRiskProfile(risk_engine_key="driver.behaviour_risk", risk_engine_name="", risk_engine_version="", status=DomainRiskStatus.COMPLETE, risk_level=RiskLevel.LOW, summary="")
        ]
        
        engine = DriverBehaviourDecisionEngine()
        res = engine.execute(profiles)
        
        self.assertEqual(res.status, DecisionStatus.COMPLETE)
        self.assertEqual(res.recommendation, RecommendationStatus.APPROVE)

    def test_decision_high(self):
        profiles = [
            DomainRiskProfile(risk_engine_key="driver.behaviour_risk", risk_engine_name="", risk_engine_version="", status=DomainRiskStatus.COMPLETE, risk_level=RiskLevel.HIGH, summary="")
        ]
        
        engine = DriverBehaviourDecisionEngine()
        res = engine.execute(profiles)
        
        self.assertEqual(res.status, DecisionStatus.COMPLETE)
        self.assertEqual(res.recommendation, RecommendationStatus.REVIEW_REQUIRED)

    def test_decision_critical(self):
        profiles = [
            DomainRiskProfile(risk_engine_key="driver.behaviour_risk", risk_engine_name="", risk_engine_version="", status=DomainRiskStatus.COMPLETE, risk_level=RiskLevel.CRITICAL, summary="")
        ]
        
        engine = DriverBehaviourDecisionEngine()
        res = engine.execute(profiles)
        
        self.assertEqual(res.status, DecisionStatus.COMPLETE)
        self.assertEqual(res.recommendation, RecommendationStatus.REJECT)

    def test_decision_missing(self):
        engine = DriverBehaviourDecisionEngine()
        res = engine.execute([])
        
        self.assertEqual(res.status, DecisionStatus.INCONCLUSIVE)
