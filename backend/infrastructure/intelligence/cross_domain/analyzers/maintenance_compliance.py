"""
Cross-Domain Intelligence - Maintenance & Compliance Correlation Analyzer
"""

from typing import List
from infrastructure.intelligence.domain_risk.models import DomainRiskProfile, RiskLevel
from infrastructure.intelligence.cross_domain.models import FleetInsight, InsightType, InsightStrength
from infrastructure.intelligence.cross_domain.base import BaseCrossDomainAnalyzer


class MaintenanceComplianceCorrelationAnalyzer(BaseCrossDomainAnalyzer):
    """
    Analyzes maintenance requirements in relation to regulatory compliance.
    """

    @classmethod
    def key(cls) -> str:
        return "cross.maintenance_compliance"

    @classmethod
    def name(cls) -> str:
        return "Maintenance & Compliance Correlation Analyzer"

    def execute(self, profiles: List[DomainRiskProfile]) -> List[FleetInsight]:
        profile_dict = {p.risk_engine_key: p for p in profiles}
        
        maintenance_profile = profile_dict.get("maintenance.vehicle_health_risk")
        compliance_profile = profile_dict.get("compliance.vehicle_risk")
        
        if not maintenance_profile or not compliance_profile:
            return []
            
        maintenance_elevated = maintenance_profile.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL)
        compliance_elevated = compliance_profile.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL, RiskLevel.MEDIUM)
        
        insights = []
        
        if maintenance_elevated and compliance_elevated:
            insights.append(FleetInsight(
                insight_key=f"{self.key()}.maintenance_compliance_risk",
                insight_type=InsightType.COMPLIANCE_PATTERN,
                insight_strength=InsightStrength.HIGH,
                summary="Vehicle requires maintenance while approaching or exceeding regulatory non-compliance.",
                supporting_profiles=[maintenance_profile, compliance_profile],
                metadata={"maintenance_risk": maintenance_profile.risk_level.value, "compliance_risk": compliance_profile.risk_level.value}
            ))
            
        return insights
