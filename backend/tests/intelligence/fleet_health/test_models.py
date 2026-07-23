import unittest
from pydantic import ValidationError
from infrastructure.intelligence.fleet_health.models import (
    FleetFinding, FleetFindingSeverity, DomainRiskCounts, FleetDomainStatistics, 
    VehicleIntelligenceContext, FleetHealthReport, FleetHealthStatus
)


class TestFleetHealthModels(unittest.TestCase):
    def test_fleet_finding_immutability(self):
        finding = FleetFinding(
            finding_key="test",
            severity=FleetFindingSeverity.INFO,
            summary="Test summary"
        )
        
        with self.assertRaises(ValidationError):
            finding.summary = "Changed"
            
    def test_domain_risk_counts_immutability(self):
        counts = DomainRiskCounts(low_count=1, medium_count=2, high_count=3, critical_count=4)
        with self.assertRaises(ValidationError):
            counts.low_count = 5
            
    def test_fleet_domain_statistics_immutability(self):
        stats = FleetDomainStatistics()
        with self.assertRaises(ValidationError):
            stats.fuel = DomainRiskCounts()
            
    def test_vehicle_intelligence_context_immutability(self):
        ctx = VehicleIntelligenceContext(vehicle_id="v1", profiles=[])
        with self.assertRaises(ValidationError):
            ctx.vehicle_id = "v2"
            
    def test_fleet_health_report_immutability(self):
        report = FleetHealthReport(
            fleet_id="f1",
            fleet_health_status=FleetHealthStatus.EXCELLENT,
            fleet_summary="Test",
            domain_statistics=FleetDomainStatistics()
        )
        with self.assertRaises(ValidationError):
            report.fleet_summary = "Changed"
