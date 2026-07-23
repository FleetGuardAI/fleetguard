from typing import List
from infrastructure.intelligence.checks.models import CheckResult, CheckStatus
from infrastructure.intelligence.assessments.base import BaseAssessment
from infrastructure.intelligence.assessments.models import AssessmentResult, AssessmentStatus, Finding


class VehicleHealthAssessment(BaseAssessment):
    @classmethod
    def key(cls) -> str:
        return "maintenance.vehicle_health_assessment"

    @classmethod
    def name(cls) -> str:
        return "Vehicle Health Assessment"

    @classmethod
    def required_checks(cls) -> List[str]:
        return [
            "maintenance.service_overdue",
            "maintenance.distance_overdue",
            "maintenance.time_overdue",
            "maintenance.repeated_failures",
            "maintenance.critical_component_due"
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
                # For maintenance, if we have missing history or schedules, we skip them.
                # It doesn't necessarily fail the whole assessment, but we log missing reqs if all are missing.
                pass
                
        if failed_checks:
            return AssessmentResult(
                assessment_key=self.key(),
                assessment_name=self.name(),
                assessment_version=self.version(),
                status=AssessmentStatus.ERROR,
                summary=f"Failed due to check errors: {failed_checks}",
                contributing_checks=checks
            )
            
        # Generate factual findings based on FAIL (which means violation)
        for check in checks:
            if check.status == CheckStatus.FAIL:
                category = "Maintenance Alert"
                summary = ""
                if check.check_key in ("maintenance.service_overdue", "maintenance.time_overdue"):
                    summary = "Scheduled maintenance overdue."
                elif check.check_key == "maintenance.distance_overdue":
                    summary = "Vehicle exceeded maintenance mileage."
                elif check.check_key == "maintenance.repeated_failures":
                    summary = "Repeated component failures detected."
                elif check.check_key == "maintenance.critical_component_due":
                    summary = "Critical maintenance inspection required."
                else:
                    summary = "Maintenance rule violation detected."
                    
                findings.append(Finding(
                    finding_key=f"{self.key()}.finding.{check.check_key.split('.')[-1]}_failed",
                    category=category,
                    summary=summary,
                    details=check.message
                ))
                
        # If there are no checks at all that ran successfully
        ran_checks = [c for c in checks if c.status in (CheckStatus.PASS, CheckStatus.FAIL)]
        if not ran_checks:
            return AssessmentResult(
                assessment_key=self.key(),
                assessment_name=self.name(),
                assessment_version=self.version(),
                status=AssessmentStatus.INCONCLUSIVE,
                summary=f"Missing or skipped required evidence for all checks: {missing_reqs}",
                contributing_checks=checks
            )
                
        if not findings:
            findings.append(Finding(
                finding_key=f"{self.key()}.finding.healthy",
                category="Vehicle Health",
                summary="Vehicle is compliant with maintenance schedules.",
                details="All maintenance checks passed without violations."
            ))
            summary = "Vehicle maintenance is compliant."
        else:
            summary = f"Detected {len(findings)} maintenance compliance issues."
            
        return AssessmentResult(
            assessment_key=self.key(),
            assessment_name=self.name(),
            assessment_version=self.version(),
            status=status,
            summary=summary,
            findings=findings,
            contributing_checks=checks
        )
