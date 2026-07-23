"""
Tyre Intelligence - Tyre Age Check
"""

from typing import List, Optional
from datetime import timezone
from infrastructure.intelligence.checks.models import CheckResult, CheckStatus
from infrastructure.intelligence.checks.base import BaseCheck
from infrastructure.intelligence.evidence.package import EvidencePackage
from infrastructure.intelligence.evidence.models import TyreInspectionEvidence
from infrastructure.intelligence.tyre_domain.config import TyreIntelligenceConfig


class TyreAgeCheck(BaseCheck):
    """
    Determines whether tyre age exceeds configured limits by calculating the difference 
    between tyre_installation_date and inspection_date.
    """
    
    def __init__(self, config: Optional[TyreIntelligenceConfig] = None):
        self.config = config or TyreIntelligenceConfig()

    @classmethod
    def key(cls) -> str:
        return "tyre.age"

    @classmethod
    def name(cls) -> str:
        return "Tyre Age Limit Check"

    @classmethod
    def version(cls) -> str:
        return "1.0.0"

    @classmethod
    def required_evidence(cls) -> List[type]:
        return [TyreInspectionEvidence]

    def execute(self, package: EvidencePackage) -> CheckResult:
        evidences = package.get_all_evidence(TyreInspectionEvidence)
        
        if not evidences:
            return CheckResult(
                check_key=self.key(),
                check_name=self.name(),
                status=CheckStatus.INCONCLUSIVE,
                message="No tyre inspection evidence available.",
            )
            
        latest = sorted(evidences, key=lambda e: e.inspection_date, reverse=True)[0]
        
        age_days = (latest.inspection_date - latest.tyre_installation_date).days
        
        if age_days <= self.config.maximum_tyre_age_days:
            return CheckResult(
                check_key=self.key(),
                check_name=self.name(),
                status=CheckStatus.PASS,
                message=f"Tyre age ({age_days} days) is within the maximum limit.",
                evidence_used=[str(latest.evidence_id)]
            )
        else:
            return CheckResult(
                check_key=self.key(),
                check_name=self.name(),
                status=CheckStatus.FAIL,
                message=f"Tyre age ({age_days} days) exceeds the maximum limit.",
                evidence_used=[str(latest.evidence_id)],
                metadata={"tyre_age_days": age_days}
            )
