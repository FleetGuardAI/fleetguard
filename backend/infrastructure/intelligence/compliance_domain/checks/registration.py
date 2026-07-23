"""
Compliance Intelligence - Registration Validity Check
"""

from datetime import datetime, timezone
from typing import List, Optional
from infrastructure.intelligence.checks.models import CheckResult, CheckStatus
from infrastructure.intelligence.checks.base import BaseCheck
from infrastructure.intelligence.evidence.package import EvidencePackage
from infrastructure.intelligence.evidence.models import VehicleRegistrationEvidence
from infrastructure.intelligence.compliance_domain.config import ComplianceIntelligenceConfig


class RegistrationValidityCheck(BaseCheck):
    """
    Determines whether the vehicle registration remains valid.
    """
    
    def __init__(self, config: Optional[ComplianceIntelligenceConfig] = None):
        self.config = config or ComplianceIntelligenceConfig()

    @classmethod
    def key(cls) -> str:
        return "compliance.registration_validity"

    @classmethod
    def name(cls) -> str:
        return "Registration Validity Check"

    @classmethod
    def version(cls) -> str:
        return "1.0.0"

    @classmethod
    def required_evidence(cls) -> List[type]:
        return [VehicleRegistrationEvidence]

    def execute(self, package: EvidencePackage) -> CheckResult:
        evidence_list = package.get_all_evidence(VehicleRegistrationEvidence)
        
        if not evidence_list:
            return CheckResult(
                check_key=self.key(),
                check_name=self.name(),
                status=CheckStatus.INCONCLUSIVE,
                message="Missing VehicleRegistrationEvidence.",
                evidence_used=[]
            )
            
        evidence = evidence_list[0]
        now = datetime.now(timezone.utc)
        
        # Ensure evidence dates are timezone-aware if comparing against `now`
        # In a real system, we'd handle timezone conversions. Assuming UTC for this domain logic.
        expiry_date = evidence.expiry_date
        if expiry_date.tzinfo is None:
            expiry_date = expiry_date.replace(tzinfo=timezone.utc)
            
        days_until_expiry = (expiry_date - now).days
        
        if days_until_expiry < 0:
            return CheckResult(
                check_key=self.key(),
                check_name=self.name(),
                status=CheckStatus.FAIL,
                message=f"Vehicle registration expired {-days_until_expiry} days ago.",
                evidence_used=[str(evidence.evidence_id)],
                metadata={"days_until_expiry": days_until_expiry}
            )
        elif days_until_expiry <= self.config.expiry_warning_days:
            # We treat warning as a PASS but flag the impending expiry in the check result
            # Or we could return a specific status, but the CheckStatus only has PASS/FAIL/INCONCLUSIVE/ERROR.
            # We will PASS and rely on the metadata/message to inform the assessment.
            # Wait, the spec says "determines whether it remains valid". Warning is still valid.
            return CheckResult(
                check_key=self.key(),
                check_name=self.name(),
                status=CheckStatus.PASS,
                message=f"Vehicle registration is valid but expires in {days_until_expiry} days.",
                evidence_used=[str(evidence.evidence_id)],
                metadata={"days_until_expiry": days_until_expiry, "expiring_soon": True}
            )
        else:
            return CheckResult(
                check_key=self.key(),
                check_name=self.name(),
                status=CheckStatus.PASS,
                message="Vehicle registration is valid.",
                evidence_used=[str(evidence.evidence_id)],
                metadata={"days_until_expiry": days_until_expiry, "expiring_soon": False}
            )
