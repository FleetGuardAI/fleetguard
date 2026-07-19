"""
Cross-Domain Intelligence - Route & Compliance Correlation Analyzer
"""

from typing import List
from infrastructure.intelligence.domain_risk.models import DomainRiskProfile, RiskLevel
from infrastructure.intelligence.cross_domain.models import FleetInsight, InsightType, InsightStrength
from infrastructure.intelligence.cross_domain.base import BaseCrossDomainAnalyzer


class RouteComplianceCorrelationAnalyzer(BaseCrossDomainAnalyzer):
    """
    Analyzes trip compliance risks occurring alongside vehicle compliance issues.
    """

    @classmethod
    def key(cls) -> str:
        return "cross.route_compliance"

    @classmethod
    def name(cls) -> str:
        return "Route & Compliance Correlation Analyzer"

    def execute(self, profiles: List[DomainRiskProfile]) -> List[FleetInsight]:
        profile_dict = {p.risk_engine_key: p for p in profiles}
        
        route_profile = profile_dict.get("route.trip_compliance_risk")
        compliance_profile = profile_dict.get("compliance.vehicle_risk")
        
        if not route_profile or not compliance_profile:
            return []
            
        route_elevated = route_profile.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL)
        compliance_elevated = compliance_profile.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL)
        
        insights = []
        
        if route_elevated and compliance_elevated:
            insights.append(FleetInsight(
                insight_key=f"{self.key()}.route_compliance_risk",
                insight_type=InsightType.COMPLIANCE_PATTERN,
                insight_strength=InsightStrength.HIGH,
                summary="Vehicle entered regulated operational areas while compliance risk is elevated.",
                supporting_profiles=[route_profile, compliance_profile],
                metadata={"route_risk": route_profile.risk_level.value, "compliance_risk": compliance_profile.risk_level.value}
            ))
            
        return insights
