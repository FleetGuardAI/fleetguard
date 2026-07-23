import unittest
from datetime import datetime, timezone

from infrastructure.intelligence.evidence.models import ReceiptEvidence, GPSEvidence, FuelSensorEvidence, VehicleEvidence, Reliability
from infrastructure.intelligence.evidence.package import EvidencePackage
from infrastructure.intelligence.checks.models import CheckStatus
from infrastructure.intelligence.fuel_domain.config import FuelIntelligenceConfig
from infrastructure.intelligence.fuel_domain.checks.quantity import FuelQuantityCheck
from infrastructure.intelligence.fuel_domain.checks.location import FuelLocationCheck
from infrastructure.intelligence.fuel_domain.checks.timing import FuelTimingCheck
from infrastructure.intelligence.fuel_domain.checks.tank_capacity import FuelTankCapacityCheck

class TestFuelChecks(unittest.TestCase):
    def setUp(self):
        self.config = FuelIntelligenceConfig()
        now = datetime.now(timezone.utc)
        
        self.receipt = ReceiptEvidence(source="ocr", origin="s", collected_at=now, reliability=Reliability.HIGH, quantity=100.0, amount=150.0, metadata={"station_lat": 40.0, "station_lon": -74.0})
        self.gps = GPSEvidence(source="gps", origin="s", collected_at=now, reliability=Reliability.HIGH, latitude=40.0, longitude=-74.0, accuracy=5.0)
        self.sensor = FuelSensorEvidence(source="sensor", origin="s", collected_at=now, reliability=Reliability.HIGH, fuel_before=50.0, fuel_after=150.0)
        self.vehicle = VehicleEvidence(source="api", origin="s", collected_at=now, reliability=Reliability.HIGH, vehicle_id="V1", tank_capacity=300.0)

    def test_quantity_check_pass(self):
        check = FuelQuantityCheck(self.config)
        res = check.execute(EvidencePackage([self.receipt, self.sensor]))
        self.assertEqual(res.status, CheckStatus.PASS)

    def test_quantity_check_fail(self):
        check = FuelQuantityCheck(self.config)
        bad_sensor = self.sensor.model_copy(update={"fuel_after": 100.0}) # 50L filled instead of 100L
        res = check.execute(EvidencePackage([self.receipt, bad_sensor]))
        self.assertEqual(res.status, CheckStatus.FAIL)

    def test_location_check_pass(self):
        check = FuelLocationCheck(self.config)
        res = check.execute(EvidencePackage([self.receipt, self.gps]))
        self.assertEqual(res.status, CheckStatus.PASS)

    def test_timing_check_pass(self):
        check = FuelTimingCheck(self.config)
        res = check.execute(EvidencePackage([self.receipt, self.gps, self.sensor]))
        self.assertEqual(res.status, CheckStatus.PASS)

    def test_tank_capacity_check_pass(self):
        check = FuelTankCapacityCheck(self.config)
        res = check.execute(EvidencePackage([self.receipt, self.sensor, self.vehicle]))
        self.assertEqual(res.status, CheckStatus.PASS)

    def test_tank_capacity_check_fail(self):
        check = FuelTankCapacityCheck(self.config)
        # tank is 300. before=250. added=100. projected=350 -> fails
        bad_sensor = self.sensor.model_copy(update={"fuel_before": 250.0, "fuel_after": 350.0})
        res = check.execute(EvidencePackage([self.receipt, bad_sensor, self.vehicle]))
        self.assertEqual(res.status, CheckStatus.FAIL)
