import unittest
from infrastructure.intelligence.assessments.models import AssessmentResult, AssessmentStatus, Finding
from infrastructure.intelligence.domain_risk.models import RiskLevel
from infrastructure.intelligence.compliance_domain.risk.vehicle_compliance_risk import VehicleComplianceRiskEngine


class TestComplianceRisk(unittest.TestCase):
    def test_risk_logic(self):
        engine = VehicleComplianceRiskEngine()
        
        # Low risk (no findings)
        a_low = AssessmentResult(
            assessment_key="compliance.vehicle_assessment", assessment_name="1", assessment_version="1",
            status=AssessmentStatus.COMPLETE, summary="OK", findings=[], contributing_checks=[]
        )
        res = engine.execute([a_low])
        self.assertEqual(res.risk_level, RiskLevel.LOW)
        
        # Medium risk (warnings only)
        a_med = AssessmentResult(
            assessment_key="compliance.vehicle_assessment", assessment_name="1", assessment_version="1",
            status=AssessmentStatus.COMPLETE, summary="OK", findings=[
                Finding(finding_key="x_warning", category="Warning", summary="W", details="D")
            ], contributing_checks=[]
        )
        res = engine.execute([a_med])
        self.assertEqual(res.risk_level, RiskLevel.MEDIUM)
        
        # Critical risk (failure)
        a_crit = AssessmentResult(
            assessment_key="compliance.vehicle_assessment", assessment_name="1", assessment_version="1",
            status=AssessmentStatus.COMPLETE, summary="OK", findings=[
                Finding(finding_key="compliance.pollution_invalid", category="Warning", summary="W", details="D")
            ], contributing_checks=[]
        )
        res = engine.execute([a_crit])
        self.assertEqual(res.risk_level, RiskLevel.CRITICAL)
