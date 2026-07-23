import unittest

from infrastructure.intelligence.assessments.models import AssessmentResult, AssessmentStatus, Finding
from infrastructure.intelligence.domain_risk.models import DomainRiskStatus, RiskLevel
from infrastructure.intelligence.driver_domain.risk.driver_risk import DriverBehaviourRiskEngine


class TestDriverRisk(unittest.TestCase):
    def test_risk_low(self):
        findings = [
            Finding(finding_key="driver.behaviour_assessment.finding.safe_operation", category="Safe Driving", summary="", details="")
        ]
        assessments = [
            AssessmentResult(assessment_key="driver.behaviour_assessment", assessment_name="", assessment_version="", status=AssessmentStatus.COMPLETE, summary="", findings=findings)
        ]
        
        engine = DriverBehaviourRiskEngine()
        res = engine.execute(assessments)
        
        self.assertEqual(res.status, DomainRiskStatus.COMPLETE)
        self.assertEqual(res.risk_level, RiskLevel.LOW)

    def test_risk_high(self):
        findings = [
            Finding(finding_key="driver.behaviour_assessment.finding.overspeed_failed", category="Mismatch", summary="", details="")
        ]
        assessments = [
            AssessmentResult(assessment_key="driver.behaviour_assessment", assessment_name="", assessment_version="", status=AssessmentStatus.COMPLETE, summary="", findings=findings)
        ]
        
        engine = DriverBehaviourRiskEngine()
        res = engine.execute(assessments)
        
        self.assertEqual(res.status, DomainRiskStatus.COMPLETE)
        self.assertEqual(res.risk_level, RiskLevel.HIGH)

    def test_risk_critical(self):
        findings = [
            Finding(finding_key="driver.behaviour_assessment.finding.overspeed_failed", category="Mismatch", summary="", details=""),
            Finding(finding_key="driver.behaviour_assessment.finding.harsh_braking_failed", category="Mismatch", summary="", details="")
        ]
        assessments = [
            AssessmentResult(assessment_key="driver.behaviour_assessment", assessment_name="", assessment_version="", status=AssessmentStatus.COMPLETE, summary="", findings=findings)
        ]
        
        engine = DriverBehaviourRiskEngine()
        res = engine.execute(assessments)
        
        self.assertEqual(res.status, DomainRiskStatus.COMPLETE)
        self.assertEqual(res.risk_level, RiskLevel.CRITICAL)

    def test_risk_missing(self):
        engine = DriverBehaviourRiskEngine()
        res = engine.execute([])
        
        self.assertEqual(res.status, DomainRiskStatus.INCONCLUSIVE)
