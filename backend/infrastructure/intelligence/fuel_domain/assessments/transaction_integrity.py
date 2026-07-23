from typing import List
from infrastructure.intelligence.checks.models import CheckResult, CheckStatus
from infrastructure.intelligence.assessments.models import AssessmentResult, AssessmentStatus, Finding
from infrastructure.intelligence.assessments.base import BaseAssessment
from infrastructure.intelligence.fuel_domain.checks.quantity import FuelQuantityCheck
from infrastructure.intelligence.fuel_domain.checks.location import FuelLocationCheck
from infrastructure.intelligence.fuel_domain.checks.timing import FuelTimingCheck
from infrastructure.intelligence.fuel_domain.checks.tank_capacity import FuelTankCapacityCheck


class FuelTransactionIntegrityAssessment(BaseAssessment):
    """
    Evaluates whether a fuel transaction is internally consistent based on the required checks.
    Produces factual findings without making business risk conclusions.
    """
    
    @classmethod
    def key(cls) -> str:
        return "fuel.transaction_integrity"
        
    @classmethod
    def required_checks(cls) -> List[str]:
        return [
            FuelQuantityCheck.key(),
            FuelLocationCheck.key(),
            FuelTimingCheck.key(),
            FuelTankCapacityCheck.key()
        ]

    def execute(self, checks: List[CheckResult]) -> AssessmentResult:
        # Determine if we have all required checks and if they executed successfully
        required_keys = self.required_checks()
        relevant_checks = [c for c in checks if c.check_key in required_keys]
        relevant_keys = [c.check_key for c in relevant_checks]
        
        missing_or_error = [k for k in required_keys if k not in relevant_keys or 
                            next((c.status for c in relevant_checks if c.check_key == k), CheckStatus.ERROR) in (CheckStatus.ERROR, CheckStatus.SKIPPED)]
        
        if missing_or_error:
            # We don't have enough clean facts to make a full integrity assessment
            return AssessmentResult(
                assessment_key=self.key(),
                assessment_name=self.name(),
                assessment_version=self.version(),
                status=AssessmentStatus.INCONCLUSIVE,
                summary=f"Inconclusive due to missing or skipped checks: {missing_or_error}",
                findings=[],
                contributing_checks=relevant_checks
            )
            
        findings = []
        is_consistent = True
        
        for check in relevant_checks:
            if check.status == CheckStatus.FAIL:
                is_consistent = False
                findings.append(Finding(
                    finding_key=f"{self.key()}.finding.{check.check_key}_failed",
                    category="Integrity Mismatch",
                    summary=f"Mismatch detected in {check.check_name}",
                    details=check.message
                ))
                
        if is_consistent:
            findings.append(Finding(
                finding_key=f"{self.key()}.finding.consistent",
                category="Integrity OK",
                summary="Fuel transaction appears internally consistent.",
                details="All integrity checks passed."
            ))
            summary = "Transaction is structurally and chronologically consistent."
        else:
            summary = f"Transaction integrity compromised with {len(findings)} mismatches."

        return AssessmentResult(
            assessment_key=self.key(),
            assessment_name=self.name(),
            assessment_version=self.version(),
            status=AssessmentStatus.COMPLETE,
            summary=summary,
            findings=findings,
            contributing_checks=relevant_checks
        )
