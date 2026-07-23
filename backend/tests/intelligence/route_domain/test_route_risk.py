import unittest

from infrastructure.intelligence.assessments.models import AssessmentResult, AssessmentStatus, Finding
from infrastructure.intelligence.domain_risk.models import DomainRiskStatus, RiskLevel
from infrastructure.intelligence.route_domain.risk.compliance_risk import TripComplianceRiskEngine


class TestRouteRisk(unittest.TestCase):
    def setUp(self):
        self.engine = TripComplianceRiskEngine()

    def _make_assessment(self, status: AssessmentStatus, findings: list) -> AssessmentResult:
        return AssessmentResult(
            assessment_key="route.trip_compliance_assessment",
            assessment_name="Trip Compliance Assessment",
            assessment_version="1.0.0",
            status=status,
            summary="test",
            findings=findings,
            contributing_checks=[]
        )

    def test_risk_low(self):
        assessment = self._make_assessment(AssessmentStatus.COMPLETE, [])
        res = self.engine.execute([assessment])
        self.assertEqual(res.risk_level, RiskLevel.LOW)

    def test_risk_medium(self):
        findings = [
            Finding(finding_key="route.trip_delayed", category="Performance", summary="test", details="test")
        ]
        assessment = self._make_assessment(AssessmentStatus.COMPLETE, findings)
        res = self.engine.execute([assessment])
        self.assertEqual(res.risk_level, RiskLevel.MEDIUM)

    def test_risk_high(self):
        findings = [
            Finding(finding_key="route.deviation_detected", category="Compliance", summary="test", details="test")
        ]
        assessment = self._make_assessment(AssessmentStatus.COMPLETE, findings)
        res = self.engine.execute([assessment])
        self.assertEqual(res.risk_level, RiskLevel.HIGH)
        
    def test_risk_high_multiple(self):
        findings = [
            Finding(finding_key="route.trip_delayed", category="Performance", summary="test", details="test"),
            Finding(finding_key="unknown", category="Unknown", summary="test", details="test")
        ]
        assessment = self._make_assessment(AssessmentStatus.COMPLETE, findings)
        res = self.engine.execute([assessment])
        self.assertEqual(res.risk_level, RiskLevel.HIGH)

    def test_risk_critical(self):
        findings = [
            Finding(finding_key="route.geofence_breach", category="Compliance", summary="test", details="test")
        ]
        assessment = self._make_assessment(AssessmentStatus.COMPLETE, findings)
        res = self.engine.execute([assessment])
        self.assertEqual(res.risk_level, RiskLevel.CRITICAL)

    def test_risk_missing(self):
        res = self.engine.execute([])
        self.assertEqual(res.status, DomainRiskStatus.INCONCLUSIVE)
