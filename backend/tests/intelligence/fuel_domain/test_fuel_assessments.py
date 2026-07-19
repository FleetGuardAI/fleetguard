import unittest
from infrastructure.intelligence.checks.models import CheckResult, CheckStatus
from infrastructure.intelligence.assessments.models import AssessmentStatus
from infrastructure.intelligence.fuel_domain.assessments.transaction_integrity import FuelTransactionIntegrityAssessment

class TestFuelAssessments(unittest.TestCase):
    def test_integrity_assessment_complete(self):
        checks = [
            CheckResult(check_key="fuel.quantity_match", check_name="", status=CheckStatus.PASS, message="", evidence_used=[]),
            CheckResult(check_key="fuel.location_match", check_name="", status=CheckStatus.PASS, message="", evidence_used=[]),
            CheckResult(check_key="fuel.timing_match", check_name="", status=CheckStatus.PASS, message="", evidence_used=[]),
            CheckResult(check_key="fuel.tank_capacity", check_name="", status=CheckStatus.PASS, message="", evidence_used=[])
        ]
        
        assessment = FuelTransactionIntegrityAssessment()
        res = assessment.execute(checks)
        
        self.assertEqual(res.status, AssessmentStatus.COMPLETE)
        self.assertEqual(len(res.findings), 1)
        self.assertEqual(res.findings[0].category, "Integrity OK")

    def test_integrity_assessment_mismatch(self):
        checks = [
            CheckResult(check_key="fuel.quantity_match", check_name="", status=CheckStatus.FAIL, message="mismatch", evidence_used=[]),
            CheckResult(check_key="fuel.location_match", check_name="", status=CheckStatus.PASS, message="", evidence_used=[]),
            CheckResult(check_key="fuel.timing_match", check_name="", status=CheckStatus.PASS, message="", evidence_used=[]),
            CheckResult(check_key="fuel.tank_capacity", check_name="", status=CheckStatus.PASS, message="", evidence_used=[])
        ]
        
        assessment = FuelTransactionIntegrityAssessment()
        res = assessment.execute(checks)
        
        self.assertEqual(res.status, AssessmentStatus.COMPLETE)
        self.assertEqual(len(res.findings), 1)
        self.assertEqual(res.findings[0].category, "Integrity Mismatch")

    def test_integrity_assessment_inconclusive(self):
        checks = [
            CheckResult(check_key="fuel.quantity_match", check_name="", status=CheckStatus.PASS, message="", evidence_used=[])
        ]
        
        assessment = FuelTransactionIntegrityAssessment()
        res = assessment.execute(checks)
        
        self.assertEqual(res.status, AssessmentStatus.INCONCLUSIVE)
