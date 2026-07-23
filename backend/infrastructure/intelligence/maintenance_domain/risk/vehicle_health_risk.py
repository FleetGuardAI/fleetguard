from typing import List
from infrastructure.intelligence.assessments.models import AssessmentResult, AssessmentStatus
from infrastructure.intelligence.domain_risk.base import BaseDomainRiskEngine
from infrastructure.intelligence.domain_risk.models import DomainRiskProfile, DomainRiskStatus, RiskLevel


class VehicleHealthRiskEngine(BaseDomainRiskEngine):
    @classmethod
    def key(cls) -> str:
        return "maintenance.vehicle_health_risk"

    @classmethod
    def name(cls) -> str:
        return "Vehicle Health Risk Engine"

    @classmethod
    def required_assessments(cls) -> List[str]:
        return ["maintenance.vehicle_health_assessment"]

    def execute(self, assessments: List[AssessmentResult]) -> DomainRiskProfile:
        assessment_dict = {a.assessment_key: a for a in assessments}
        req_key = "maintenance.vehicle_health_assessment"
        
        if req_key not in assessment_dict:
            return DomainRiskProfile(
                risk_engine_key=self.key(),
                risk_engine_name=self.name(),
                risk_engine_version=self.version(),
                status=DomainRiskStatus.INCONCLUSIVE,
                risk_level=RiskLevel.UNKNOWN,
                summary="Missing required vehicle health assessment.",
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
                summary="Vehicle health assessment encountered an error.",
                supporting_assessments=assessments
            )
            
        if assessment.status == AssessmentStatus.INCONCLUSIVE:
            return DomainRiskProfile(
                risk_engine_key=self.key(),
                risk_engine_name=self.name(),
                risk_engine_version=self.version(),
                status=DomainRiskStatus.INCONCLUSIVE,
                risk_level=RiskLevel.UNKNOWN,
                summary="Vehicle health assessment was inconclusive.",
                supporting_assessments=assessments
            )
            
        # Analyze findings
        violation_count = 0
        critical_failure = False
        
        for finding in assessment.findings:
            if "healthy" in finding.finding_key:
                continue
                
            violation_count += 1
            if "critical_component_due" in finding.finding_key:
                critical_failure = True
                
        if critical_failure:
            return DomainRiskProfile(
                risk_engine_key=self.key(),
                risk_engine_name=self.name(),
                risk_engine_version=self.version(),
                status=DomainRiskStatus.COMPLETE,
                risk_level=RiskLevel.CRITICAL,
                summary="Critical safety component maintenance is overdue. Critical health risk.",
                supporting_assessments=assessments
            )
            
        if violation_count == 0:
            return DomainRiskProfile(
                risk_engine_key=self.key(),
                risk_engine_name=self.name(),
                risk_engine_version=self.version(),
                status=DomainRiskStatus.COMPLETE,
                risk_level=RiskLevel.LOW,
                summary="No maintenance compliance issues detected. Low health risk.",
                supporting_assessments=assessments
            )
        elif violation_count == 1:
            return DomainRiskProfile(
                risk_engine_key=self.key(),
                risk_engine_name=self.name(),
                risk_engine_version=self.version(),
                status=DomainRiskStatus.COMPLETE,
                risk_level=RiskLevel.MEDIUM,
                summary="Minor maintenance compliance issue detected. Medium health risk.",
                supporting_assessments=assessments
            )
        else:
            return DomainRiskProfile(
                risk_engine_key=self.key(),
                risk_engine_name=self.name(),
                risk_engine_version=self.version(),
                status=DomainRiskStatus.COMPLETE,
                risk_level=RiskLevel.HIGH,
                summary=f"Multiple maintenance compliance issues ({violation_count}) detected. High health risk.",
                supporting_assessments=assessments
            )
