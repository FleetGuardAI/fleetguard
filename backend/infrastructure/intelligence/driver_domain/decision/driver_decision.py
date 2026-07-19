from typing import List
from infrastructure.intelligence.domain_risk.models import DomainRiskProfile, RiskLevel, DomainRiskStatus
from infrastructure.intelligence.global_decision.base import BaseDecisionEngine
from infrastructure.intelligence.global_decision.models import Recommendation, RecommendationStatus, DecisionStatus


class DriverBehaviourDecisionEngine(BaseDecisionEngine):
    @classmethod
    def key(cls) -> str:
        return "driver.behaviour_decision"

    @classmethod
    def name(cls) -> str:
        return "Driver Behaviour Decision Engine"

    @classmethod
    def required_profiles(cls) -> List[str]:
        return ["driver.behaviour_risk"]

    def execute(self, profiles: List[DomainRiskProfile]) -> Recommendation:
        profile_dict = {p.risk_engine_key: p for p in profiles}
        req_key = "driver.behaviour_risk"
        
        if req_key not in profile_dict:
            return Recommendation(
                decision_engine_key=self.key(),
                decision_engine_name=self.name(),
                decision_engine_version=self.version(),
                status=DecisionStatus.INCONCLUSIVE,
                recommendation=None,
                summary="Missing required driver behaviour risk profile.",
                supporting_profiles=profiles
            )
            
        profile = profile_dict[req_key]
        
        if profile.status == DomainRiskStatus.ERROR:
            return Recommendation(
                decision_engine_key=self.key(),
                decision_engine_name=self.name(),
                decision_engine_version=self.version(),
                status=DecisionStatus.ERROR,
                recommendation=None,
                summary="Driver risk engine encountered an error.",
                supporting_profiles=profiles
            )
            
        if profile.status == DomainRiskStatus.INCONCLUSIVE:
            return Recommendation(
                decision_engine_key=self.key(),
                decision_engine_name=self.name(),
                decision_engine_version=self.version(),
                status=DecisionStatus.INCONCLUSIVE,
                recommendation=None,
                summary="Driver risk was inconclusive.",
                supporting_profiles=profiles
            )
            
        if profile.risk_level == RiskLevel.LOW:
            return Recommendation(
                decision_engine_key=self.key(),
                decision_engine_name=self.name(),
                decision_engine_version=self.version(),
                status=DecisionStatus.COMPLETE,
                recommendation=RecommendationStatus.APPROVE,
                summary="Safe driving behaviour confirmed. Approved.",
                supporting_profiles=profiles
            )
        elif profile.risk_level == RiskLevel.MEDIUM:
            return Recommendation(
                decision_engine_key=self.key(),
                decision_engine_name=self.name(),
                decision_engine_version=self.version(),
                status=DecisionStatus.COMPLETE,
                recommendation=RecommendationStatus.APPROVE_WITH_REVIEW,
                summary="Moderate risk driving behaviour detected. Review recommended.",
                supporting_profiles=profiles
            )
        elif profile.risk_level == RiskLevel.HIGH:
            return Recommendation(
                decision_engine_key=self.key(),
                decision_engine_name=self.name(),
                decision_engine_version=self.version(),
                status=DecisionStatus.COMPLETE,
                recommendation=RecommendationStatus.REVIEW_REQUIRED,
                summary="High risk driving behaviour detected. Mandatory review required.",
                supporting_profiles=profiles
            )
        else: # CRITICAL
            return Recommendation(
                decision_engine_key=self.key(),
                decision_engine_name=self.name(),
                decision_engine_version=self.version(),
                status=DecisionStatus.COMPLETE,
                recommendation=RecommendationStatus.REJECT,
                summary="Critical risk driving behaviour detected. Session flagged/rejected.",
                supporting_profiles=profiles
            )
