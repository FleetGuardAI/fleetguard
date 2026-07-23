import unittest

from infrastructure.intelligence.checks.models import CheckResult, CheckStatus
from infrastructure.intelligence.assessments.models import AssessmentStatus
from infrastructure.intelligence.tyre_domain.assessments.health import TyreHealthAssessment


class TestTyreAssessment(unittest.TestCase):
    def setUp(self):
        self.assessment = TyreHealthAssessment()
        
    def _make_check(self, key: str, status: CheckStatus) -> CheckResult:
        return CheckResult(
            check_key=key,
            check_name=key,
            status=status,
            message="test",
            evidence_used=[],
        )

    def test_assessment_all_pass(self):
        checks = [
            self._make_check("tyre.pressure", CheckStatus.PASS),
            self._make_check("tyre.tread_depth", CheckStatus.PASS),
            self._make_check("tyre.age", CheckStatus.PASS),
            self._make_check("tyre.wear_pattern", CheckStatus.PASS),
            self._make_check("tyre.damage", CheckStatus.PASS),
        ]
        
        res = self.assessment.execute(checks)
        
        self.assertEqual(res.status, AssessmentStatus.COMPLETE)
        self.assertEqual(len(res.findings), 0)

    def test_assessment_multiple_fails(self):
        checks = [
            self._make_check("tyre.pressure", CheckStatus.FAIL),
            self._make_check("tyre.tread_depth", CheckStatus.FAIL),
            self._make_check("tyre.age", CheckStatus.PASS),
            self._make_check("tyre.wear_pattern", CheckStatus.FAIL),
            self._make_check("tyre.damage", CheckStatus.PASS),
        ]
        
        res = self.assessment.execute(checks)
        
        self.assertEqual(res.status, AssessmentStatus.COMPLETE)
        self.assertEqual(len(res.findings), 3)
        finding_keys = [f.finding_key for f in res.findings]
        self.assertIn("tyre.pressure_deviation", finding_keys)
        self.assertIn("tyre.low_tread", finding_keys)
        self.assertIn("tyre.abnormal_wear", finding_keys)

    def test_assessment_missing_check(self):
        checks = [
            self._make_check("tyre.pressure", CheckStatus.PASS),
        ]
        
        res = self.assessment.execute(checks)
        self.assertEqual(res.status, AssessmentStatus.INCONCLUSIVE)
