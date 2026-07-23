"""
Tyre Intelligence - Tyre Tread Depth Check
"""

from typing import List, Optional
from infrastructure.intelligence.checks.models import CheckResult, CheckStatus
from infrastructure.intelligence.checks.base import BaseCheck
from infrastructure.intelligence.evidence.package import EvidencePackage
from infrastructure.intelligence.evidence.models import TyreInspectionEvidence
from infrastructure.intelligence.tyre_domain.config import TyreIntelligenceConfig


class TyreTreadDepthCheck(BaseCheck):
    """
    Determines whether tread depth satisfies minimum requirements.
    """
    
    def __init__(self, config: Optional[TyreIntelligenceConfig] = None):
        self.config = config or TyreIntelligenceConfig()

    @classmethod
    def key(cls) -> str:
        return "tyre.tread_depth"

    @classmethod
    def name(cls) -> str:
        return "Tyre Tread Depth Check"

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
        
        if latest.tread_depth_mm >= self.config.minimum_tread_depth_mm:
            return CheckResult(
                check_key=self.key(),
                check_name=self.name(),
                status=CheckStatus.PASS,
                message=f"Tread depth ({latest.tread_depth_mm}mm) meets minimum requirements.",
                evidence_used=[str(latest.evidence_id)]
            )
        else:
            return CheckResult(
                check_key=self.key(),
                check_name=self.name(),
                status=CheckStatus.FAIL,
                message=f"Tread depth ({latest.tread_depth_mm}mm) is below minimum requirements.",
                evidence_used=[str(latest.evidence_id)],
                metadata={"tread_depth_mm": latest.tread_depth_mm}
            )
