import unittest
from typing import List
from pydantic import ValidationError

from infrastructure.intelligence.assessments.models import AssessmentResult, AssessmentStatus
from infrastructure.intelligence.domain_risk.models import DomainRiskStatus, RiskLevel, RiskFinding, DomainRiskProfile
from infrastructure.intelligence.domain_risk.base import BaseDomainRiskEngine
from infrastructure.intelligence.domain_risk.registry import DomainRiskRegistry
from infrastructure.intelligence.domain_risk.executor import DomainRiskExecutor


# Dummy Risk Engines for Testing
class ValidRiskEngine(BaseDomainRiskEngine):
    @classmethod
    def key(cls) -> str:
        return "test.valid_risk"

    @classmethod
    def required_assessments(cls) -> List[str]:
        return ["test.assessment_1"]

    def execute(self, assessments: List[AssessmentResult]) -> DomainRiskProfile:
        # Filter for the assessments we care about, ignoring unrelated ones
        relevant = [a for a in assessments if a.assessment_key in self.required_assessments()]
        relevant_keys = [a.assessment_key for a in relevant]
        
        missing = [req for req in self.required_assessments() if req not in relevant_keys]
        if missing:
            return DomainRiskProfile(
                risk_engine_key=self.key(),
                risk_engine_name=self.name(),
                risk_engine_version=self.version(),
                status=DomainRiskStatus.INCONCLUSIVE,
                risk_level=RiskLevel.UNKNOWN,
                summary=f"Missing required assessments: {missing}",
                supporting_assessments=relevant
            )
            
        finding = RiskFinding(
            finding_key="test.finding.risk",
            category="Test",
            summary="High risk detected.",
            details="The assessment was completed and high risk was quantified."
        )
        
        return DomainRiskProfile(
            risk_engine_key=self.key(),
            risk_engine_name=self.name(),
            risk_engine_version=self.version(),
            status=DomainRiskStatus.COMPLETE,
            risk_level=RiskLevel.HIGH,
            summary="High risk.",
            findings=[finding],
            supporting_assessments=relevant
        )

class FaultyRiskEngine(BaseDomainRiskEngine):
    @classmethod
    def key(cls) -> str:
        return "test.faulty_risk"

    @classmethod
    def required_assessments(cls) -> List[str]:
        return []

    def execute(self, assessments: List[AssessmentResult]) -> DomainRiskProfile:
        raise ValueError("Unexpected failure in risk engine!")


class TestDomainRiskFramework(unittest.TestCase):
    
    def setUp(self):
        self.registry = DomainRiskRegistry()
        self.executor = DomainRiskExecutor(self.registry)
        
        self.assessment1 = AssessmentResult(
            assessment_key="test.assessment_1",
            assessment_name="Assessment 1",
            assessment_version="1.0",
            status=AssessmentStatus.COMPLETE,
            summary="Assessment 1 complete",
            findings=[],
            contributing_checks=[]
        )
        
        # Unrelated assessment
        self.assessment_unrelated = AssessmentResult(
            assessment_key="test.assessment_unrelated",
            assessment_name="Unrelated Assessment",
            assessment_version="1.0",
            status=AssessmentStatus.COMPLETE,
            summary="Unrelated",
            findings=[],
            contributing_checks=[]
        )

    def test_risk_engine_registration_and_lookup(self):
        self.registry.register(ValidRiskEngine)
        
        with self.assertRaises(ValueError):
            self.registry.register(ValidRiskEngine)
            
        cls = self.registry.get_engine("test.valid_risk")
        self.assertEqual(cls, ValidRiskEngine)
        
        with self.assertRaises(ValueError):
            self.registry.get_engine("unknown")
            
        self.registry.register(FaultyRiskEngine)
        engines = self.registry.enumerate_engines()
        self.assertEqual(engines[0].key(), "test.faulty_risk")
        self.assertEqual(engines[1].key(), "test.valid_risk")

    def test_executor_missing_required_assessments(self):
        self.registry.register(ValidRiskEngine)
        
        # Empty assessments
        results = self.executor.execute_all([])
        
        self.assertEqual(len(results), 1)
        res = results[0]
        self.assertEqual(res.status, DomainRiskStatus.INCONCLUSIVE)
        self.assertEqual(res.risk_level, RiskLevel.UNKNOWN)
        self.assertIn("test.assessment_1", res.summary)

    def test_executor_ignores_unrelated_assessments(self):
        self.registry.register(ValidRiskEngine)
        
        # Has assessment 1 and unrelated
        results = self.executor.execute_all([self.assessment1, self.assessment_unrelated])
        
        self.assertEqual(len(results), 1)
        res = results[0]
        self.assertEqual(res.status, DomainRiskStatus.COMPLETE)
        self.assertEqual(res.risk_level, RiskLevel.HIGH)
        
        # Engine should filter supporting assessments to only include the relevant one
        self.assertEqual(len(res.supporting_assessments), 1)
        self.assertEqual(res.supporting_assessments[0].assessment_key, "test.assessment_1")

    def test_executor_isolates_faults(self):
        self.registry.register(ValidRiskEngine)
        self.registry.register(FaultyRiskEngine)
        
        results = self.executor.execute_all([self.assessment1])
        
        self.assertEqual(len(results), 2)
        
        faulty_res = next(r for r in results if r.risk_engine_key == "test.faulty_risk")
        valid_res = next(r for r in results if r.risk_engine_key == "test.valid_risk")
        
        # Faulty should have ERROR status and UNKNOWN risk
        self.assertEqual(faulty_res.status, DomainRiskStatus.ERROR)
        self.assertEqual(faulty_res.risk_level, RiskLevel.UNKNOWN)
        self.assertIn("Unhandled exception", faulty_res.summary)
        self.assertIn("traceback", faulty_res.metadata)
        
        # Valid should still complete successfully
        self.assertEqual(valid_res.status, DomainRiskStatus.COMPLETE)
        self.assertEqual(valid_res.risk_level, RiskLevel.HIGH)
