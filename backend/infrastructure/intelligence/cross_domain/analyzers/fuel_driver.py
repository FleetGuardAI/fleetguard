"""
Cross-Domain Intelligence - Fuel & Driver Correlation Analyzer
"""

from typing import List
from infrastructure.intelligence.domain_risk.models import DomainRiskProfile, RiskLevel
from infrastructure.intelligence.cross_domain.models import FleetInsight, InsightType, InsightStrength
from infrastructure.intelligence.cross_domain.base import BaseCrossDomainAnalyzer


class FuelDriverCorrelationAnalyzer(BaseCrossDomainAnalyzer):
    """
    Analyzes elevated driver behaviour risk alongside increased fuel risk.
    """

    @classmethod
    def key(cls) -> str:
        return "cross.fuel_driver"

    @classmethod
    def name(cls) -> str:
        return "Fuel & Driver Correlation Analyzer"

    def execute(self, profiles: List[DomainRiskProfile]) -> List[FleetInsight]:
        profile_dict = {p.risk_engine_key: p for p in profiles}
        
        fuel_profile = profile_dict.get("fuel.transaction_risk")
        driver_profile = profile_dict.get("driver.behaviour_risk")
        
        if not fuel_profile or not driver_profile:
            return []
            
        fuel_elevated = fuel_profile.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL)
        driver_elevated = driver_profile.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL)
        
        insights = []
        
        if fuel_elevated and driver_elevated:
            insights.append(FleetInsight(
                insight_key=f"{self.key()}.elevated_risk",
                insight_type=InsightType.CORRELATION,
                insight_strength=InsightStrength.HIGH,
                summary="Elevated driver behaviour risk coincides with increased fuel risk. Driver behaviour should be investigated as a contributing factor.",
                supporting_profiles=[fuel_profile, driver_profile],
                metadata={"fuel_risk": fuel_profile.risk_level.value, "driver_risk": driver_profile.risk_level.value}
            ))
            
        return insights
