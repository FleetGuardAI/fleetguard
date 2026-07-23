from typing import List
from infrastructure.intelligence.domain_risk.models import DomainRiskProfile, DomainRiskStatus, RiskLevel
from infrastructure.intelligence.global_decision.base import BaseDecisionEngine
from infrastructure.intelligence.global_decision.models import Recommendation, DecisionStatus, RecommendationStatus, RecommendationFinding
from infrastructure.intelligence.fuel_domain.risk.transaction_risk import FuelTransactionRiskEngine


class FuelDecisionEngine(BaseDecisionEngine):
    """
    Makes the final business recommendation based on Fuel Transaction Domain Risk.
    """
    
    @classmethod
    def key(cls) -> str:
        return "fuel.transaction_decision"
        
    @classmethod
    def name(cls) -> str:
        return "Fuel Transaction Decision Engine"

    def execute(self, profiles: List[DomainRiskProfile]) -> Recommendation:
        relevant = [p for p in profiles if p.risk_engine_key == FuelTransactionRiskEngine.key()]
        
        if not relevant or relevant[0].status != DomainRiskStatus.COMPLETE:
            return Recommendation(
                decision_engine_key=self.key(),
                decision_engine_name=self.name(),
                decision_engine_version=self.version(),
                status=DecisionStatus.INCONCLUSIVE,
                recommendation=None,
                summary="Cannot make decision due to missing or inconclusive fuel transaction risk profile.",
                supporting_profiles=relevant
            )
            
        risk_profile = relevant[0]
        
        # Policy Mapping
        findings = []
        if risk_profile.risk_level == RiskLevel.LOW:
            rec_status = RecommendationStatus.APPROVE
            findings.append(RecommendationFinding(
                finding_key=f"{self.key()}.finding.approved",
                category="Auto-Approve",
                summary="Transaction approved automatically due to LOW risk.",
                details="No anomalies found across any evidence sources."
            ))
        elif risk_profile.risk_level == RiskLevel.MEDIUM:
            rec_status = RecommendationStatus.APPROVE_WITH_REVIEW
            findings.append(RecommendationFinding(
                finding_key=f"{self.key()}.finding.approve_review",
                category="Manual Review",
                summary="Transaction approved but flagged for review.",
                details="Medium risk detected."
            ))
        elif risk_profile.risk_level == RiskLevel.HIGH:
            rec_status = RecommendationStatus.REVIEW_REQUIRED
            findings.append(RecommendationFinding(
                finding_key=f"{self.key()}.finding.review_required",
                category="Manual Review Required",
                summary="Transaction paused for review due to HIGH risk.",
                details=risk_profile.summary
            ))
        else: # CRITICAL
            rec_status = RecommendationStatus.REJECT
            findings.append(RecommendationFinding(
                finding_key=f"{self.key()}.finding.rejected",
                category="Auto-Reject",
                summary="Transaction automatically rejected due to CRITICAL risk.",
                details=risk_profile.summary
            ))
            
        return Recommendation(
            decision_engine_key=self.key(),
            decision_engine_name=self.name(),
            decision_engine_version=self.version(),
            status=DecisionStatus.COMPLETE,
            recommendation=rec_status,
            summary=f"Final recommendation: {rec_status.value}",
            findings=findings,
            supporting_profiles=relevant
        )
