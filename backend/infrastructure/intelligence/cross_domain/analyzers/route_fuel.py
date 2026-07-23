"""
Cross-Domain Intelligence - Route & Fuel Correlation Analyzer
"""

from typing import List
from infrastructure.intelligence.domain_risk.models import DomainRiskProfile, RiskLevel
from infrastructure.intelligence.cross_domain.models import FleetInsight, InsightType, InsightStrength
from infrastructure.intelligence.cross_domain.base import BaseCrossDomainAnalyzer


class RouteFuelCorrelationAnalyzer(BaseCrossDomainAnalyzer):
    """
    Analyzes how route deviations correlate with increased fuel consumption.
    """

    @classmethod
    def key(cls) -> str:
        return "cross.route_fuel"

    @classmethod
    def name(cls) -> str:
        return "Route & Fuel Correlation Analyzer"

    def execute(self, profiles: List[DomainRiskProfile]) -> List[FleetInsight]:
        profile_dict = {p.risk_engine_key: p for p in profiles}
        
        fuel_profile = profile_dict.get("fuel.transaction_risk")
        route_profile = profile_dict.get("route.trip_compliance_risk")
        
        if not fuel_profile or not route_profile:
            return []
            
        fuel_elevated = fuel_profile.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL)
        route_elevated = route_profile.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL)
        
        insights = []
        
        if fuel_elevated and route_elevated:
            insights.append(FleetInsight(
                insight_key=f"{self.key()}.route_deviation_fuel",
                insight_type=InsightType.CORRELATION,
                insight_strength=InsightStrength.MEDIUM,
                summary="Route deviations may contribute to increased fuel consumption.",
                supporting_profiles=[fuel_profile, route_profile],
                metadata={"fuel_risk": fuel_profile.risk_level.value, "route_risk": route_profile.risk_level.value}
            ))
            
        return insights
