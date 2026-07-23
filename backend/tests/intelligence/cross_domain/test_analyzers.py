import unittest
from infrastructure.intelligence.domain_risk.models import DomainRiskProfile, RiskLevel, DomainRiskStatus
from infrastructure.intelligence.cross_domain.analyzers.fuel_driver import FuelDriverCorrelationAnalyzer
from infrastructure.intelligence.cross_domain.analyzers.fuel_tyre import FuelTyreCorrelationAnalyzer
from infrastructure.intelligence.cross_domain.analyzers.driver_tyre import DriverTyreCorrelationAnalyzer
from infrastructure.intelligence.cross_domain.analyzers.maintenance_compliance import MaintenanceComplianceCorrelationAnalyzer
from infrastructure.intelligence.cross_domain.analyzers.route_compliance import RouteComplianceCorrelationAnalyzer
from infrastructure.intelligence.cross_domain.analyzers.route_fuel import RouteFuelCorrelationAnalyzer


class TestCrossDomainAnalyzers(unittest.TestCase):
    def _make_profile(self, key: str, level: RiskLevel) -> DomainRiskProfile:
        return DomainRiskProfile(
            risk_engine_key=key,
            risk_engine_name=key,
            risk_engine_version="1",
            status=DomainRiskStatus.COMPLETE,
            risk_level=level,
            summary="test"
        )

    def test_fuel_driver_correlation(self):
        analyzer = FuelDriverCorrelationAnalyzer()
        
        # High and High -> Insight
        p_fuel = self._make_profile("fuel.transaction_risk", RiskLevel.HIGH)
        p_driver = self._make_profile("driver.behaviour_risk", RiskLevel.HIGH)
        insights = analyzer.execute([p_fuel, p_driver])
        self.assertEqual(len(insights), 1)
        self.assertEqual(len(insights[0].supporting_profiles), 2)
        
        # Low and High -> No insight
        p_fuel_low = self._make_profile("fuel.transaction_risk", RiskLevel.LOW)
        insights = analyzer.execute([p_fuel_low, p_driver])
        self.assertEqual(len(insights), 0)

    def test_maintenance_compliance_correlation(self):
        analyzer = MaintenanceComplianceCorrelationAnalyzer()
        
        p_maint = self._make_profile("maintenance.vehicle_health_risk", RiskLevel.HIGH)
        p_comp = self._make_profile("compliance.vehicle_risk", RiskLevel.MEDIUM)
        
        insights = analyzer.execute([p_maint, p_comp])
        self.assertEqual(len(insights), 1)
        self.assertEqual(len(insights[0].supporting_profiles), 2)
        
        p_maint_low = self._make_profile("maintenance.vehicle_health_risk", RiskLevel.LOW)
        insights = analyzer.execute([p_maint_low, p_comp])
        self.assertEqual(len(insights), 0)
