"""
Compliance Intelligence - Permit Validity Check
"""

from datetime import datetime, timezone
from typing import List, Optional
from infrastructure.intelligence.checks.models import CheckResult, CheckStatus
from infrastructure.intelligence.checks.base import BaseCheck
from infrastructure.intelligence.evidence.package import EvidencePackage
from infrastructure.intelligence.evidence.models import PermitEvidence
from infrastructure.intelligence.compliance_domain.config import ComplianceIntelligenceConfig


class PermitValidityCheck(BaseCheck):
    """
    Determines whether required permits remain valid.
    """
    
    def __init__(self, config: Optional[ComplianceIntelligenceConfig] = None):
        self.config = config or ComplianceIntelligenceConfig()

    @classmethod
    def key(cls) -> str:
        return "compliance.permit_validity"

    @classmethod
    def name(cls) -> str:
        return "Permit Validity Check"

    @classmethod
    def version(cls) -> str:
        return "1.0.0"

    @classmethod
    def required_evidence(cls) -> List[type]:
        return [PermitEvidence]

    def execute(self, package: EvidencePackage) -> CheckResult:
        evidence_list = package.get_all_evidence(PermitEvidence)
        
        if not evidence_list:
            return CheckResult(
                check_key=self.key(),
                check_name=self.name(),
                status=CheckStatus.INCONCLUSIVE,
                message="Missing PermitEvidence.",
                evidence_used=[]
            )
            
        now = datetime.now(timezone.utc)
        
        evidence_ids = []
        missing_permits = set(self.config.mandatory_permit_types)
        expired_permits = []
        
        for evidence in evidence_list:
            evidence_ids.append(str(evidence.evidence_id))
            cat = evidence.document_category.upper()
            
            expiry_date = evidence.expiry_date
            if expiry_date.tzinfo is None:
                expiry_date = expiry_date.replace(tzinfo=timezone.utc)
                
            days_until_expiry = (expiry_date - now).days
            
            if days_until_expiry < 0:
                expired_permits.append((cat, -days_until_expiry))
            elif cat in missing_permits:
                missing_permits.remove(cat)
                
        if missing_permits:
            return CheckResult(
                check_key=self.key(),
                check_name=self.name(),
                status=CheckStatus.FAIL,
                message=f"Missing mandatory permit(s): {', '.join(missing_permits)}",
                evidence_used=evidence_ids,
                metadata={"missing_permits": list(missing_permits)}
            )
            
        if expired_permits:
            return CheckResult(
                check_key=self.key(),
                check_name=self.name(),
                status=CheckStatus.FAIL,
                message=f"Permit(s) expired: {', '.join([f'{p[0]} ({p[1]} days ago)' for p in expired_permits])}",
                evidence_used=evidence_ids,
                metadata={"expired_permits": [p[0] for p in expired_permits]}
            )
            
        return CheckResult(
            check_key=self.key(),
            check_name=self.name(),
            status=CheckStatus.PASS,
            message="All mandatory permits are valid.",
            evidence_used=evidence_ids,
            metadata={"valid_permits_count": len(evidence_list)}
        )
