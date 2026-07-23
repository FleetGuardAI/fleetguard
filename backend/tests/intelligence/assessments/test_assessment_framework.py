import unittest
from typing import List
from pydantic import ValidationError

from infrastructure.intelligence.checks.models import CheckResult, CheckStatus
from infrastructure.intelligence.assessments.models import AssessmentStatus, Finding, AssessmentResult
from infrastructure.intelligence.assessments.base import BaseAssessment
from infrastructure.intelligence.assessments.registry import AssessmentRegistry
from infrastructure.intelligence.assessments.executor import AssessmentExecutor


# Dummy Assessments for Testing
class ValidAssessment(BaseAssessment):
    @classmethod
    def key(cls) -> str:
        return "test.valid_assessment"

    @classmethod
    def required_checks(cls) -> List[str]:
        return ["test.check_1", "test.check_2"]
        
    @classmethod
    def optional_checks(cls) -> List[str]:
        return ["test.check_3"]

    def execute(self, checks: List[CheckResult]) -> AssessmentResult:
        check_keys = [c.check_key for c in checks]
        
        # Check required
        missing = [req for req in self.required_checks() if req not in check_keys]
        if missing:
            return AssessmentResult(
                assessment_key=self.key(),
                assessment_name=self.name(),
                assessment_version=self.version(),
                status=AssessmentStatus.INCONCLUSIVE,
                summary=f"Missing required checks: {missing}",
                contributing_checks=checks
            )
            
        finding = Finding(
            finding_key="test.finding.valid",
            category="Test",
            summary="All required checks present.",
            details="The assessment was able to complete."
        )
        
        return AssessmentResult(
            assessment_key=self.key(),
            assessment_name=self.name(),
            assessment_version=self.version(),
            status=AssessmentStatus.COMPLETE,
            summary="Assessment completed successfully.",
            findings=[finding],
            contributing_checks=checks
        )

class FaultyAssessment(BaseAssessment):
    @classmethod
    def key(cls) -> str:
        return "test.faulty_assessment"

    @classmethod
    def required_checks(cls) -> List[str]:
        return []

    def execute(self, checks: List[CheckResult]) -> AssessmentResult:
        raise ValueError("Unexpected failure in assessment!")


class TestAssessmentFramework(unittest.TestCase):
    
    def setUp(self):
        self.registry = AssessmentRegistry()
        self.executor = AssessmentExecutor(self.registry)
        
        self.check1 = CheckResult(
            check_key="test.check_1",
            check_name="Check 1",
            status=CheckStatus.PASS,
            message="OK"
        )
        self.check2 = CheckResult(
            check_key="test.check_2",
            check_name="Check 2",
            status=CheckStatus.FAIL,
            message="Failed"
        )
        self.check3 = CheckResult(
            check_key="test.check_3",
            check_name="Check 3",
            status=CheckStatus.PASS,
            message="OK"
        )

    def test_finding_serialization_and_validation(self):
        finding = Finding(
            finding_key="key1",
            category="Cat",
            summary="Sum",
            details="Det"
        )
        self.assertEqual(finding.category, "Cat")
        
        # Immutability
        with self.assertRaises(ValidationError):
            finding.summary = "New sum"

    def test_assessment_registration_and_lookup(self):
        self.registry.register(ValidAssessment)
        
        # Duplicate
        with self.assertRaises(ValueError):
            self.registry.register(ValidAssessment)
            
        # Lookup
        cls = self.registry.get_assessment("test.valid_assessment")
        self.assertEqual(cls, ValidAssessment)
        
        # Unknown
        with self.assertRaises(ValueError):
            self.registry.get_assessment("unknown")
            
        # Deterministic Order
        self.registry.register(FaultyAssessment)
        assessments = self.registry.enumerate_assessments()
        # Alphabetical by key: "test.faulty_assessment", "test.valid_assessment"
        self.assertEqual(assessments[0].key(), "test.faulty_assessment")
        self.assertEqual(assessments[1].key(), "test.valid_assessment")

    def test_executor_missing_required_checks(self):
        self.registry.register(ValidAssessment)
        
        # Missing check_2
        results = self.executor.execute_all([self.check1])
        
        self.assertEqual(len(results), 1)
        res = results[0]
        self.assertEqual(res.status, AssessmentStatus.INCONCLUSIVE)
        self.assertIn("test.check_2", res.summary)
        
        # Verify check references are preserved exactly
        self.assertEqual(len(res.contributing_checks), 1)
        self.assertEqual(res.contributing_checks[0].check_key, "test.check_1")

    def test_executor_with_all_required_checks(self):
        self.registry.register(ValidAssessment)
        
        # Has check 1 and 2
        results = self.executor.execute_all([self.check1, self.check2])
        
        self.assertEqual(len(results), 1)
        res = results[0]
        self.assertEqual(res.status, AssessmentStatus.COMPLETE)
        self.assertEqual(len(res.findings), 1)
        self.assertEqual(res.findings[0].finding_key, "test.finding.valid")
        self.assertEqual(len(res.contributing_checks), 2)

    def test_executor_isolates_faults(self):
        self.registry.register(ValidAssessment)
        self.registry.register(FaultyAssessment)
        
        results = self.executor.execute_all([self.check1, self.check2])
        
        self.assertEqual(len(results), 2)
        
        faulty_res = next(r for r in results if r.assessment_key == "test.faulty_assessment")
        valid_res = next(r for r in results if r.assessment_key == "test.valid_assessment")
        
        self.assertEqual(faulty_res.status, AssessmentStatus.ERROR)
        self.assertIn("Unhandled exception", faulty_res.summary)
        self.assertIn("traceback", faulty_res.metadata)
        
        self.assertEqual(valid_res.status, AssessmentStatus.COMPLETE)
