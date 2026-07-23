"""
Tyre Intelligence - Tyre Damage Check
"""

from typing import List, Optional
from infrastructure.intelligence.checks.models import CheckResult, CheckStatus
from infrastructure.intelligence.checks.base import BaseCheck
from infrastructure.intelligence.evidence.package import EvidencePackage
from infrastructure.intelligence.evidence.models import TyreInspectionEvidence, DamageSeverity
from infrastructure.intelligence.tyre_domain.config import TyreIntelligenceConfig


class TyreDamageCheck(BaseCheck):
    """
    Determines whether inspection identified critical tyre damage.
    """
    
    def __init__(self, config: Optional[TyreIntelligenceConfig] = None):
        self.config = config or TyreIntelligenceConfig()

    @classmethod
    def key(cls) -> str:
        return "tyre.damage"

    @classmethod
    def name(cls) -> str:
        return "Tyre Damage Check"

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
        
        if latest.observed_damage_severity.value in self.config.critical_damage_types:
            return CheckResult(
                check_key=self.key(),
                check_name=self.name(),
                status=CheckStatus.FAIL,
                message=f"Critical tyre damage identified: {latest.observed_damage_severity.value}.",
                evidence_used=[str(latest.evidence_id)],
                metadata={"damage_severity": latest.observed_damage_severity.value}
            )
        else:
            return CheckResult(
                check_key=self.key(),
                check_name=self.name(),
                status=CheckStatus.PASS,
                message="No critical tyre damage identified.",
                evidence_used=[str(latest.evidence_id)]
            )
