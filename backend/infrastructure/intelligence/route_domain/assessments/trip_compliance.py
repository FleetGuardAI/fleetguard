"""
Route Intelligence - Trip Compliance Assessment
"""

from typing import List
from infrastructure.intelligence.assessments.base import BaseAssessment
from infrastructure.intelligence.assessments.models import AssessmentResult, AssessmentStatus, Finding
from infrastructure.intelligence.checks.models import CheckResult, CheckStatus


class TripComplianceAssessment(BaseAssessment):
    """
    Consumes route check results and produces factual trip compliance findings.
    """

    @classmethod
    def key(cls) -> str:
        return "route.trip_compliance_assessment"

    @classmethod
    def name(cls) -> str:
        return "Trip Compliance Assessment"

    @classmethod
    def version(cls) -> str:
        return "1.0.0"

    @classmethod
    def required_checks(cls) -> List[str]:
        return [
            "route.deviation",
            "route.trip_delay",
            "route.unauthorized_stop",
            "route.geofence_violation",
            "route.excessive_detour"
        ]

    def execute(self, checks: List[CheckResult]) -> AssessmentResult:
        check_dict = {c.check_key: c for c in checks}
        
        required = set(self.required_checks())
        provided = set(check_dict.keys())
        
        if not required.issubset(provided):
            return AssessmentResult(
                assessment_key=self.key(),
                assessment_name=self.name(),
                assessment_version=self.version(),
                status=AssessmentStatus.INCONCLUSIVE,
                summary="Missing required checks.",
                findings=[],
                contributing_checks=checks
            )
            
        findings: List[Finding] = []
        
        deviation = check_dict["route.deviation"]
        if deviation.status == CheckStatus.FAIL:
            findings.append(Finding(
                finding_key="route.deviation_detected",
                category="Compliance",
                summary="Significant route deviation detected.",
                details=deviation.message,
                metadata=deviation.metadata
            ))

        delay = check_dict["route.trip_delay"]
        if delay.status == CheckStatus.FAIL:
            findings.append(Finding(
                finding_key="route.trip_delayed",
                category="Performance",
                summary="Trip exceeded planned duration.",
                details=delay.message,
                metadata=delay.metadata
            ))

        stop = check_dict["route.unauthorized_stop"]
        if stop.status == CheckStatus.FAIL:
            findings.append(Finding(
                finding_key="route.unauthorized_stop_detected",
                category="Compliance",
                summary="Unauthorized stop detected.",
                details=stop.message,
                metadata=stop.metadata
            ))

        geofence = check_dict["route.geofence_violation"]
        if geofence.status == CheckStatus.FAIL:
            findings.append(Finding(
                finding_key="route.geofence_breach",
                category="Compliance",
                summary="Vehicle entered restricted geofence.",
                details=geofence.message,
                metadata=geofence.metadata
            ))

        detour = check_dict["route.excessive_detour"]
        if detour.status == CheckStatus.FAIL:
            findings.append(Finding(
                finding_key="route.excessive_detour",
                category="Performance",
                summary="Excessive detour observed.",
                details=detour.message,
                metadata=detour.metadata
            ))

        return AssessmentResult(
            assessment_key=self.key(),
            assessment_name=self.name(),
            assessment_version=self.version(),
            status=AssessmentStatus.COMPLETE,
            summary=f"Computed {len(findings)} compliance finding(s).",
            findings=findings,
            contributing_checks=checks
        )
