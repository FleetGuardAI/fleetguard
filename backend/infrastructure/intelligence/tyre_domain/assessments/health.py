"""
Tyre Intelligence - Tyre Health Assessment
"""

from typing import List
from infrastructure.intelligence.assessments.base import BaseAssessment
from infrastructure.intelligence.assessments.models import AssessmentResult, AssessmentStatus, Finding
from infrastructure.intelligence.checks.models import CheckResult, CheckStatus


class TyreHealthAssessment(BaseAssessment):
    """
    Consumes tyre check results and produces factual findings regarding tyre health.
    """

    @classmethod
    def key(cls) -> str:
        return "tyre.health_assessment"

    @classmethod
    def name(cls) -> str:
        return "Tyre Health Assessment"

    @classmethod
    def version(cls) -> str:
        return "1.0.0"

    @classmethod
    def required_checks(cls) -> List[str]:
        return [
            "tyre.pressure",
            "tyre.tread_depth",
            "tyre.age",
            "tyre.wear_pattern",
            "tyre.damage"
        ]

    def execute(self, checks: List[CheckResult]) -> AssessmentResult:
        check_dict = {c.check_key: c for c in checks}
        
        required_keys = [
            "tyre.pressure",
            "tyre.tread_depth",
            "tyre.age",
            "tyre.wear_pattern",
            "tyre.damage"
        ]
        
        if not all(k in check_dict for k in required_keys):
            return AssessmentResult(
                assessment_key=self.key(),
                assessment_name=self.name(),
                assessment_version=self.version(),
                status=AssessmentStatus.INCONCLUSIVE,
                summary="Missing required tyre checks.",
                contributing_checks=checks
            )
            
        findings: List[Finding] = []
        
        pressure = check_dict["tyre.pressure"]
        if pressure.status == CheckStatus.FAIL:
            findings.append(Finding(
                finding_key="tyre.pressure_deviation",
                category="Maintenance",
                summary="Abnormal tyre pressure detected.",
                details=pressure.message,
                metadata=pressure.metadata
            ))

        tread = check_dict["tyre.tread_depth"]
        if tread.status == CheckStatus.FAIL:
            findings.append(Finding(
                finding_key="tyre.low_tread",
                category="Safety",
                summary="Tyre tread depth is below minimum safe limits.",
                details=tread.message,
                metadata=tread.metadata
            ))

        age = check_dict["tyre.age"]
        if age.status == CheckStatus.FAIL:
            findings.append(Finding(
                finding_key="tyre.excessive_age",
                category="Safety",
                summary="Tyre has exceeded maximum safe age.",
                details=age.message,
                metadata=age.metadata
            ))

        wear = check_dict["tyre.wear_pattern"]
        if wear.status == CheckStatus.FAIL:
            findings.append(Finding(
                finding_key="tyre.abnormal_wear",
                category="Maintenance",
                summary="Abnormal tyre wear pattern detected.",
                details=wear.message,
                metadata=wear.metadata
            ))

        damage = check_dict["tyre.damage"]
        if damage.status == CheckStatus.FAIL:
            findings.append(Finding(
                finding_key="tyre.critical_damage",
                category="Safety",
                summary="Critical tyre damage identified during inspection.",
                details=damage.message,
                metadata=damage.metadata
            ))
            
        return AssessmentResult(
            assessment_key=self.key(),
            assessment_name=self.name(),
            assessment_version=self.version(),
            status=AssessmentStatus.COMPLETE,
            summary=f"Tyre health assessment completed. {len(findings)} issues found.",
            findings=findings,
            contributing_checks=checks
        )
