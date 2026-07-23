import unittest

from infrastructure.intelligence.assessments.models import AssessmentResult, AssessmentStatus, Finding
from infrastructure.intelligence.domain_risk.models import DomainRiskStatus, RiskLevel
from infrastructure.intelligence.maintenance_domain.risk.vehicle_health_risk import VehicleHealthRiskEngine


class TestMaintenanceRisk(unittest.TestCase):
    def test_risk_low(self):
        findings = [
            Finding(finding_key="maintenance.vehicle_health_assessment.finding.healthy", category="Health", summary="", details="")
        ]
        assessments = [
            AssessmentResult(assessment_key="maintenance.vehicle_health_assessment", assessment_name="", assessment_version="", status=AssessmentStatus.COMPLETE, summary="", findings=findings)
        ]
        
        engine = VehicleHealthRiskEngine()
        res = engine.execute(assessments)
        
        self.assertEqual(res.status, DomainRiskStatus.COMPLETE)
        self.assertEqual(res.risk_level, RiskLevel.LOW)

    def test_risk_medium(self):
        findings = [
            Finding(finding_key="maintenance.vehicle_health_assessment.finding.time_overdue_failed", category="Alert", summary="", details="")
        ]
        assessments = [
            AssessmentResult(assessment_key="maintenance.vehicle_health_assessment", assessment_name="", assessment_version="", status=AssessmentStatus.COMPLETE, summary="", findings=findings)
        ]
        
        engine = VehicleHealthRiskEngine()
        res = engine.execute(assessments)
        
        self.assertEqual(res.status, DomainRiskStatus.COMPLETE)
        self.assertEqual(res.risk_level, RiskLevel.MEDIUM)

    def test_risk_high(self):
        findings = [
            Finding(finding_key="maintenance.vehicle_health_assessment.finding.time_overdue_failed", category="Alert", summary="", details=""),
            Finding(finding_key="maintenance.vehicle_health_assessment.finding.repeated_failures_failed", category="Alert", summary="", details="")
        ]
        assessments = [
            AssessmentResult(assessment_key="maintenance.vehicle_health_assessment", assessment_name="", assessment_version="", status=AssessmentStatus.COMPLETE, summary="", findings=findings)
        ]
        
        engine = VehicleHealthRiskEngine()
        res = engine.execute(assessments)
        
        self.assertEqual(res.status, DomainRiskStatus.COMPLETE)
        self.assertEqual(res.risk_level, RiskLevel.HIGH)

    def test_risk_critical(self):
        findings = [
            Finding(finding_key="maintenance.vehicle_health_assessment.finding.critical_component_due_failed", category="Alert", summary="", details="")
        ]
        assessments = [
            AssessmentResult(assessment_key="maintenance.vehicle_health_assessment", assessment_name="", assessment_version="", status=AssessmentStatus.COMPLETE, summary="", findings=findings)
        ]
        
        engine = VehicleHealthRiskEngine()
        res = engine.execute(assessments)
        
        self.assertEqual(res.status, DomainRiskStatus.COMPLETE)
        self.assertEqual(res.risk_level, RiskLevel.CRITICAL)

    def test_risk_missing(self):
        engine = VehicleHealthRiskEngine()
        res = engine.execute([])
        
        self.assertEqual(res.status, DomainRiskStatus.INCONCLUSIVE)
