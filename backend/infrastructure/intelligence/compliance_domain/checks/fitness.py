"""
Compliance Intelligence - Fitness Certificate Check
"""

from datetime import datetime, timezone
from typing import List, Optional
from infrastructure.intelligence.checks.models import CheckResult, CheckStatus
from infrastructure.intelligence.checks.base import BaseCheck
from infrastructure.intelligence.evidence.package import EvidencePackage
from infrastructure.intelligence.evidence.models import FitnessCertificateEvidence
from infrastructure.intelligence.compliance_domain.config import ComplianceIntelligenceConfig


class FitnessCertificateCheck(BaseCheck):
    """
    Determines whether the vehicle fitness certificate remains valid.
    """
    
    def __init__(self, config: Optional[ComplianceIntelligenceConfig] = None):
        self.config = config or ComplianceIntelligenceConfig()

    @classmethod
    def key(cls) -> str:
        return "compliance.fitness_validity"

    @classmethod
    def name(cls) -> str:
        return "Fitness Certificate Validity Check"

    @classmethod
    def version(cls) -> str:
        return "1.0.0"

    @classmethod
    def required_evidence(cls) -> List[type]:
        return [FitnessCertificateEvidence]

    def execute(self, package: EvidencePackage) -> CheckResult:
        evidence_list = package.get_all_evidence(FitnessCertificateEvidence)
        
        if not evidence_list:
            return CheckResult(
                check_key=self.key(),
                check_name=self.name(),
                status=CheckStatus.INCONCLUSIVE,
                message="Missing FitnessCertificateEvidence.",
                evidence_used=[]
            )
            
        evidence = evidence_list[0]
        now = datetime.now(timezone.utc)
        
        expiry_date = evidence.expiry_date
        if expiry_date.tzinfo is None:
            expiry_date = expiry_date.replace(tzinfo=timezone.utc)
            
        days_until_expiry = (expiry_date - now).days
        
        if evidence.document_status.upper() not in ("ACTIVE", "VALID"):
            return CheckResult(
                check_key=self.key(),
                check_name=self.name(),
                status=CheckStatus.FAIL,
                message=f"Fitness certificate status is invalid ({evidence.document_status}).",
                evidence_used=[str(evidence.evidence_id)],
                metadata={"document_status": evidence.document_status}
            )
            
        if days_until_expiry < 0:
            return CheckResult(
                check_key=self.key(),
                check_name=self.name(),
                status=CheckStatus.FAIL,
                message=f"Fitness certificate expired {-days_until_expiry} days ago.",
                evidence_used=[str(evidence.evidence_id)],
                metadata={"days_until_expiry": days_until_expiry}
            )
        else:
            return CheckResult(
                check_key=self.key(),
                check_name=self.name(),
                status=CheckStatus.PASS,
                message=f"Fitness certificate is valid and expires in {days_until_expiry} days.",
                evidence_used=[str(evidence.evidence_id)],
                metadata={"days_until_expiry": days_until_expiry, "expiring_soon": days_until_expiry <= self.config.expiry_warning_days}
            )
