import unittest
from unittest.mock import MagicMock
from datetime import datetime, timezone

from infrastructure.intelligence.evidence.models import ReceiptEvidence, Reliability
from infrastructure.intelligence.evidence.package import EvidencePackage
from infrastructure.intelligence.checks.models import CheckResult, CheckStatus
from infrastructure.intelligence.assessments.models import AssessmentResult, AssessmentStatus
from infrastructure.intelligence.domain_risk.models import DomainRiskProfile, DomainRiskStatus, RiskLevel
from infrastructure.intelligence.global_decision.models import Recommendation, DecisionStatus, RecommendationStatus
from infrastructure.intelligence.orchestrator.base import IntelligenceOrchestrator
from infrastructure.intelligence.orchestrator.models import IntelligenceExecutionStatus


class TestIntelligenceOrchestrator(unittest.TestCase):
    def setUp(self):
        self.check_executor = MagicMock()
        self.assessment_executor = MagicMock()
        self.risk_executor = MagicMock()
        self.decision_executor = MagicMock()
        
        self.orchestrator = IntelligenceOrchestrator(
            check_executor=self.check_executor,
            assessment_executor=self.assessment_executor,
            risk_executor=self.risk_executor,
            decision_executor=self.decision_executor
        )
        
        self.evidence = ReceiptEvidence(
            source="ocr", origin="app", collected_at=datetime.now(timezone.utc),
            reliability=Reliability.HIGH, quantity=100.0, amount=150.0
        )
        self.package = EvidencePackage([self.evidence])

    def test_happy_path_execution(self):
        # Mock outputs
        check_out = [CheckResult(check_key="c1", check_name="c1", status=CheckStatus.PASS, message="")]
        assessment_out = [AssessmentResult(assessment_key="a1", assessment_name="a1", assessment_version="1", status=AssessmentStatus.COMPLETE, summary="")]
        risk_out = [DomainRiskProfile(risk_engine_key="r1", risk_engine_name="r1", risk_engine_version="1", status=DomainRiskStatus.COMPLETE, risk_level=RiskLevel.LOW, summary="")]
        decision_out = [Recommendation(decision_engine_key="d1", decision_engine_name="d1", decision_engine_version="1", status=DecisionStatus.COMPLETE, recommendation=RecommendationStatus.APPROVE, summary="")]
        
        self.check_executor.execute_all.return_value = check_out
        self.assessment_executor.execute_all.return_value = assessment_out
        self.risk_executor.execute_all.return_value = risk_out
        self.decision_executor.execute_all.return_value = decision_out
        
        result = self.orchestrator.execute(self.package)
        
        # Verify status
        self.assertEqual(result.status, IntelligenceExecutionStatus.COMPLETE)
        
        # Verify trace preservation
        self.assertEqual(result.trace.evidence_package, self.package)
        self.assertEqual(result.trace.check_results, check_out)
        self.assertEqual(result.trace.assessment_results, assessment_out)
        self.assertEqual(result.trace.domain_risk_profiles, risk_out)
        self.assertEqual(result.recommendations, decision_out)
        
        # Verify execution order (each layer consumes the output of the previous)
        self.check_executor.execute_all.assert_called_once_with(self.package)
        self.assessment_executor.execute_all.assert_called_once_with(check_out)
        self.risk_executor.execute_all.assert_called_once_with(assessment_out)
        self.decision_executor.execute_all.assert_called_once_with(risk_out)
        
        # Verify timing
        self.assertGreater(result.execution_time, 0.0)

    def test_catastrophic_failure_isolation(self):
        # Simulate an unexpected exception in one of the layers (e.g. Risk Executor blows up)
        self.check_executor.execute_all.return_value = []
        self.assessment_executor.execute_all.return_value = []
        self.risk_executor.execute_all.side_effect = RuntimeError("Out of memory")
        
        result = self.orchestrator.execute(self.package)
        
        self.assertEqual(result.status, IntelligenceExecutionStatus.ERROR)
        self.assertEqual(result.recommendations, [])
        self.assertIn("error", result.metadata)
        self.assertEqual(result.metadata["error"], "Out of memory")

    def test_partial_pipeline_failure(self):
        # Simulate a scenario where early stages succeed, but a later stage yields an error 
        # (This is handled by the executors themselves, so the orchestrator should still complete)
        check_out = [CheckResult(check_key="c1", check_name="c1", status=CheckStatus.PASS, message="")]
        assessment_out = [AssessmentResult(assessment_key="a1", assessment_name="a1", assessment_version="1", status=AssessmentStatus.COMPLETE, summary="")]
        # Risk outputs an ERROR profile (handled by framework, not an exception)
        risk_out = [DomainRiskProfile(risk_engine_key="r1", risk_engine_name="r1", risk_engine_version="1", status=DomainRiskStatus.ERROR, risk_level=RiskLevel.UNKNOWN, summary="Crash")]
        # Decision outputs ERROR recommendation
        decision_out = [Recommendation(decision_engine_key="d1", decision_engine_name="d1", decision_engine_version="1", status=DecisionStatus.ERROR, recommendation=None, summary="Crash")]
        
        self.check_executor.execute_all.return_value = check_out
        self.assessment_executor.execute_all.return_value = assessment_out
        self.risk_executor.execute_all.return_value = risk_out
        self.decision_executor.execute_all.return_value = decision_out
        
        result = self.orchestrator.execute(self.package)
        
        # The orchestrator succeeded in running the pipeline, even though the pipeline results contain errors
        self.assertEqual(result.status, IntelligenceExecutionStatus.COMPLETE)
        self.assertEqual(result.recommendations, decision_out)
        
        # Verify intermediate trace is perfectly preserved despite the logical failures
        self.assertEqual(result.trace.check_results, check_out)
        self.assertEqual(result.trace.assessment_results, assessment_out)
        self.assertEqual(result.trace.domain_risk_profiles, risk_out)
