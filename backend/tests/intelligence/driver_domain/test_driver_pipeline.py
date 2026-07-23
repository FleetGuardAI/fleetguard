import unittest
from datetime import datetime, timezone

from infrastructure.intelligence.evidence.models import DrivingSessionEvidence, Reliability
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

from infrastructure.intelligence.driver_domain.checks.overspeed import DriverOverspeedCheck
from infrastructure.intelligence.driver_domain.checks.harsh_acceleration import HarshAccelerationCheck
from infrastructure.intelligence.driver_domain.checks.harsh_braking import HarshBrakingCheck
from infrastructure.intelligence.driver_domain.checks.excessive_idling import ExcessiveIdlingCheck
from infrastructure.intelligence.driver_domain.checks.route_compliance import RouteComplianceCheck
from infrastructure.intelligence.driver_domain.assessments.driver_behaviour import DriverBehaviourAssessment
from infrastructure.intelligence.driver_domain.risk.driver_risk import DriverBehaviourRiskEngine
from infrastructure.intelligence.driver_domain.decision.driver_decision import DriverBehaviourDecisionEngine

from infrastructure.intelligence.orchestrator.models import IntelligenceExecutionStatus
from infrastructure.intelligence.global_decision.models import RecommendationStatus


class TestDriverPipeline(unittest.TestCase):
    def setUp(self):
        # Assemble the full driver intelligence pipeline
        check_registry = CheckRegistry()
        check_registry.register(DriverOverspeedCheck)
        check_registry.register(HarshAccelerationCheck)
        check_registry.register(HarshBrakingCheck)
        check_registry.register(ExcessiveIdlingCheck)
        check_registry.register(RouteComplianceCheck)
        check_executor = CheckExecutor(check_registry)
        
        assessment_registry = AssessmentRegistry()
        assessment_registry.register(DriverBehaviourAssessment)
        assessment_executor = AssessmentExecutor(assessment_registry)
        
        risk_registry = DomainRiskRegistry()
        risk_registry.register(DriverBehaviourRiskEngine)
        risk_executor = DomainRiskExecutor(risk_registry)
        
        decision_registry = DecisionRegistry()
        decision_registry.register(DriverBehaviourDecisionEngine)
        decision_executor = DecisionExecutor(decision_registry)
        
        self.orchestrator = IntelligenceOrchestrator(
            check_executor=check_executor,
            assessment_executor=assessment_executor,
            risk_executor=risk_executor,
            decision_executor=decision_executor
        )

    def test_end_to_end_safe_driver(self):
        telemetry = [
            {"timestamp": datetime.now(timezone.utc), "speed_kmh": 80.0, "acceleration_g": 0.1, "latitude": 0.0, "longitude": 0.0, "engine_on": True},
            {"timestamp": datetime.now(timezone.utc), "speed_kmh": 85.0, "acceleration_g": 0.2, "latitude": 0.0001, "longitude": 0.0001, "engine_on": True}
        ]
        route = [{"lat": 0.0, "lon": 0.0}, {"lat": 0.0001, "lon": 0.0001}]
        
        session = DrivingSessionEvidence(
            source="test", origin="test", collected_at=datetime.now(timezone.utc),
            reliability=Reliability.HIGH,
            telemetry_points=telemetry,
            expected_route_polygon=route
        )
        
        result = self.orchestrator.execute(EvidencePackage([session]))
        
        self.assertEqual(result.status, IntelligenceExecutionStatus.COMPLETE)
        self.assertEqual(len(result.recommendations), 1)
        self.assertEqual(result.recommendations[0].recommendation, RecommendationStatus.APPROVE)
        
        # Verify trace explainability
        self.assertEqual(len(result.trace.check_results), 5)
        self.assertEqual(len(result.trace.assessment_results), 1)
        self.assertEqual(len(result.trace.domain_risk_profiles), 1)

    def test_end_to_end_reckless_driver(self):
        # Trigger overspeed and harsh acceleration
        telemetry = [
            {"timestamp": datetime.now(timezone.utc), "speed_kmh": 150.0, "acceleration_g": 0.5, "latitude": 0.0, "longitude": 0.0, "engine_on": True}
        ]
        route = [{"lat": 0.0, "lon": 0.0}]
        
        session = DrivingSessionEvidence(
            source="test", origin="test", collected_at=datetime.now(timezone.utc),
            reliability=Reliability.HIGH,
            telemetry_points=telemetry,
            expected_route_polygon=route
        )
        
        result = self.orchestrator.execute(EvidencePackage([session]))
        
        self.assertEqual(result.status, IntelligenceExecutionStatus.COMPLETE)
        self.assertEqual(len(result.recommendations), 1)
        
        # Two violations = CRITICAL risk -> REJECT
        self.assertEqual(result.recommendations[0].recommendation, RecommendationStatus.REJECT)
        
        # Verify explainability path
        risk_profile = result.trace.domain_risk_profiles[0]
        self.assertEqual(risk_profile.risk_level.value, "CRITICAL")
        
        assessment = risk_profile.supporting_assessments[0]
        self.assertEqual(len(assessment.findings), 2)
        
        failed_checks = [c.check_key for c in assessment.contributing_checks if c.status.value == "FAIL"]
        self.assertIn("driver.overspeed", failed_checks)
        self.assertIn("driver.harsh_acceleration", failed_checks)
