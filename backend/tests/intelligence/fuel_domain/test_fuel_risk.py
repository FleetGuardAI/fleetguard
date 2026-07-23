import unittest
from infrastructure.intelligence.assessments.models import AssessmentResult, AssessmentStatus, Finding
from infrastructure.intelligence.domain_risk.models import DomainRiskStatus, RiskLevel
from infrastructure.intelligence.fuel_domain.risk.transaction_risk import FuelTransactionRiskEngine

class TestFuelRisk(unittest.TestCase):
    def test_risk_low(self):
        assessment = AssessmentResult(
            assessment_key="fuel.transaction_integrity",
            assessment_name="", assessment_version="", status=AssessmentStatus.COMPLETE, summary="",
            findings=[Finding(finding_key="fuel.transaction_integrity.finding.consistent", category="Integrity OK", summary="", details="")],
            contributing_checks=[]
        )
        
        engine = FuelTransactionRiskEngine()
        res = engine.execute([assessment])
        
        self.assertEqual(res.status, DomainRiskStatus.COMPLETE)
        self.assertEqual(res.risk_level, RiskLevel.LOW)

    def test_risk_high(self):
        assessment = AssessmentResult(
            assessment_key="fuel.transaction_integrity",
            assessment_name="", assessment_version="", status=AssessmentStatus.COMPLETE, summary="",
            findings=[Finding(finding_key="mismatch", category="Integrity Mismatch", summary="", details="")],
            contributing_checks=[]
        )
        
        engine = FuelTransactionRiskEngine()
        res = engine.execute([assessment])
        
        self.assertEqual(res.status, DomainRiskStatus.COMPLETE)
        self.assertEqual(res.risk_level, RiskLevel.HIGH)

    def test_risk_critical(self):
        assessment = AssessmentResult(
            assessment_key="fuel.transaction_integrity",
            assessment_name="", assessment_version="", status=AssessmentStatus.COMPLETE, summary="",
            findings=[
                Finding(finding_key="m1", category="Integrity Mismatch", summary="", details=""),
                Finding(finding_key="m2", category="Integrity Mismatch", summary="", details="")
            ],
            contributing_checks=[]
        )
        
        engine = FuelTransactionRiskEngine()
        res = engine.execute([assessment])
        
        self.assertEqual(res.status, DomainRiskStatus.COMPLETE)
        self.assertEqual(res.risk_level, RiskLevel.CRITICAL)

    def test_risk_inconclusive(self):
        assessment = AssessmentResult(
            assessment_key="fuel.transaction_integrity",
            assessment_name="", assessment_version="", status=AssessmentStatus.INCONCLUSIVE, summary="",
            findings=[],
            contributing_checks=[]
        )
        
        engine = FuelTransactionRiskEngine()
        res = engine.execute([assessment])
        
        self.assertEqual(res.status, DomainRiskStatus.INCONCLUSIVE)
        self.assertEqual(res.risk_level, RiskLevel.UNKNOWN)
