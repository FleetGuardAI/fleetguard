"""
Compliance Intelligence - Driver License Validity Check
"""

from datetime import datetime, timezone
from typing import List, Optional
from infrastructure.intelligence.checks.models import CheckResult, CheckStatus
from infrastructure.intelligence.checks.base import BaseCheck
from infrastructure.intelligence.evidence.package import EvidencePackage
from infrastructure.intelligence.evidence.models import DriverLicenseEvidence
from infrastructure.intelligence.compliance_domain.config import ComplianceIntelligenceConfig


class DriverLicenseValidityCheck(BaseCheck):
    """
    Determines whether the assigned driver's license satisfies regulatory requirements.
    """
    
    def __init__(self, config: Optional[ComplianceIntelligenceConfig] = None):
        self.config = config or ComplianceIntelligenceConfig()

    @classmethod
    def key(cls) -> str:
        return "compliance.driver_license_validity"

    @classmethod
    def name(cls) -> str:
        return "Driver License Validity Check"

    @classmethod
    def version(cls) -> str:
        return "1.0.0"

    @classmethod
    def required_evidence(cls) -> List[type]:
        return [DriverLicenseEvidence]

    def execute(self, package: EvidencePackage) -> CheckResult:
        evidence_list = package.get_all_evidence(DriverLicenseEvidence)
        
        if not evidence_list:
            return CheckResult(
                check_key=self.key(),
                check_name=self.name(),
                status=CheckStatus.INCONCLUSIVE,
                message="Missing DriverLicenseEvidence.",
                evidence_used=[]
            )
            
        now = datetime.now(timezone.utc)
        evidence = evidence_list[0]
        
        expiry_date = evidence.expiry_date
        if expiry_date.tzinfo is None:
            expiry_date = expiry_date.replace(tzinfo=timezone.utc)
            
        days_until_expiry = (expiry_date - now).days
        
        cat = evidence.document_category.upper()
        
        if days_until_expiry < 0:
            return CheckResult(
                check_key=self.key(),
                check_name=self.name(),
                status=CheckStatus.FAIL,
                message=f"Driver license expired {-days_until_expiry} days ago.",
                evidence_used=[str(evidence.evidence_id)],
                metadata={"days_until_expiry": days_until_expiry}
            )
            
        if cat not in self.config.required_driver_license_classes:
            return CheckResult(
                check_key=self.key(),
                check_name=self.name(),
                status=CheckStatus.FAIL,
                message=f"Driver license class '{cat}' does not match required classes.",
                evidence_used=[str(evidence.evidence_id)],
                metadata={"document_category": cat, "required": self.config.required_driver_license_classes}
            )
            
        return CheckResult(
            check_key=self.key(),
            check_name=self.name(),
            status=CheckStatus.PASS,
            message="Driver license is valid and matches required classes.",
            evidence_used=[str(evidence.evidence_id)],
            metadata={"days_until_expiry": days_until_expiry, "document_category": cat}
        )
