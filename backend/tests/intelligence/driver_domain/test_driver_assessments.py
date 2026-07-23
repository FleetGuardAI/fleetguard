import unittest

from infrastructure.intelligence.checks.models import CheckResult, CheckStatus
from infrastructure.intelligence.assessments.models import AssessmentStatus
from infrastructure.intelligence.driver_domain.assessments.driver_behaviour import DriverBehaviourAssessment


class TestDriverAssessments(unittest.TestCase):
    def test_behaviour_assessment_complete_safe(self):
        checks = [
            CheckResult(check_key="driver.overspeed", check_name="", status=CheckStatus.PASS, message="", evidence_used=[]),
            CheckResult(check_key="driver.harsh_acceleration", check_name="", status=CheckStatus.PASS, message="", evidence_used=[]),
            CheckResult(check_key="driver.harsh_braking", check_name="", status=CheckStatus.PASS, message="", evidence_used=[]),
            CheckResult(check_key="driver.excessive_idling", check_name="", status=CheckStatus.PASS, message="", evidence_used=[]),
            CheckResult(check_key="driver.route_compliance", check_name="", status=CheckStatus.PASS, message="", evidence_used=[])
        ]
        
        assessment = DriverBehaviourAssessment()
        res = assessment.execute(checks)
        
        self.assertEqual(res.status, AssessmentStatus.COMPLETE)
        self.assertEqual(len(res.findings), 1)
        self.assertIn("safe_operation", res.findings[0].finding_key)

    def test_behaviour_assessment_with_violations(self):
        checks = [
            CheckResult(check_key="driver.overspeed", check_name="", status=CheckStatus.FAIL, message="", evidence_used=[]),
            CheckResult(check_key="driver.harsh_acceleration", check_name="", status=CheckStatus.FAIL, message="", evidence_used=[]),
            CheckResult(check_key="driver.harsh_braking", check_name="", status=CheckStatus.PASS, message="", evidence_used=[]),
            CheckResult(check_key="driver.excessive_idling", check_name="", status=CheckStatus.PASS, message="", evidence_used=[]),
            CheckResult(check_key="driver.route_compliance", check_name="", status=CheckStatus.PASS, message="", evidence_used=[])
        ]
        
        assessment = DriverBehaviourAssessment()
        res = assessment.execute(checks)
        
        self.assertEqual(res.status, AssessmentStatus.COMPLETE)
        self.assertEqual(len(res.findings), 2)
        self.assertTrue(any("overspeed" in f.finding_key for f in res.findings))
        self.assertTrue(any("harsh_acceleration" in f.finding_key for f in res.findings))

    def test_behaviour_assessment_inconclusive(self):
        checks = [
            CheckResult(check_key="driver.overspeed", check_name="", status=CheckStatus.PASS, message="", evidence_used=[])
        ]
        
        assessment = DriverBehaviourAssessment()
        res = assessment.execute(checks)
        
        self.assertEqual(res.status, AssessmentStatus.INCONCLUSIVE)
