"""
Route Intelligence - Trip Compliance Risk Engine
"""

from typing import List
from infrastructure.intelligence.domain_risk.base import BaseDomainRiskEngine
from infrastructure.intelligence.domain_risk.models import DomainRiskProfile, RiskLevel, DomainRiskStatus
from infrastructure.intelligence.assessments.models import AssessmentResult, AssessmentStatus


class TripComplianceRiskEngine(BaseDomainRiskEngine):
    """
    Consumes TripComplianceAssessment and maps findings deterministically to RiskLevel.
    """

    @classmethod
    def key(cls) -> str:
        return "route.trip_compliance_risk"

    @classmethod
    def name(cls) -> str:
        return "Trip Compliance Risk Engine"

    @classmethod
    def version(cls) -> str:
        return "1.0.0"

    @classmethod
    def required_assessments(cls) -> List[str]:
        return ["route.trip_compliance_assessment"]

    def execute(self, assessments: List[AssessmentResult]) -> DomainRiskProfile:
        assessment_dict = {a.assessment_key: a for a in assessments}
        req_key = "route.trip_compliance_assessment"
        
        if req_key not in assessment_dict:
            return DomainRiskProfile(
                risk_engine_key=self.key(), risk_engine_name=self.name(), risk_engine_version=self.version(),
                status=DomainRiskStatus.INCONCLUSIVE,
                risk_level=RiskLevel.UNKNOWN,
                supporting_assessments=assessments,
                summary="Missing required assessment: route.trip_compliance_assessment"
            )
            
        assessment = assessment_dict[req_key]
        if assessment.status != AssessmentStatus.COMPLETE:
            return DomainRiskProfile(
                risk_engine_key=self.key(), risk_engine_name=self.name(), risk_engine_version=self.version(),
                status=DomainRiskStatus.ERROR,
                risk_level=RiskLevel.UNKNOWN,
                supporting_assessments=assessments,
                summary="Required assessment is not complete."
            )

        # Categorize findings
        critical_keys = {"route.geofence_breach", "route.unauthorized_stop_detected"}
        high_keys = {"route.deviation_detected", "route.excessive_detour"}
        medium_keys = {"route.trip_delayed"}
        
        critical_count = sum(1 for f in assessment.findings if f.finding_key in critical_keys)
        high_count = sum(1 for f in assessment.findings if f.finding_key in high_keys)
        medium_count = sum(1 for f in assessment.findings if f.finding_key in medium_keys)

        total_findings = len(assessment.findings)

        if critical_count > 0:
            risk_level = RiskLevel.CRITICAL
        elif high_count > 0:
            risk_level = RiskLevel.HIGH
        elif total_findings >= 2:
            risk_level = RiskLevel.HIGH
        elif medium_count > 0:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW
            
        return DomainRiskProfile(
            risk_engine_key=self.key(), risk_engine_name=self.name(), risk_engine_version=self.version(),
            status=DomainRiskStatus.COMPLETE,
            risk_level=risk_level,
            supporting_assessments=[assessment],
            summary=f"Computed route compliance risk: {risk_level.value} based on {total_findings} findings."
        )
