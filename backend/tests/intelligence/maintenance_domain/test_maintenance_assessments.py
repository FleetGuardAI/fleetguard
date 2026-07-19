import unittest

from infrastructure.intelligence.checks.models import CheckResult, CheckStatus
from infrastructure.intelligence.assessments.models import AssessmentStatus
from infrastructure.intelligence.maintenance_domain.assessments.vehicle_health import VehicleHealthAssessment


class TestMaintenanceAssessments(unittest.TestCase):
    def test_vehicle_health_assessment_complete_safe(self):
        checks = [
            CheckResult(check_key="maintenance.service_overdue", check_name="", status=CheckStatus.PASS, message="", evidence_used=[]),
            CheckResult(check_key="maintenance.distance_overdue", check_name="", status=CheckStatus.PASS, message="", evidence_used=[]),
            CheckResult(check_key="maintenance.time_overdue", check_name="", status=CheckStatus.PASS, message="", evidence_used=[]),
            CheckResult(check_key="maintenance.repeated_failures", check_name="", status=CheckStatus.PASS, message="", evidence_used=[]),
            CheckResult(check_key="maintenance.critical_component_due", check_name="", status=CheckStatus.PASS, message="", evidence_used=[])
        ]
        
        assessment = VehicleHealthAssessment()
        res = assessment.execute(checks)
        
        self.assertEqual(res.status, AssessmentStatus.COMPLETE)
        self.assertEqual(len(res.findings), 1)
        self.assertIn("healthy", res.findings[0].finding_key)

    def test_vehicle_health_assessment_with_violations(self):
        checks = [
            CheckResult(check_key="maintenance.service_overdue", check_name="", status=CheckStatus.FAIL, message="", evidence_used=[]),
            CheckResult(check_key="maintenance.distance_overdue", check_name="", status=CheckStatus.PASS, message="", evidence_used=[]),
            CheckResult(check_key="maintenance.time_overdue", check_name="", status=CheckStatus.FAIL, message="", evidence_used=[]),
            CheckResult(check_key="maintenance.repeated_failures", check_name="", status=CheckStatus.PASS, message="", evidence_used=[]),
            CheckResult(check_key="maintenance.critical_component_due", check_name="", status=CheckStatus.PASS, message="", evidence_used=[])
        ]
        
        assessment = VehicleHealthAssessment()
        res = assessment.execute(checks)
        
        self.assertEqual(res.status, AssessmentStatus.COMPLETE)
        self.assertEqual(len(res.findings), 2)
        self.assertTrue(any("service_overdue" in f.finding_key for f in res.findings))
        self.assertTrue(any("time_overdue" in f.finding_key for f in res.findings))

    def test_vehicle_health_assessment_inconclusive(self):
        # All checks skipped because no evidence
        checks = [
            CheckResult(check_key="maintenance.service_overdue", check_name="", status=CheckStatus.SKIPPED, message="", evidence_used=[])
        ]
        
        assessment = VehicleHealthAssessment()
        res = assessment.execute(checks)
        
        self.assertEqual(res.status, AssessmentStatus.INCONCLUSIVE)
