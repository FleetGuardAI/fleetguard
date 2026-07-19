import unittest
from datetime import datetime, timedelta, timezone

from infrastructure.intelligence.evidence.models import MaintenanceHistoryEvidence, MaintenanceScheduleEvidence, Reliability
from infrastructure.intelligence.evidence.package import EvidencePackage
from infrastructure.intelligence.checks.models import CheckStatus
from infrastructure.intelligence.maintenance_domain.config import MaintenanceIntelligenceConfig
from infrastructure.intelligence.maintenance_domain.checks.service_overdue import MaintenanceServiceOverdueCheck
from infrastructure.intelligence.maintenance_domain.checks.distance_overdue import MaintenanceDistanceOverdueCheck
from infrastructure.intelligence.maintenance_domain.checks.time_overdue import MaintenanceTimeOverdueCheck
from infrastructure.intelligence.maintenance_domain.checks.repeated_failures import RepeatedFailureCheck
from infrastructure.intelligence.maintenance_domain.checks.critical_component_due import CriticalComponentDueCheck


class TestMaintenanceChecks(unittest.TestCase):
    def setUp(self):
        self.config = MaintenanceIntelligenceConfig(
            service_interval_days=180,
            repeated_failure_threshold_count=3,
            repeated_failure_time_window_days=90
        )
        self.now = datetime.now(timezone.utc)
        
        self.history = MaintenanceHistoryEvidence(
            source="test", origin="test", collected_at=self.now,
            reliability=Reliability.HIGH,
            vehicle_id="v1",
            service_date=self.now - timedelta(days=100),
            odometer_km=50000.0,
            service_type="general",
            reported_component_failures=["brake_pad", "brake_pad"],
            diagnostic_codes=[]
        )
        
        self.schedule = MaintenanceScheduleEvidence(
            source="test", origin="test", collected_at=self.now,
            reliability=Reliability.HIGH,
            vehicle_id="v1",
            next_service_due_date=self.now + timedelta(days=10),
            next_service_due_km=60000.0
        )
        
        self.package = EvidencePackage([self.history, self.schedule])

    def test_service_overdue_pass(self):
        check = MaintenanceServiceOverdueCheck(self.config)
        res = check.execute(self.package)
        self.assertEqual(res.status, CheckStatus.PASS)

    def test_service_overdue_fail(self):
        check = MaintenanceServiceOverdueCheck(self.config)
        bad_schedule = self.schedule.model_copy(deep=True, update={"next_service_due_date": self.now - timedelta(days=1)})
        res = check.execute(EvidencePackage([self.history, bad_schedule]))
        self.assertEqual(res.status, CheckStatus.FAIL)

    def test_distance_overdue_pass(self):
        check = MaintenanceDistanceOverdueCheck(self.config)
        res = check.execute(self.package)
        self.assertEqual(res.status, CheckStatus.PASS)

    def test_distance_overdue_fail(self):
        check = MaintenanceDistanceOverdueCheck(self.config)
        bad_schedule = self.schedule.model_copy(deep=True, update={"next_service_due_km": 40000.0}) # Odometer is 50000
        res = check.execute(EvidencePackage([self.history, bad_schedule]))
        self.assertEqual(res.status, CheckStatus.FAIL)

    def test_time_overdue_pass(self):
        check = MaintenanceTimeOverdueCheck(self.config)
        # Last service was 100 days ago, config says 180 days interval
        res = check.execute(self.package)
        self.assertEqual(res.status, CheckStatus.PASS)

    def test_time_overdue_fail(self):
        check = MaintenanceTimeOverdueCheck(self.config)
        bad_history = self.history.model_copy(deep=True, update={"service_date": self.now - timedelta(days=200)})
        res = check.execute(EvidencePackage([bad_history, self.schedule]))
        self.assertEqual(res.status, CheckStatus.FAIL)

    def test_repeated_failures_pass(self):
        check = RepeatedFailureCheck(self.config)
        # Only 2 failures in history (threshold is 3)
        res = check.execute(self.package)
        self.assertEqual(res.status, CheckStatus.PASS)

    def test_repeated_failures_fail(self):
        check = RepeatedFailureCheck(self.config)
        # Add 3 failures within time window
        bad_history = self.history.model_copy(deep=True, update={"reported_component_failures": ["brake_pad", "brake_pad", "brake_pad"], "service_date": self.now - timedelta(days=10)})
        res = check.execute(EvidencePackage([bad_history, self.schedule]))
        self.assertEqual(res.status, CheckStatus.FAIL)
        
    def test_critical_component_pass(self):
        check = CriticalComponentDueCheck(self.config)
        res = check.execute(self.package)
        self.assertEqual(res.status, CheckStatus.PASS)

    def test_critical_component_fail(self):
        check = CriticalComponentDueCheck(self.config)
        bad_history = self.history.model_copy(deep=True, update={"diagnostic_codes": ["CRIT_BRAKE_01"]})
        res = check.execute(EvidencePackage([bad_history, self.schedule]))
        self.assertEqual(res.status, CheckStatus.FAIL)
