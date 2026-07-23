import unittest

from infrastructure.intelligence.checks.models import CheckResult, CheckStatus
from infrastructure.intelligence.assessments.models import AssessmentStatus
from infrastructure.intelligence.route_domain.assessments.trip_compliance import TripComplianceAssessment


class TestRouteAssessment(unittest.TestCase):
    def setUp(self):
        self.assessment = TripComplianceAssessment()

    def _make_check(self, key: str, status: CheckStatus) -> CheckResult:
        return CheckResult(
            check_key=key,
            check_name=key,
            status=status,
            message="test",
            evidence_used=[]
        )

    def test_assessment_all_pass(self):
        checks = [
            self._make_check("route.deviation", CheckStatus.PASS),
            self._make_check("route.trip_delay", CheckStatus.PASS),
            self._make_check("route.unauthorized_stop", CheckStatus.PASS),
            self._make_check("route.geofence_violation", CheckStatus.PASS),
            self._make_check("route.excessive_detour", CheckStatus.PASS),
        ]
        res = self.assessment.execute(checks)
        self.assertEqual(res.status, AssessmentStatus.COMPLETE)
        self.assertEqual(len(res.findings), 0)

    def test_assessment_multiple_fails(self):
        checks = [
            self._make_check("route.deviation", CheckStatus.FAIL),
            self._make_check("route.trip_delay", CheckStatus.PASS),
            self._make_check("route.unauthorized_stop", CheckStatus.FAIL),
            self._make_check("route.geofence_violation", CheckStatus.PASS),
            self._make_check("route.excessive_detour", CheckStatus.PASS),
        ]
        res = self.assessment.execute(checks)
        self.assertEqual(res.status, AssessmentStatus.COMPLETE)
        self.assertEqual(len(res.findings), 2)
        keys = {f.finding_key for f in res.findings}
        self.assertIn("route.deviation_detected", keys)
        self.assertIn("route.unauthorized_stop_detected", keys)

    def test_assessment_missing_checks(self):
        checks = [self._make_check("route.deviation", CheckStatus.PASS)]
        res = self.assessment.execute(checks)
        self.assertEqual(res.status, AssessmentStatus.INCONCLUSIVE)
