from typing import List
from infrastructure.intelligence.assessments.models import AssessmentResult, AssessmentStatus
from infrastructure.intelligence.domain_risk.base import BaseDomainRiskEngine
from infrastructure.intelligence.domain_risk.models import DomainRiskProfile, DomainRiskStatus, RiskLevel, RiskFinding
from infrastructure.intelligence.fuel_domain.assessments.transaction_integrity import FuelTransactionIntegrityAssessment


class FuelTransactionRiskEngine(BaseDomainRiskEngine):
    """
    Quantifies the business risk of a fuel transaction based on its integrity assessment.
    """
    
    @classmethod
    def key(cls) -> str:
        return "fuel.transaction_risk"
        
    @classmethod
    def name(cls) -> str:
        return "Fuel Transaction Risk Engine"

    @classmethod
    def required_assessments(cls) -> List[str]:
        return [FuelTransactionIntegrityAssessment.key()]

    def execute(self, assessments: List[AssessmentResult]) -> DomainRiskProfile:
        relevant = [a for a in assessments if a.assessment_key == FuelTransactionIntegrityAssessment.key()]
        
        if not relevant or relevant[0].status != AssessmentStatus.COMPLETE:
            return DomainRiskProfile(
                risk_engine_key=self.key(),
                risk_engine_name=self.name(),
                risk_engine_version=self.version(),
                status=DomainRiskStatus.INCONCLUSIVE,
                risk_level=RiskLevel.UNKNOWN,
                summary="Cannot quantify risk due to missing or inconclusive integrity assessment.",
                supporting_assessments=relevant
            )
            
        integrity = relevant[0]
        
        # Determine risk based on factual findings
        mismatches = [f for f in integrity.findings if f.category == "Integrity Mismatch"]
        
        findings = []
        if not mismatches:
            risk_level = RiskLevel.LOW
            summary = "Low risk. Transaction is completely consistent."
            findings.append(RiskFinding(
                finding_key=f"{self.key()}.finding.consistent",
                category="Low Risk",
                summary="No integrity mismatches found.",
                details="All evidence corroborates the transaction."
            ))
        elif len(mismatches) == 1:
            risk_level = RiskLevel.HIGH
            summary = "High risk. Transaction has a single integrity mismatch."
            findings.append(RiskFinding(
                finding_key=f"{self.key()}.finding.single_mismatch",
                category="High Risk",
                summary="A single integrity anomaly was detected.",
                details=mismatches[0].summary
            ))
        else:
            risk_level = RiskLevel.CRITICAL
            summary = f"Critical risk. Transaction has {len(mismatches)} integrity mismatches."
            findings.append(RiskFinding(
                finding_key=f"{self.key()}.finding.multiple_mismatches",
                category="Critical Risk",
                summary="Multiple anomalies detected, strongly indicating fraud or error.",
                details="; ".join(m.summary for m in mismatches)
            ))
            
        return DomainRiskProfile(
            risk_engine_key=self.key(),
            risk_engine_name=self.name(),
            risk_engine_version=self.version(),
            status=DomainRiskStatus.COMPLETE,
            risk_level=risk_level,
            summary=summary,
            findings=findings,
            supporting_assessments=relevant
        )
