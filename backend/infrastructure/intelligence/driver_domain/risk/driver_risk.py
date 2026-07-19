from typing import List
from infrastructure.intelligence.assessments.models import AssessmentResult, AssessmentStatus
from infrastructure.intelligence.domain_risk.base import BaseDomainRiskEngine
from infrastructure.intelligence.domain_risk.models import DomainRiskProfile, DomainRiskStatus, RiskLevel


class DriverBehaviourRiskEngine(BaseDomainRiskEngine):
    @classmethod
    def key(cls) -> str:
        return "driver.behaviour_risk"

    @classmethod
    def name(cls) -> str:
        return "Driver Behaviour Risk Engine"

    @classmethod
    def required_assessments(cls) -> List[str]:
        return ["driver.behaviour_assessment"]

    def execute(self, assessments: List[AssessmentResult]) -> DomainRiskProfile:
        assessment_dict = {a.assessment_key: a for a in assessments}
        req_key = "driver.behaviour_assessment"
        
        if req_key not in assessment_dict:
            return DomainRiskProfile(
                risk_engine_key=self.key(),
                risk_engine_name=self.name(),
                risk_engine_version=self.version(),
                status=DomainRiskStatus.INCONCLUSIVE,
                risk_level=RiskLevel.UNKNOWN,
                summary="Missing required driver behaviour assessment.",
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
                summary="Driver behaviour assessment encountered an error.",
                supporting_assessments=assessments
            )
            
        if assessment.status == AssessmentStatus.INCONCLUSIVE:
            return DomainRiskProfile(
                risk_engine_key=self.key(),
                risk_engine_name=self.name(),
                risk_engine_version=self.version(),
                status=DomainRiskStatus.INCONCLUSIVE,
                risk_level=RiskLevel.UNKNOWN,
                summary="Driver behaviour assessment was inconclusive.",
                supporting_assessments=assessments
            )
            
        # Count violation findings
        violation_count = sum(1 for f in assessment.findings if "safe_operation" not in f.finding_key)
        
        if violation_count == 0:
            return DomainRiskProfile(
                risk_engine_key=self.key(),
                risk_engine_name=self.name(),
                risk_engine_version=self.version(),
                status=DomainRiskStatus.COMPLETE,
                risk_level=RiskLevel.LOW,
                summary="No operational violations detected. Low driver risk.",
                supporting_assessments=assessments
            )
        elif violation_count == 1:
            return DomainRiskProfile(
                risk_engine_key=self.key(),
                risk_engine_name=self.name(),
                risk_engine_version=self.version(),
                status=DomainRiskStatus.COMPLETE,
                risk_level=RiskLevel.HIGH,
                summary="Single operational violation detected. High driver risk.",
                supporting_assessments=assessments
            )
        else:
            return DomainRiskProfile(
                risk_engine_key=self.key(),
                risk_engine_name=self.name(),
                risk_engine_version=self.version(),
                status=DomainRiskStatus.COMPLETE,
                risk_level=RiskLevel.CRITICAL,
                summary=f"Multiple operational violations ({violation_count}) detected. Critical driver risk.",
                supporting_assessments=assessments
            )
