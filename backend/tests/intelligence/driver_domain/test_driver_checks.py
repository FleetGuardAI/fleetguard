import unittest
from datetime import datetime, timezone

from infrastructure.intelligence.evidence.models import DrivingSessionEvidence, Reliability
from infrastructure.intelligence.evidence.package import EvidencePackage
from infrastructure.intelligence.checks.models import CheckStatus
from infrastructure.intelligence.driver_domain.config import DriverIntelligenceConfig
from infrastructure.intelligence.driver_domain.checks.overspeed import DriverOverspeedCheck
from infrastructure.intelligence.driver_domain.checks.harsh_acceleration import HarshAccelerationCheck
from infrastructure.intelligence.driver_domain.checks.harsh_braking import HarshBrakingCheck
from infrastructure.intelligence.driver_domain.checks.excessive_idling import ExcessiveIdlingCheck
from infrastructure.intelligence.driver_domain.checks.route_compliance import RouteComplianceCheck


class TestDriverChecks(unittest.TestCase):
    def setUp(self):
        self.config = DriverIntelligenceConfig(
            max_speed_kmh=100.0,
            harsh_acceleration_g=0.3,
            harsh_braking_g=-0.3,
            max_idle_seconds=60,
            route_deviation_meters=100.0
        )
        
        # Good session
        self.good_telemetry = [
            {"timestamp": datetime.now(timezone.utc), "speed_kmh": 80.0, "acceleration_g": 0.1, "latitude": 0.0, "longitude": 0.0, "engine_on": True},
            {"timestamp": datetime.now(timezone.utc), "speed_kmh": 85.0, "acceleration_g": 0.2, "latitude": 0.0001, "longitude": 0.0001, "engine_on": True}
        ]
        self.good_route = [{"lat": 0.0, "lon": 0.0}, {"lat": 0.0001, "lon": 0.0001}]
        
        self.session = DrivingSessionEvidence(
            source="test", origin="test", collected_at=datetime.now(timezone.utc),
            reliability=Reliability.HIGH,
            telemetry_points=self.good_telemetry,
            expected_route_polygon=self.good_route
        )
        self.package = EvidencePackage([self.session])

    def test_overspeed_pass(self):
        check = DriverOverspeedCheck(self.config)
        res = check.execute(self.package)
        self.assertEqual(res.status, CheckStatus.PASS)

    def test_overspeed_fail(self):
        check = DriverOverspeedCheck(self.config)
        bad_session = self.session.model_copy(deep=True, update={"telemetry_points": [{"speed_kmh": 120.0}]})
        res = check.execute(EvidencePackage([bad_session]))
        self.assertEqual(res.status, CheckStatus.FAIL)

    def test_acceleration_pass(self):
        check = HarshAccelerationCheck(self.config)
        res = check.execute(self.package)
        self.assertEqual(res.status, CheckStatus.PASS)

    def test_acceleration_fail(self):
        check = HarshAccelerationCheck(self.config)
        bad_session = self.session.model_copy(deep=True, update={"telemetry_points": [{"acceleration_g": 0.4}]})
        res = check.execute(EvidencePackage([bad_session]))
        self.assertEqual(res.status, CheckStatus.FAIL)

    def test_braking_pass(self):
        check = HarshBrakingCheck(self.config)
        res = check.execute(self.package)
        self.assertEqual(res.status, CheckStatus.PASS)

    def test_braking_fail(self):
        check = HarshBrakingCheck(self.config)
        bad_session = self.session.model_copy(deep=True, update={"telemetry_points": [{"acceleration_g": -0.5}]})
        res = check.execute(EvidencePackage([bad_session]))
        self.assertEqual(res.status, CheckStatus.FAIL)

    def test_idling_pass(self):
        check = ExcessiveIdlingCheck(self.config)
        # only 1 idle point in setup, config allows 60
        idle_points = [{"speed_kmh": 0.0, "engine_on": True}] * 10 
        session = self.session.model_copy(deep=True, update={"telemetry_points": idle_points})
        res = check.execute(EvidencePackage([session]))
        self.assertEqual(res.status, CheckStatus.PASS)

    def test_idling_fail(self):
        check = ExcessiveIdlingCheck(self.config)
        idle_points = [{"speed_kmh": 0.0, "engine_on": True}] * 61 
        session = self.session.model_copy(deep=True, update={"telemetry_points": idle_points})
        res = check.execute(EvidencePackage([session]))
        self.assertEqual(res.status, CheckStatus.FAIL)

    def test_route_pass(self):
        check = RouteComplianceCheck(self.config)
        res = check.execute(self.package)
        self.assertEqual(res.status, CheckStatus.PASS)

    def test_route_fail(self):
        check = RouteComplianceCheck(self.config)
        # Lat=1.0 is ~111km away, well beyond 100m
        bad_session = self.session.model_copy(deep=True, update={"telemetry_points": [{"latitude": 1.0, "longitude": 1.0}]})
        res = check.execute(EvidencePackage([bad_session]))
        self.assertEqual(res.status, CheckStatus.FAIL)
