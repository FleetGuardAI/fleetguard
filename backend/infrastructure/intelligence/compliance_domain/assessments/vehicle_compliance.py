"""
Compliance Intelligence - Vehicle Compliance Assessment
"""

from typing import List
from infrastructure.intelligence.assessments.base import BaseAssessment
from infrastructure.intelligence.assessments.models import AssessmentResult, AssessmentStatus, Finding
from infrastructure.intelligence.checks.models import CheckResult, CheckStatus


class VehicleComplianceAssessment(BaseAssessment):
    """
    Consumes all compliance check results and produces factual findings.
    """

    @classmethod
    def key(cls) -> str:
        return "compliance.vehicle_assessment"

    @classmethod
    def name(cls) -> str:
        return "Vehicle Compliance Assessment"

    @classmethod
    def version(cls) -> str:
        return "1.0.0"

    @classmethod
    def required_checks(cls) -> List[str]:
        return [
            "compliance.registration_validity",
            "compliance.insurance_validity",
            "compliance.fitness_validity",
            "compliance.pollution_validity",
            "compliance.permit_validity",
            "compliance.driver_license_validity"
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
        
        def add_finding(check_key: str, finding_key: str, summary: str):
            check = check_dict[check_key]
            if check.status == CheckStatus.FAIL:
                findings.append(Finding(
                    finding_key=finding_key,
                    category="Compliance",
                    summary=summary,
                    details=check.message,
                    metadata=check.metadata
                ))
            elif check.status == CheckStatus.PASS and check.metadata.get("expiring_soon"):
                findings.append(Finding(
                    finding_key=f"{finding_key}_warning",
                    category="Warning",
                    summary=f"{summary} (Warning: Expiring soon)",
                    details=check.message,
                    metadata=check.metadata
                ))

        add_finding("compliance.registration_validity", "compliance.registration_invalid", "Vehicle registration invalid or expired.")
        add_finding("compliance.insurance_validity", "compliance.insurance_invalid", "Insurance invalid or expired.")
        add_finding("compliance.fitness_validity", "compliance.fitness_invalid", "Fitness certificate invalid or expired.")
        add_finding("compliance.pollution_validity", "compliance.pollution_invalid", "Pollution certificate invalid or expired.")
        add_finding("compliance.permit_validity", "compliance.permit_invalid", "Required permit(s) missing or expired.")
        add_finding("compliance.driver_license_validity", "compliance.driver_license_invalid", "Driver license invalid or mismatch.")

        if findings:
            status = AssessmentStatus.COMPLETE
            summary_msg = f"Found {len(findings)} compliance issue(s) or warning(s)."
        else:
            status = AssessmentStatus.COMPLETE
            summary_msg = "All vehicle compliance checks passed successfully."

        return AssessmentResult(
            assessment_key=self.key(),
            assessment_name=self.name(),
            assessment_version=self.version(),
            status=status,
            summary=summary_msg,
            findings=findings,
            contributing_checks=checks
        )
