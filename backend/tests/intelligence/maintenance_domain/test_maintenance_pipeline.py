import unittest
from datetime import datetime, timedelta, timezone

from infrastructure.intelligence.evidence.models import MaintenanceHistoryEvidence, MaintenanceScheduleEvidence, Reliability
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

from infrastructure.intelligence.maintenance_domain.checks.service_overdue import MaintenanceServiceOverdueCheck
from infrastructure.intelligence.maintenance_domain.checks.distance_overdue import MaintenanceDistanceOverdueCheck
from infrastructure.intelligence.maintenance_domain.checks.time_overdue import MaintenanceTimeOverdueCheck
from infrastructure.intelligence.maintenance_domain.checks.repeated_failures import RepeatedFailureCheck
from infrastructure.intelligence.maintenance_domain.checks.critical_component_due import CriticalComponentDueCheck
from infrastructure.intelligence.maintenance_domain.assessments.vehicle_health import VehicleHealthAssessment
from infrastructure.intelligence.maintenance_domain.risk.vehicle_health_risk import VehicleHealthRiskEngine
from infrastructure.intelligence.maintenance_domain.decision.vehicle_health_decision import VehicleHealthDecisionEngine

from infrastructure.intelligence.orchestrator.models import IntelligenceExecutionStatus
from infrastructure.intelligence.global_decision.models import RecommendationStatus


class TestMaintenancePipeline(unittest.TestCase):
    def setUp(self):
        check_registry = CheckRegistry()
        check_registry.register(MaintenanceServiceOverdueCheck)
        check_registry.register(MaintenanceDistanceOverdueCheck)
        check_registry.register(MaintenanceTimeOverdueCheck)
        check_registry.register(RepeatedFailureCheck)
        check_registry.register(CriticalComponentDueCheck)
        check_executor = CheckExecutor(check_registry)
        
        assessment_registry = AssessmentRegistry()
        assessment_registry.register(VehicleHealthAssessment)
        assessment_executor = AssessmentExecutor(assessment_registry)
        
        risk_registry = DomainRiskRegistry()
        risk_registry.register(VehicleHealthRiskEngine)
        risk_executor = DomainRiskExecutor(risk_registry)
        
        decision_registry = DecisionRegistry()
        decision_registry.register(VehicleHealthDecisionEngine)
        decision_executor = DecisionExecutor(decision_registry)
        
        self.orchestrator = IntelligenceOrchestrator(
            check_executor=check_executor,
            assessment_executor=assessment_executor,
            risk_executor=risk_executor,
            decision_executor=decision_executor
        )
        
        self.now = datetime.now(timezone.utc)

    def test_end_to_end_healthy_vehicle(self):
        history = MaintenanceHistoryEvidence(
            source="test", origin="test", collected_at=self.now,
            reliability=Reliability.HIGH,
            vehicle_id="v1",
            service_date=self.now - timedelta(days=10),
            odometer_km=50000.0,
            service_type="general",
            reported_component_failures=[],
            diagnostic_codes=[]
        )
        
        schedule = MaintenanceScheduleEvidence(
            source="test", origin="test", collected_at=self.now,
            reliability=Reliability.HIGH,
            vehicle_id="v1",
            next_service_due_date=self.now + timedelta(days=170),
            next_service_due_km=60000.0
        )
        
        result = self.orchestrator.execute(EvidencePackage([history, schedule]))
        
        self.assertEqual(result.status, IntelligenceExecutionStatus.COMPLETE)
        self.assertEqual(len(result.recommendations), 1)
        self.assertEqual(result.recommendations[0].recommendation, RecommendationStatus.APPROVE)
        
        # Verify trace explainability
        self.assertEqual(len(result.trace.check_results), 5)
        self.assertEqual(len(result.trace.assessment_results), 1)
        self.assertEqual(len(result.trace.domain_risk_profiles), 1)

    def test_end_to_end_critical_vehicle(self):
        history = MaintenanceHistoryEvidence(
            source="test", origin="test", collected_at=self.now,
            reliability=Reliability.HIGH,
            vehicle_id="v1",
            service_date=self.now - timedelta(days=10),
            odometer_km=50000.0,
            service_type="general",
            reported_component_failures=[],
            diagnostic_codes=["CRIT_BRAKE_01"]
        )
        
        schedule = MaintenanceScheduleEvidence(
            source="test", origin="test", collected_at=self.now,
            reliability=Reliability.HIGH,
            vehicle_id="v1",
            next_service_due_date=self.now + timedelta(days=170),
            next_service_due_km=60000.0
        )
        
        result = self.orchestrator.execute(EvidencePackage([history, schedule]))
        
        self.assertEqual(result.status, IntelligenceExecutionStatus.COMPLETE)
        self.assertEqual(len(result.recommendations), 1)
        
        # Critical risk -> REJECT
        self.assertEqual(result.recommendations[0].recommendation, RecommendationStatus.REJECT)
        
        # Verify explainability path
        risk_profile = result.trace.domain_risk_profiles[0]
        self.assertEqual(risk_profile.risk_level.value, "CRITICAL")
        
        assessment = risk_profile.supporting_assessments[0]
        failed_checks = [c.check_key for c in assessment.contributing_checks if c.status.value == "FAIL"]
        self.assertIn("maintenance.critical_component_due", failed_checks)
