"""
Cross-Domain Intelligence - Driver & Tyre Correlation Analyzer
"""

from typing import List
from infrastructure.intelligence.domain_risk.models import DomainRiskProfile, RiskLevel
from infrastructure.intelligence.cross_domain.models import FleetInsight, InsightType, InsightStrength
from infrastructure.intelligence.cross_domain.base import BaseCrossDomainAnalyzer


class DriverTyreCorrelationAnalyzer(BaseCrossDomainAnalyzer):
    """
    Analyzes aggressive driving behaviour's effect on tyre wear.
    """

    @classmethod
    def key(cls) -> str:
        return "cross.driver_tyre"

    @classmethod
    def name(cls) -> str:
        return "Driver & Tyre Correlation Analyzer"

    def execute(self, profiles: List[DomainRiskProfile]) -> List[FleetInsight]:
        profile_dict = {p.risk_engine_key: p for p in profiles}
        
        driver_profile = profile_dict.get("driver.behaviour_risk")
        tyre_profile = profile_dict.get("tyre.health_risk")
        
        if not driver_profile or not tyre_profile:
            return []
            
        driver_elevated = driver_profile.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL)
        tyre_elevated = tyre_profile.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL)
        
        insights = []
        
        if driver_elevated and tyre_elevated:
            insights.append(FleetInsight(
                insight_key=f"{self.key()}.aggressive_driving_tyre_wear",
                insight_type=InsightType.DEPENDENCY,
                insight_strength=InsightStrength.MEDIUM,
                summary="Aggressive driving behaviour may contribute to accelerated tyre wear.",
                supporting_profiles=[driver_profile, tyre_profile],
                metadata={"driver_risk": driver_profile.risk_level.value, "tyre_risk": tyre_profile.risk_level.value}
            ))
            
        return insights
