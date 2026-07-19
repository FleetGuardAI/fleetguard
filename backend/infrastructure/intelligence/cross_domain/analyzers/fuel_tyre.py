"""
Cross-Domain Intelligence - Fuel & Tyre Correlation Analyzer
"""

from typing import List
from infrastructure.intelligence.domain_risk.models import DomainRiskProfile, RiskLevel
from infrastructure.intelligence.cross_domain.models import FleetInsight, InsightType, InsightStrength
from infrastructure.intelligence.cross_domain.base import BaseCrossDomainAnalyzer


class FuelTyreCorrelationAnalyzer(BaseCrossDomainAnalyzer):
    """
    Analyzes tyre condition as a contributor to reduced fuel efficiency.
    """

    @classmethod
    def key(cls) -> str:
        return "cross.fuel_tyre"

    @classmethod
    def name(cls) -> str:
        return "Fuel & Tyre Correlation Analyzer"

    def execute(self, profiles: List[DomainRiskProfile]) -> List[FleetInsight]:
        profile_dict = {p.risk_engine_key: p for p in profiles}
        
        fuel_profile = profile_dict.get("fuel.transaction_risk")
        tyre_profile = profile_dict.get("tyre.health_risk")
        
        if not fuel_profile or not tyre_profile:
            return []
            
        fuel_elevated = fuel_profile.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL)
        tyre_elevated = tyre_profile.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL)
        
        insights = []
        
        if fuel_elevated and tyre_elevated:
            insights.append(FleetInsight(
                insight_key=f"{self.key()}.poor_tyre_condition",
                insight_type=InsightType.DEPENDENCY,
                insight_strength=InsightStrength.MEDIUM,
                summary="Poor tyre condition may contribute to reduced fuel efficiency.",
                supporting_profiles=[fuel_profile, tyre_profile],
                metadata={"fuel_risk": fuel_profile.risk_level.value, "tyre_risk": tyre_profile.risk_level.value}
            ))
            
        return insights
