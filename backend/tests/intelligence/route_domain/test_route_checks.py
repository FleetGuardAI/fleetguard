import unittest
from datetime import datetime, timedelta
import uuid

from infrastructure.intelligence.evidence.package import EvidencePackage
from infrastructure.intelligence.evidence.models import (
    PlannedRouteEvidence, TripExecutionEvidence, ApprovedStopEvidence, GeofenceEventEvidence, GeofenceEventType, Reliability
)
from infrastructure.intelligence.route_domain.checks.deviation import RouteDeviationCheck
from infrastructure.intelligence.route_domain.checks.trip_delay import TripDelayCheck
from infrastructure.intelligence.route_domain.checks.unauthorized_stop import UnauthorizedStopCheck
from infrastructure.intelligence.route_domain.checks.geofence_violation import GeofenceViolationCheck
from infrastructure.intelligence.route_domain.checks.excessive_detour import ExcessiveDetourCheck
from infrastructure.intelligence.checks.models import CheckStatus


class TestRouteChecks(unittest.TestCase):
    def setUp(self):
        now = datetime.utcnow()
        self.planned_evidence = PlannedRouteEvidence(
            source="planner", origin="api", collected_at=now, reliability=Reliability.HIGH,
            trip_id="trip-1", planned_route_id="route-1", vehicle_id="v-1",
            planned_start_time=now, planned_end_time=now + timedelta(hours=1),
            gps_track=[{"lat": 0.0, "lon": 0.0}, {"lat": 0.1, "lon": 0.1}]
        )
        self.exec_evidence = TripExecutionEvidence(
            source="gps", origin="device", collected_at=now, reliability=Reliability.HIGH,
            trip_id="trip-1", vehicle_id="v-1", actual_start_time=now, actual_end_time=now + timedelta(hours=1, minutes=10),
            gps_track=[{"lat": 0.0, "lon": 0.0, "timestamp": now, "speed": 50}, {"lat": 0.1, "lon": 0.1, "timestamp": now, "speed": 50}],
            stop_locations=[{"lat": 0.05, "lon": 0.05, "duration_minutes": 10, "start_time": now}]
        )
        self.approved_stops = ApprovedStopEvidence(
            source="config", origin="api", collected_at=now, reliability=Reliability.HIGH,
            trip_id="trip-1", approved_stops=[{"lat": 0.05, "lon": 0.05, "radius_meters": 200}]
        )
        self.geofence_event = GeofenceEventEvidence(
            source="geofence", origin="system", collected_at=now, reliability=Reliability.HIGH,
            vehicle_id="v-1", geofence_id="restricted-1", event_type=GeofenceEventType.ENTER,
            event_time=now, latitude=0.1, longitude=0.1
        )
        self.package = EvidencePackage([self.planned_evidence, self.exec_evidence, self.approved_stops, self.geofence_event])

    def test_deviation_pass(self):
        check = RouteDeviationCheck()
        res = check.execute(self.package)
        self.assertEqual(res.status, CheckStatus.PASS)

    def test_deviation_fail(self):
        check = RouteDeviationCheck()
        # Create an execution with a large deviation (lat 0.5, lon 0.5 is far from the route)
        bad_exec = TripExecutionEvidence(
            source="gps", origin="device", collected_at=datetime.utcnow(), reliability=Reliability.HIGH,
            trip_id="trip-1", vehicle_id="v-1", actual_start_time=datetime.utcnow(), actual_end_time=datetime.utcnow(),
            gps_track=[{"lat": 0.5, "lon": 0.5, "timestamp": datetime.utcnow(), "speed": 50}]
        )
        package = EvidencePackage([self.planned_evidence, bad_exec])
        res = check.execute(package)
        self.assertEqual(res.status, CheckStatus.FAIL)

    def test_trip_delay_pass(self):
        check = TripDelayCheck()
        res = check.execute(self.package)
        self.assertEqual(res.status, CheckStatus.PASS)

    def test_trip_delay_fail(self):
        check = TripDelayCheck()
        bad_exec = TripExecutionEvidence(
            source="gps", origin="device", collected_at=datetime.utcnow(), reliability=Reliability.HIGH,
            trip_id="trip-1", vehicle_id="v-1", actual_start_time=datetime.utcnow(), actual_end_time=datetime.utcnow() + timedelta(hours=3),
            gps_track=[]
        )
        package = EvidencePackage([self.planned_evidence, bad_exec])
        res = check.execute(package)
        self.assertEqual(res.status, CheckStatus.FAIL)

    def test_unauthorized_stop_pass(self):
        check = UnauthorizedStopCheck()
        res = check.execute(self.package)
        self.assertEqual(res.status, CheckStatus.PASS)

    def test_unauthorized_stop_fail(self):
        check = UnauthorizedStopCheck()
        bad_exec = TripExecutionEvidence(
            source="gps", origin="device", collected_at=datetime.utcnow(), reliability=Reliability.HIGH,
            trip_id="trip-1", vehicle_id="v-1", actual_start_time=datetime.utcnow(), actual_end_time=datetime.utcnow(),
            gps_track=[],
            stop_locations=[{"lat": 0.9, "lon": 0.9, "duration_minutes": 60, "start_time": datetime.utcnow()}]
        )
        package = EvidencePackage([bad_exec, self.approved_stops])
        res = check.execute(package)
        self.assertEqual(res.status, CheckStatus.FAIL)

    def test_geofence_violation_fail(self):
        check = GeofenceViolationCheck()
        check.config = check.config.model_copy(update={"restricted_geofence_ids": ["restricted-1"]})
        res = check.execute(self.package)
        self.assertEqual(res.status, CheckStatus.FAIL)

    def test_excessive_detour_pass(self):
        check = ExcessiveDetourCheck()
        res = check.execute(self.package)
        self.assertEqual(res.status, CheckStatus.PASS)

    def test_excessive_detour_fail(self):
        check = ExcessiveDetourCheck()
        bad_exec = TripExecutionEvidence(
            source="gps", origin="device", collected_at=datetime.utcnow(), reliability=Reliability.HIGH,
            trip_id="trip-1", vehicle_id="v-1", actual_start_time=datetime.utcnow(), actual_end_time=datetime.utcnow(),
            gps_track=[{"lat": 0.0, "lon": 0.0}, {"lat": 0.0, "lon": 1.0}, {"lat": 1.0, "lon": 1.0}, {"lat": 0.1, "lon": 0.1}]
        )
        package = EvidencePackage([self.planned_evidence, bad_exec])
        res = check.execute(package)
        self.assertEqual(res.status, CheckStatus.FAIL)
