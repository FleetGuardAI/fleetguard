"""
Tyre Intelligence - Tyre Health Risk Engine
"""

from typing import List
from infrastructure.intelligence.domain_risk.base import BaseDomainRiskEngine
from infrastructure.intelligence.domain_risk.models import DomainRiskProfile, RiskLevel, DomainRiskStatus, RiskFinding
from infrastructure.intelligence.assessments.models import AssessmentResult, AssessmentStatus


class TyreHealthRiskEngine(BaseDomainRiskEngine):
    """
    Consumes TyreHealthAssessment and maps findings deterministically to a RiskLevel.
    """

    @classmethod
    def key(cls) -> str:
        return "tyre.health_risk"

    @classmethod
    def name(cls) -> str:
        return "Tyre Health Risk Engine"

    @classmethod
    def version(cls) -> str:
        return "1.0.0"

    @classmethod
    def required_assessments(cls) -> List[str]:
        return ["tyre.health_assessment"]

    def execute(self, assessments: List[AssessmentResult]) -> DomainRiskProfile:
        assessment_dict = {a.assessment_key: a for a in assessments}
        req_key = "tyre.health_assessment"
        
        if req_key not in assessment_dict:
            return DomainRiskProfile(
                risk_engine_key=self.key(),
                risk_engine_name=self.name(),
                risk_engine_version=self.version(),
                status=DomainRiskStatus.INCONCLUSIVE,
                risk_level=RiskLevel.UNKNOWN,
                summary="Missing required tyre health assessment.",
                supporting_assessments=assessments
            )
            
        assessment = assessment_dict[req_key]
        
        if assessment.status == AssessmentStatus.ERROR:
            return DomainRiskProfile(
                risk_engine_key=self.key(),
                risk_engine_name=self.name(),
                risk_engine_version=self.version(),
                status=DomainRiskStatus.ERROR,
                risk_level=RiskLevel.UNKNOWN,
                summary="Tyre health assessment encountered an error.",
                supporting_assessments=assessments
            )
            
        if assessment.status == AssessmentStatus.INCONCLUSIVE:
            return DomainRiskProfile(
                risk_engine_key=self.key(),
                risk_engine_name=self.name(),
                risk_engine_version=self.version(),
                status=DomainRiskStatus.INCONCLUSIVE,
                risk_level=RiskLevel.UNKNOWN,
                summary="Tyre health assessment was inconclusive.",
                supporting_assessments=assessments
            )
            
        findings: List[RiskFinding] = []
        
        # Analyze findings
        is_critical = False
        violation_count = len(assessment.findings)
        
        for f in assessment.findings:
            if f.category == "Safety" and f.finding_key in ["tyre.critical_damage", "tyre.low_tread", "tyre.excessive_age"]:
                is_critical = True
                
            findings.append(RiskFinding(
                finding_key=f.finding_key,
                category=f.category,
                summary=f.summary,
                details=f.details,
                metadata=f.metadata
            ))
            
        if is_critical:
            return DomainRiskProfile(
                risk_engine_key=self.key(),
                risk_engine_name=self.name(),
                risk_engine_version=self.version(),
                status=DomainRiskStatus.COMPLETE,
                risk_level=RiskLevel.CRITICAL,
                summary="Critical tyre safety issues detected. Immediate replacement required.",
                findings=findings,
                supporting_assessments=assessments
            )
            
        if violation_count == 0:
            return DomainRiskProfile(
                risk_engine_key=self.key(),
                risk_engine_name=self.name(),
                risk_engine_version=self.version(),
                status=DomainRiskStatus.COMPLETE,
                risk_level=RiskLevel.LOW,
                summary="Tyres are in good condition. Low risk.",
                findings=findings,
                supporting_assessments=assessments
            )
        elif violation_count == 1:
            return DomainRiskProfile(
                risk_engine_key=self.key(),
                risk_engine_name=self.name(),
                risk_engine_version=self.version(),
                status=DomainRiskStatus.COMPLETE,
                risk_level=RiskLevel.MEDIUM,
                summary="Minor tyre issue detected. Medium risk.",
                findings=findings,
                supporting_assessments=assessments
            )
        else:
            return DomainRiskProfile(
                risk_engine_key=self.key(),
                risk_engine_name=self.name(),
                risk_engine_version=self.version(),
                status=DomainRiskStatus.COMPLETE,
                risk_level=RiskLevel.HIGH,
                summary=f"Multiple tyre issues ({violation_count}) detected. High risk.",
                findings=findings,
                supporting_assessments=assessments
            )
