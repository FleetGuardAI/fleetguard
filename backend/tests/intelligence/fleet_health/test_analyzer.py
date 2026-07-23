import unittest
from infrastructure.intelligence.domain_risk.models import DomainRiskProfile, RiskLevel, DomainRiskStatus
from infrastructure.intelligence.fleet_health.models import VehicleIntelligenceContext, FleetHealthStatus, FleetFindingSeverity
from infrastructure.intelligence.fleet_health.analyzer import FleetHealthAnalyzer


class TestFleetHealthAnalyzer(unittest.TestCase):
    def _make_profile(self, key: str, level: RiskLevel) -> DomainRiskProfile:
        return DomainRiskProfile(
            risk_engine_key=key,
            risk_engine_name=key,
            risk_engine_version="1",
            status=DomainRiskStatus.COMPLETE,
            risk_level=level,
            summary="test"
        )

    def test_excellent_fleet(self):
        ctx1 = VehicleIntelligenceContext(vehicle_id="v1", profiles=[
            self._make_profile("fuel.transaction_risk", RiskLevel.LOW)
        ])
        ctx2 = VehicleIntelligenceContext(vehicle_id="v2", profiles=[
            self._make_profile("maintenance.vehicle_health_risk", RiskLevel.MEDIUM)
        ])
        
        analyzer = FleetHealthAnalyzer(fleet_id="f1")
        report = analyzer.execute([ctx1, ctx2], [])
        
        self.assertEqual(report.fleet_health_status, FleetHealthStatus.EXCELLENT)
        self.assertEqual(report.vehicle_count, 2)
        self.assertEqual(report.operational_vehicle_count, 2)
        self.assertEqual(report.critical_vehicle_count, 0)
        self.assertEqual(report.domain_statistics.fuel.low_count, 1)
        self.assertEqual(report.domain_statistics.maintenance.medium_count, 1)
        
        self.assertEqual(len(report.fleet_findings), 1)
        self.assertEqual(report.fleet_findings[0].finding_key, "fleet.excellent")
        self.assertEqual(report.fleet_findings[0].severity, FleetFindingSeverity.INFO)

    def test_critical_fleet(self):
        ctx1 = VehicleIntelligenceContext(vehicle_id="v1", profiles=[
            self._make_profile("fuel.transaction_risk", RiskLevel.CRITICAL)
        ])
        ctx2 = VehicleIntelligenceContext(vehicle_id="v2", profiles=[
            self._make_profile("compliance.vehicle_risk", RiskLevel.HIGH)
        ])
        
        analyzer = FleetHealthAnalyzer(fleet_id="f1")
        report = analyzer.execute([ctx1, ctx2], [])
        
        # 1 critical out of 2 = 50% (> 15%) -> CRITICAL
        self.assertEqual(report.fleet_health_status, FleetHealthStatus.CRITICAL)
        self.assertEqual(report.vehicle_count, 2)
        self.assertEqual(report.critical_vehicle_count, 1)
        self.assertEqual(report.operational_vehicle_count, 1)
        
        self.assertEqual(report.domain_statistics.fuel.critical_count, 1)
        self.assertEqual(report.domain_statistics.compliance.high_count, 1)
        
        finding_keys = [f.finding_key for f in report.fleet_findings]
        self.assertIn("fleet.critical_vehicles", finding_keys)
        self.assertIn("fleet.compliance_issues", finding_keys)
        
        self.assertIn("1 vehicles require immediate attention.", report.fleet_summary)
        self.assertIn("Compliance issues concentrated in 1 vehicle domain checks.", report.fleet_summary)

    def test_empty_fleet(self):
        analyzer = FleetHealthAnalyzer(fleet_id="f1")
        report = analyzer.execute([], [])
        
        self.assertEqual(report.fleet_health_status, FleetHealthStatus.EXCELLENT)
        self.assertEqual(report.vehicle_count, 0)
        self.assertEqual(len(report.fleet_findings), 1)
        self.assertEqual(report.fleet_findings[0].finding_key, "fleet.empty")
