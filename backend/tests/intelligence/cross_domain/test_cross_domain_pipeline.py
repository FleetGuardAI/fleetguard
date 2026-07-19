import unittest
from infrastructure.intelligence.domain_risk.models import DomainRiskProfile, RiskLevel, DomainRiskStatus
from infrastructure.intelligence.cross_domain.registry import CrossDomainRegistry
from infrastructure.intelligence.cross_domain.executor import CrossDomainExecutor
from infrastructure.intelligence.cross_domain.analyzers.fuel_driver import FuelDriverCorrelationAnalyzer
from infrastructure.intelligence.cross_domain.analyzers.fuel_tyre import FuelTyreCorrelationAnalyzer
from infrastructure.intelligence.cross_domain.analyzers.driver_tyre import DriverTyreCorrelationAnalyzer
from infrastructure.intelligence.cross_domain.analyzers.maintenance_compliance import MaintenanceComplianceCorrelationAnalyzer
from infrastructure.intelligence.cross_domain.analyzers.route_compliance import RouteComplianceCorrelationAnalyzer
from infrastructure.intelligence.cross_domain.analyzers.route_fuel import RouteFuelCorrelationAnalyzer


class TestCrossDomainPipeline(unittest.TestCase):
    def setUp(self):
        self.registry = CrossDomainRegistry()
        self.registry.register(FuelDriverCorrelationAnalyzer)
        self.registry.register(FuelTyreCorrelationAnalyzer)
        self.registry.register(DriverTyreCorrelationAnalyzer)
        self.registry.register(MaintenanceComplianceCorrelationAnalyzer)
        self.registry.register(RouteComplianceCorrelationAnalyzer)
        self.registry.register(RouteFuelCorrelationAnalyzer)
        self.executor = CrossDomainExecutor(self.registry)

    def _make_profile(self, key: str, level: RiskLevel) -> DomainRiskProfile:
        return DomainRiskProfile(
            risk_engine_key=key,
            risk_engine_name=key,
            risk_engine_version="1",
            status=DomainRiskStatus.COMPLETE,
            risk_level=level,
            summary="test"
        )

    def test_pipeline_execution(self):
        profiles = [
            self._make_profile("fuel.transaction_risk", RiskLevel.HIGH),
            self._make_profile("driver.behaviour_risk", RiskLevel.HIGH),
            self._make_profile("tyre.health_risk", RiskLevel.CRITICAL),
            self._make_profile("maintenance.vehicle_health_risk", RiskLevel.HIGH),
            self._make_profile("compliance.vehicle_risk", RiskLevel.HIGH),
            self._make_profile("route.trip_compliance_risk", RiskLevel.HIGH),
        ]
        
        result = self.executor.execute(profiles)
        
        # We expect all analyzers to have succeeded
        for res in result.analyzer_results.values():
            self.assertEqual(res, "SUCCESS")
            
        # Every combination should produce insights
        self.assertEqual(len(result.insights), 6)
        
        # Verify explainability preservation
        for insight in result.insights:
            self.assertEqual(len(insight.supporting_profiles), 2)
