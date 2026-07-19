"""
Compliance Intelligence - Vehicle Compliance Risk Engine
"""

from typing import List, Optional
from infrastructure.intelligence.domain_risk.base import BaseDomainRiskEngine
from infrastructure.intelligence.assessments.models import AssessmentResult, Finding
from infrastructure.intelligence.domain_risk.models import DomainRiskProfile, RiskLevel, DomainRiskStatus


class VehicleComplianceRiskEngine(BaseDomainRiskEngine):
    """
    Consumes the VehicleComplianceAssessment and maps findings to a discrete risk level.
    """

    @classmethod
    def key(cls) -> str:
        return "compliance.vehicle_risk"

    @classmethod
    def name(cls) -> str:
        return "Vehicle Compliance Risk Engine"

    @classmethod
    def version(cls) -> str:
        return "1.0.0"

    @classmethod
    def required_assessments(cls) -> List[str]:
        return ["compliance.vehicle_assessment"]

    def execute(self, assessments: List[AssessmentResult]) -> DomainRiskProfile:
        assessment_dict = {a.assessment_key: a for a in assessments}
        req_key = "compliance.vehicle_assessment"
        
        if req_key not in assessment_dict:
            return DomainRiskProfile(
                risk_engine_key=self.key(),
                risk_engine_name=self.name(),
                risk_engine_version=self.version(),
                status=DomainRiskStatus.INCONCLUSIVE,
                risk_level=RiskLevel.UNKNOWN,
                summary="Missing required assessment: compliance.vehicle_assessment",
                supporting_assessments=assessments
            )
            
        assessment = assessment_dict[req_key]
        findings = assessment.findings
        
        if not findings:
            return DomainRiskProfile(
                risk_engine_key=self.key(),
                risk_engine_name=self.name(),
                risk_engine_version=self.version(),
                status=DomainRiskStatus.COMPLETE,
                risk_level=RiskLevel.LOW,
                summary="No compliance issues found. Risk is LOW.",
                supporting_assessments=[assessment]
            )

        # Mapping findings to risk levels
        # If any document is expired (finding_key does not end with _warning), it's a critical compliance issue -> CRITICAL
        # If it's just a warning (expiring soon) -> MEDIUM
        
        critical_findings = [f for f in findings if not f.finding_key.endswith("_warning")]
        warning_findings = [f for f in findings if f.finding_key.endswith("_warning")]

        if critical_findings:
            return DomainRiskProfile(
                risk_engine_key=self.key(),
                risk_engine_name=self.name(),
                risk_engine_version=self.version(),
                status=DomainRiskStatus.COMPLETE,
                risk_level=RiskLevel.CRITICAL,
                summary=f"Detected {len(critical_findings)} critical compliance failure(s). Risk is CRITICAL.",
                supporting_assessments=[assessment]
            )
            
        if warning_findings:
            return DomainRiskProfile(
                risk_engine_key=self.key(),
                risk_engine_name=self.name(),
                risk_engine_version=self.version(),
                status=DomainRiskStatus.COMPLETE,
                risk_level=RiskLevel.MEDIUM,
                summary=f"Detected {len(warning_findings)} compliance warning(s) (expiring soon). Risk is MEDIUM.",
                supporting_assessments=[assessment]
            )

        # Fallback
        return DomainRiskProfile(
            risk_engine_key=self.key(),
            risk_engine_name=self.name(),
            risk_engine_version=self.version(),
            status=DomainRiskStatus.COMPLETE,
            risk_level=RiskLevel.UNKNOWN,
            summary="Unable to determine compliance risk level.",
            supporting_assessments=[assessment]
        )
