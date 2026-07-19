import unittest
from infrastructure.intelligence.checks.models import CheckResult, CheckStatus
from infrastructure.intelligence.assessments.models import AssessmentStatus
from infrastructure.intelligence.compliance_domain.assessments.vehicle_compliance import VehicleComplianceAssessment


class TestComplianceAssessment(unittest.TestCase):
    def test_assessment_logic(self):
        assessment = VehicleComplianceAssessment()
        
        checks = [
            CheckResult(check_key="compliance.registration_validity", check_name="1", status=CheckStatus.PASS, message="OK", evidence_used=[]),
            CheckResult(check_key="compliance.insurance_validity", check_name="2", status=CheckStatus.PASS, message="OK", evidence_used=[]),
            CheckResult(check_key="compliance.fitness_validity", check_name="3", status=CheckStatus.PASS, message="OK", evidence_used=[], metadata={"expiring_soon": True}),
            CheckResult(check_key="compliance.pollution_validity", check_name="4", status=CheckStatus.FAIL, message="Fail", evidence_used=[]),
            CheckResult(check_key="compliance.permit_validity", check_name="5", status=CheckStatus.PASS, message="OK", evidence_used=[]),
            CheckResult(check_key="compliance.driver_license_validity", check_name="6", status=CheckStatus.PASS, message="OK", evidence_used=[]),
        ]
        
        res = assessment.execute(checks)
        self.assertEqual(res.status, AssessmentStatus.COMPLETE)
        self.assertEqual(len(res.findings), 2)
        
        # One is failure, one is warning
        keys = [f.finding_key for f in res.findings]
        self.assertIn("compliance.fitness_invalid_warning", keys)
        self.assertIn("compliance.pollution_invalid", keys)
