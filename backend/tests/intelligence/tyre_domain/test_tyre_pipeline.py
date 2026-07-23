import unittest
from datetime import datetime, timedelta, timezone

from infrastructure.intelligence.evidence.models import (
    TyreInspectionEvidence,
    TyrePressureEvidence,
    Reliability,
    TyrePosition,
    WearPatternCategory,
    DamageSeverity
)
from infrastructure.intelligence.evidence.package import EvidencePackage

from infrastructure.intelligence.orchestrator.base import IntelligenceOrchestrator
from infrastructure.intelligence.checks.registry import CheckRegistry
from infrastructure.intelligence.checks.executor import CheckExecutor
from infrastructure.intelligence.assessments.registry import AssessmentRegistry
from infrastructure.intelligence.assessments.executor import AssessmentExecutor
from infrastructure.intelligence.domain_risk.registry import DomainRiskRegistry
from infrastructure.intelligence.domain_risk.executor import DomainRiskExecutor
from infrastructure.intelligence.global_decision.registry import DecisionRegistry
from infrastructure.intelligence.global_decision.executor import DecisionExecutor

from infrastructure.intelligence.tyre_domain.checks.pressure import TyrePressureCheck
from infrastructure.intelligence.tyre_domain.checks.tread_depth import TyreTreadDepthCheck
from infrastructure.intelligence.tyre_domain.checks.age import TyreAgeCheck
from infrastructure.intelligence.tyre_domain.checks.wear_pattern import TyreWearPatternCheck
from infrastructure.intelligence.tyre_domain.checks.damage import TyreDamageCheck
from infrastructure.intelligence.tyre_domain.assessments.health import TyreHealthAssessment
from infrastructure.intelligence.tyre_domain.risk.health_risk import TyreHealthRiskEngine
from infrastructure.intelligence.tyre_domain.decision.health_decision import TyreHealthDecisionEngine

from infrastructure.intelligence.orchestrator.models import IntelligenceExecutionStatus
from infrastructure.intelligence.global_decision.models import RecommendationStatus


class TestTyrePipeline(unittest.TestCase):
    def setUp(self):
        check_registry = CheckRegistry()
        check_registry.register(TyrePressureCheck)
        check_registry.register(TyreTreadDepthCheck)
        check_registry.register(TyreAgeCheck)
        check_registry.register(TyreWearPatternCheck)
        check_registry.register(TyreDamageCheck)
        check_executor = CheckExecutor(check_registry)
        
        assessment_registry = AssessmentRegistry()
        assessment_registry.register(TyreHealthAssessment)
        assessment_executor = AssessmentExecutor(assessment_registry)
        
        risk_registry = DomainRiskRegistry()
        risk_registry.register(TyreHealthRiskEngine)
        risk_executor = DomainRiskExecutor(risk_registry)
        
        decision_registry = DecisionRegistry()
        decision_registry.register(TyreHealthDecisionEngine)
        decision_executor = DecisionExecutor(decision_registry)
        
        self.orchestrator = IntelligenceOrchestrator(
            check_executor=check_executor,
            assessment_executor=assessment_executor,
            risk_executor=risk_executor,
            decision_executor=decision_executor
        )
        
        self.now = datetime.now(timezone.utc)

    def test_end_to_end_healthy_tyre(self):
        inspection = TyreInspectionEvidence(
            source="test", origin="test", collected_at=self.now,
            reliability=Reliability.HIGH,
            vehicle_id="v1",
            tyre_position=TyrePosition.FRONT_LEFT,
            inspection_date=self.now,
            tread_depth_mm=5.0,
            tyre_installation_date=self.now - timedelta(days=365),
            wear_pattern=WearPatternCategory.NORMAL,
            observed_damage_severity=DamageSeverity.NONE
        )
        
        pressure = TyrePressureEvidence(
            source="test", origin="test", collected_at=self.now,
            reliability=Reliability.HIGH,
            vehicle_id="v1",
            tyre_position=TyrePosition.FRONT_LEFT,
            reading_date=self.now,
            tyre_pressure_psi=32.0,
            recommended_pressure_psi=32.0
        )
        
        result = self.orchestrator.execute(EvidencePackage([inspection, pressure]))
        
        self.assertEqual(result.status, IntelligenceExecutionStatus.COMPLETE)
        self.assertEqual(len(result.recommendations), 1)
        self.assertEqual(result.recommendations[0].recommendation, RecommendationStatus.APPROVE)
        
        # Verify trace explainability
        self.assertEqual(len(result.trace.check_results), 5)
        self.assertEqual(len(result.trace.assessment_results), 1)
        self.assertEqual(len(result.trace.domain_risk_profiles), 1)

    def test_end_to_end_critical_tyre(self):
        inspection = TyreInspectionEvidence(
            source="test", origin="test", collected_at=self.now,
            reliability=Reliability.HIGH,
            vehicle_id="v1",
            tyre_position=TyrePosition.FRONT_LEFT,
            inspection_date=self.now,
            tread_depth_mm=1.0, # Below 2.0 limit -> CRITICAL safety finding
            tyre_installation_date=self.now - timedelta(days=365),
            wear_pattern=WearPatternCategory.UNEVEN,
            observed_damage_severity=DamageSeverity.CRITICAL # CRITICAL
        )
        
        pressure = TyrePressureEvidence(
            source="test", origin="test", collected_at=self.now,
            reliability=Reliability.HIGH,
            vehicle_id="v1",
            tyre_position=TyrePosition.FRONT_LEFT,
            reading_date=self.now,
            tyre_pressure_psi=32.0,
            recommended_pressure_psi=32.0
        )
        
        result = self.orchestrator.execute(EvidencePackage([inspection, pressure]))
        
        self.assertEqual(result.status, IntelligenceExecutionStatus.COMPLETE)
        self.assertEqual(len(result.recommendations), 1)
        
        # Critical risk -> REJECT
        self.assertEqual(result.recommendations[0].recommendation, RecommendationStatus.REJECT)
        
        # Verify explainability path
        risk_profile = result.trace.domain_risk_profiles[0]
        self.assertEqual(risk_profile.risk_level.value, "CRITICAL")
        
        assessment = risk_profile.supporting_assessments[0]
        failed_checks = [c.check_key for c in assessment.contributing_checks if c.status.value == "FAIL"]
        self.assertIn("tyre.tread_depth", failed_checks)
        self.assertIn("tyre.wear_pattern", failed_checks)
        self.assertIn("tyre.damage", failed_checks)
