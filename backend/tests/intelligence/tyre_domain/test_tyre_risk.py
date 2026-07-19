import unittest

from infrastructure.intelligence.assessments.models import AssessmentResult, AssessmentStatus, Finding
from infrastructure.intelligence.domain_risk.models import DomainRiskStatus, RiskLevel
from infrastructure.intelligence.tyre_domain.risk.health_risk import TyreHealthRiskEngine


class TestTyreRisk(unittest.TestCase):
    def setUp(self):
        self.engine = TyreHealthRiskEngine()

    def _make_assessment(self, status: AssessmentStatus, findings: list) -> AssessmentResult:
        return AssessmentResult(
            assessment_key="tyre.health_assessment",
            assessment_name="test",
            assessment_version="1.0",
            status=status,
            summary="test",
            findings=findings,
            contributing_checks=[]
        )

    def test_risk_low(self):
        assessment = self._make_assessment(AssessmentStatus.COMPLETE, [])
        res = self.engine.execute([assessment])
        
        self.assertEqual(res.status, DomainRiskStatus.COMPLETE)
        self.assertEqual(res.risk_level, RiskLevel.LOW)

    def test_risk_medium(self):
        findings = [
            Finding(finding_key="tyre.pressure_deviation", category="Maintenance", summary="test", details="test")
        ]
        assessment = self._make_assessment(AssessmentStatus.COMPLETE, findings)
        res = self.engine.execute([assessment])
        
        self.assertEqual(res.status, DomainRiskStatus.COMPLETE)
        self.assertEqual(res.risk_level, RiskLevel.MEDIUM)

    def test_risk_high(self):
        findings = [
            Finding(finding_key="tyre.pressure_deviation", category="Maintenance", summary="test", details="test"),
            Finding(finding_key="tyre.abnormal_wear", category="Maintenance", summary="test", details="test")
        ]
        assessment = self._make_assessment(AssessmentStatus.COMPLETE, findings)
        res = self.engine.execute([assessment])
        
        self.assertEqual(res.status, DomainRiskStatus.COMPLETE)
        self.assertEqual(res.risk_level, RiskLevel.HIGH)

    def test_risk_critical(self):
        findings = [
            Finding(finding_key="tyre.low_tread", category="Safety", summary="test", details="test")
        ]
        assessment = self._make_assessment(AssessmentStatus.COMPLETE, findings)
        res = self.engine.execute([assessment])
        
        self.assertEqual(res.status, DomainRiskStatus.COMPLETE)
        self.assertEqual(res.risk_level, RiskLevel.CRITICAL)

    def test_risk_missing(self):
        res = self.engine.execute([])
        self.assertEqual(res.status, DomainRiskStatus.INCONCLUSIVE)
