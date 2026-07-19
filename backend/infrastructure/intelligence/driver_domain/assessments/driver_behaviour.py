from typing import List
from infrastructure.intelligence.checks.models import CheckResult, CheckStatus
from infrastructure.intelligence.assessments.base import BaseAssessment
from infrastructure.intelligence.assessments.models import AssessmentResult, AssessmentStatus, Finding


class DriverBehaviourAssessment(BaseAssessment):
    @classmethod
    def key(cls) -> str:
        return "driver.behaviour_assessment"

    @classmethod
    def name(cls) -> str:
        return "Driver Behaviour Assessment"

    @classmethod
    def required_checks(cls) -> List[str]:
        return [
            "driver.overspeed",
            "driver.harsh_acceleration",
            "driver.harsh_braking",
            "driver.excessive_idling",
            "driver.route_compliance"
        ]

    def execute(self, checks: List[CheckResult]) -> AssessmentResult:
        findings = []
        status = AssessmentStatus.COMPLETE
        missing_reqs = []
        failed_checks = []
        
        check_dict = {c.check_key: c for c in checks}
        
        for req in self.required_checks():
            if req not in check_dict:
                missing_reqs.append(req)
                continue
                
            check = check_dict[req]
            if check.status == CheckStatus.ERROR:
                failed_checks.append(check.check_key)
            elif check.status == CheckStatus.SKIPPED:
                missing_reqs.append(req)
                
        if failed_checks:
            return AssessmentResult(
                assessment_key=self.key(),
                assessment_name=self.name(),
                assessment_version=self.version(),
                status=AssessmentStatus.ERROR,
                summary=f"Failed due to check errors: {failed_checks}",
                contributing_checks=checks
            )
            
        if missing_reqs:
            return AssessmentResult(
                assessment_key=self.key(),
                assessment_name=self.name(),
                assessment_version=self.version(),
                status=AssessmentStatus.INCONCLUSIVE,
                summary=f"Missing or skipped required checks: {missing_reqs}",
                contributing_checks=checks
            )
            
        # All required checks passed successfully. Now generate factual findings based on FAIL (which means violation)
        for check in checks:
            if check.status == CheckStatus.FAIL:
                category = "Behaviour Mismatch"
                summary = ""
                if check.check_key == "driver.overspeed":
                    summary = "Excessive speeding detected."
                elif check.check_key in ("driver.harsh_acceleration", "driver.harsh_braking"):
                    summary = "Aggressive driving behaviour observed."
                elif check.check_key == "driver.excessive_idling":
                    summary = "Excessive idle time detected."
                elif check.check_key == "driver.route_compliance":
                    summary = "Route deviation observed."
                
                findings.append(Finding(
                    finding_key=f"{self.key()}.finding.{check.check_key}_failed",
                    category=category,
                    summary=summary,
                    details=check.message
                ))
                
        if not findings:
            findings.append(Finding(
                finding_key=f"{self.key()}.finding.safe_operation",
                category="Safe Driving",
                summary="Safe driving behaviour observed.",
                details="All operational checks passed without violations."
            ))
            summary = "Driver behaviour is compliant."
        else:
            summary = f"Detected {len(findings)} operational violations."
            
        return AssessmentResult(
            assessment_key=self.key(),
            assessment_name=self.name(),
            assessment_version=self.version(),
            status=status,
            summary=summary,
            findings=findings,
            contributing_checks=checks
        )
