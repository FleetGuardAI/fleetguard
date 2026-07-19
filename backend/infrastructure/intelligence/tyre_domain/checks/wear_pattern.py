"""
Tyre Intelligence - Tyre Wear Pattern Check
"""

from typing import List, Optional
from infrastructure.intelligence.checks.models import CheckResult, CheckStatus
from infrastructure.intelligence.checks.base import BaseCheck
from infrastructure.intelligence.evidence.package import EvidencePackage
from infrastructure.intelligence.evidence.models import TyreInspectionEvidence, WearPatternCategory
from infrastructure.intelligence.tyre_domain.config import TyreIntelligenceConfig


class TyreWearPatternCheck(BaseCheck):
    """
    Deterministically evaluates configured wear pattern categories.
    Passes if NORMAL, otherwise fails and flags the specific wear pattern.
    """
    
    def __init__(self, config: Optional[TyreIntelligenceConfig] = None):
        self.config = config or TyreIntelligenceConfig()

    @classmethod
    def key(cls) -> str:
        return "tyre.wear_pattern"

    @classmethod
    def name(cls) -> str:
        return "Tyre Wear Pattern Check"

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
        
        if latest.wear_pattern == WearPatternCategory.NORMAL:
            return CheckResult(
                check_key=self.key(),
                check_name=self.name(),
                status=CheckStatus.PASS,
                message="Normal tyre wear pattern observed.",
                evidence_used=[str(latest.evidence_id)]
            )
        else:
            return CheckResult(
                check_key=self.key(),
                check_name=self.name(),
                status=CheckStatus.FAIL,
                message=f"Abnormal tyre wear pattern observed: {latest.wear_pattern.value}.",
                evidence_used=[str(latest.evidence_id)],
                metadata={"wear_pattern": latest.wear_pattern.value}
            )
