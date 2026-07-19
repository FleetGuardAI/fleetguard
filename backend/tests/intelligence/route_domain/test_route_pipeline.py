import unittest
from datetime import datetime, timedelta, timezone
import uuid

from infrastructure.intelligence.evidence.package import EvidencePackage
from infrastructure.intelligence.evidence.models import (
    PlannedRouteEvidence, TripExecutionEvidence, ApprovedStopEvidence, GeofenceEventEvidence, GeofenceEventType, Reliability
)

from infrastructure.intelligence.orchestrator.base import IntelligenceOrchestrator
from infrastructure.intelligence.checks.registry import CheckRegistry
from infrastructure.intelligence.checks.executor import CheckExecutor
from infrastructure.intelligence.assessments.registry import AssessmentRegistry
from infrastructure.intelligence.assessments.executor import AssessmentExecutor
from infrastructure.intelligence.domain_risk.registry import DomainRiskRegistry
from infrastructure.intelligence.domain_risk.executor import DomainRiskExecutor
from infrastructure.intelligence.global_decision.registry import DecisionRegistry
from infrastructure.intelligence.global_decision.executor import DecisionExecutor
from infrastructure.intelligence.orchestrator.models import IntelligenceExecutionStatus

from infrastructure.intelligence.route_domain.checks.deviation import RouteDeviationCheck
from infrastructure.intelligence.route_domain.checks.trip_delay import TripDelayCheck
from infrastructure.intelligence.route_domain.checks.unauthorized_stop import UnauthorizedStopCheck
from infrastructure.intelligence.route_domain.checks.geofence_violation import GeofenceViolationCheck
from infrastructure.intelligence.route_domain.checks.excessive_detour import ExcessiveDetourCheck
from infrastructure.intelligence.route_domain.assessments.trip_compliance import TripComplianceAssessment
from infrastructure.intelligence.route_domain.risk.compliance_risk import TripComplianceRiskEngine
from infrastructure.intelligence.route_domain.decision.compliance_decision import TripComplianceDecisionEngine
from infrastructure.intelligence.global_decision.models import RecommendationStatus


class TestRoutePipeline(unittest.TestCase):
    def setUp(self):
        check_registry = CheckRegistry()
        check_registry.register(RouteDeviationCheck)
        check_registry.register(TripDelayCheck)
        check_registry.register(UnauthorizedStopCheck)
        check_registry.register(GeofenceViolationCheck)
        check_registry.register(ExcessiveDetourCheck)
        check_executor = CheckExecutor(check_registry)
        
        assessment_registry = AssessmentRegistry()
        assessment_registry.register(TripComplianceAssessment)
        assessment_executor = AssessmentExecutor(assessment_registry)
        
        risk_registry = DomainRiskRegistry()
        risk_registry.register(TripComplianceRiskEngine)
        risk_executor = DomainRiskExecutor(risk_registry)
        
        decision_registry = DecisionRegistry()
        decision_registry.register(TripComplianceDecisionEngine)
        decision_executor = DecisionExecutor(decision_registry)
        
        self.orchestrator = IntelligenceOrchestrator(
            check_executor=check_executor,
            assessment_executor=assessment_executor,
            risk_executor=risk_executor,
            decision_executor=decision_executor
        )
        
        now = datetime.now(timezone.utc)
        self.planned_evidence = PlannedRouteEvidence(
            source="planner", origin="api", collected_at=now, reliability=Reliability.HIGH,
            trip_id="trip-1", planned_route_id="route-1", vehicle_id="v-1",
            planned_start_time=now, planned_end_time=now + timedelta(hours=1),
            gps_track=[{"lat": 0.0, "lon": 0.0}, {"lat": 0.1, "lon": 0.1}]
        )
        self.approved_stops = ApprovedStopEvidence(
            source="config", origin="api", collected_at=now, reliability=Reliability.HIGH,
            trip_id="trip-1", approved_stops=[{"lat": 0.05, "lon": 0.05, "radius_meters": 200}]
        )
        self.now = now

    def test_end_to_end_compliant_trip(self):
        exec_evidence = TripExecutionEvidence(
            source="gps", origin="device", collected_at=self.now, reliability=Reliability.HIGH,
            trip_id="trip-1", vehicle_id="v-1", actual_start_time=self.now, actual_end_time=self.now + timedelta(minutes=50),
            gps_track=[{"lat": 0.0, "lon": 0.0, "timestamp": self.now, "speed": 50}, {"lat": 0.1, "lon": 0.1, "timestamp": self.now, "speed": 50}],
            stop_locations=[]
        )
        result = self.orchestrator.execute(EvidencePackage([self.planned_evidence, exec_evidence, self.approved_stops]))
        
        self.assertEqual(result.status, IntelligenceExecutionStatus.COMPLETE)
        self.assertEqual(result.recommendations[0].recommendation, RecommendationStatus.APPROVE)

    def test_end_to_end_critical_trip(self):
        geofence_event = GeofenceEventEvidence(
            source="geofence", origin="system", collected_at=self.now, reliability=Reliability.HIGH,
            vehicle_id="v-1", geofence_id="restricted-1", event_type=GeofenceEventType.ENTER,
            event_time=self.now, latitude=0.1, longitude=0.1
        )
        exec_evidence = TripExecutionEvidence(
            source="gps", origin="device", collected_at=self.now, reliability=Reliability.HIGH,
            trip_id="trip-1", vehicle_id="v-1", actual_start_time=self.now, actual_end_time=self.now + timedelta(minutes=50),
            gps_track=[{"lat": 0.0, "lon": 0.0, "timestamp": self.now, "speed": 50}, {"lat": 0.1, "lon": 0.1, "timestamp": self.now, "speed": 50}],
            stop_locations=[]
        )
        
        from infrastructure.intelligence.route_domain.config import RouteIntelligenceConfig
        original_init = RouteIntelligenceConfig.__init__
        def mocked_init(self, **kwargs):
            kwargs["restricted_geofence_ids"] = ["restricted-1"]
            original_init(self, **kwargs)
            
        RouteIntelligenceConfig.__init__ = mocked_init
        
        result = self.orchestrator.execute(EvidencePackage([self.planned_evidence, exec_evidence, self.approved_stops, geofence_event]))
        
        RouteIntelligenceConfig.__init__ = original_init
        
        self.assertEqual(result.status, IntelligenceExecutionStatus.COMPLETE)
        self.assertEqual(result.recommendations[0].recommendation, RecommendationStatus.REJECT)
