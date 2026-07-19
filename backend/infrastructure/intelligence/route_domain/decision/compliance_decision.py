"""
Route Intelligence - Trip Compliance Decision Engine
"""

from typing import List
from infrastructure.intelligence.global_decision.base import BaseDecisionEngine
from infrastructure.intelligence.domain_risk.models import DomainRiskProfile, RiskLevel
from infrastructure.intelligence.global_decision.models import Recommendation, RecommendationStatus, DecisionStatus


class TripComplianceDecisionEngine(BaseDecisionEngine):
    """
    Translates route compliance risk into operational policy recommendations.
    """

    @classmethod
    def key(cls) -> str:
        return "route.trip_compliance_decision"

    @classmethod
    def name(cls) -> str:
        return "Trip Compliance Decision Engine"

    @classmethod
    def version(cls) -> str:
        return "1.0.0"

    def execute(self, profiles: List[DomainRiskProfile]) -> Recommendation:
        profile_dict = {p.risk_engine_key: p for p in profiles}
        req_key = "route.trip_compliance_risk"
        
        if req_key not in profile_dict:
            return Recommendation(
                decision_engine_key=self.key(),
                decision_engine_name=self.name(),
                decision_engine_version=self.version(),
                status=DecisionStatus.INCONCLUSIVE,
                recommendation=RecommendationStatus.REVIEW_REQUIRED,
                summary="Missing required risk profile: route.trip_compliance_risk",
                supporting_profiles=profiles
            )
            
        profile = profile_dict[req_key]
        
        if profile.risk_level == RiskLevel.LOW:
            rec = RecommendationStatus.APPROVE
            justification = "Trip compliance risk is LOW. Approve trip."
        elif profile.risk_level == RiskLevel.MEDIUM:
            rec = RecommendationStatus.APPROVE_WITH_REVIEW
            justification = "Trip compliance risk is MEDIUM. Approve with review."
        elif profile.risk_level == RiskLevel.HIGH:
            rec = RecommendationStatus.REVIEW_REQUIRED
            justification = "Trip compliance risk is HIGH. Review required."
        elif profile.risk_level == RiskLevel.CRITICAL:
            rec = RecommendationStatus.REJECT
            justification = "Trip compliance risk is CRITICAL. Reject trip."
        else:
            rec = RecommendationStatus.REVIEW_REQUIRED
            justification = "Trip compliance risk is UNKNOWN. Review required."
            
        return Recommendation(
            decision_engine_key=self.key(),
            decision_engine_name=self.name(),
            decision_engine_version=self.version(),
            status=DecisionStatus.COMPLETE,
            recommendation=rec,
            summary=justification,
            supporting_profiles=[profile]
        )
