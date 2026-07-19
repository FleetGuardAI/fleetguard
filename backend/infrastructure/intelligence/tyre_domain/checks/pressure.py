"""
Tyre Intelligence - Tyre Pressure Check
"""

from typing import List, Optional
from infrastructure.intelligence.checks.models import CheckResult, CheckStatus
from infrastructure.intelligence.checks.base import BaseCheck
from infrastructure.intelligence.evidence.package import EvidencePackage
from infrastructure.intelligence.evidence.models import TyrePressureEvidence
from infrastructure.intelligence.tyre_domain.config import TyreIntelligenceConfig


class TyrePressureCheck(BaseCheck):
    """
    Determines whether tyre pressure is within the configured tolerance.
    """
    
    def __init__(self, config: Optional[TyreIntelligenceConfig] = None):
        self.config = config or TyreIntelligenceConfig()

    @classmethod
    def key(cls) -> str:
        return "tyre.pressure"

    @classmethod
    def name(cls) -> str:
        return "Tyre Pressure Tolerance Check"

    @classmethod
    def version(cls) -> str:
        return "1.0.0"

    @classmethod
    def required_evidence(cls) -> List[type]:
        return [TyrePressureEvidence]

    def execute(self, package: EvidencePackage) -> CheckResult:
        evidences = package.get_all_evidence(TyrePressureEvidence)
        
        if not evidences:
            return CheckResult(
                check_key=self.key(),
                check_name=self.name(),
                status=CheckStatus.INCONCLUSIVE,
                message="No tyre pressure evidence available.",
            )
            
        # For simplicity, evaluate the latest pressure reading.
        latest = sorted(evidences, key=lambda e: e.reading_date, reverse=True)[0]
        
        deviation = abs(latest.tyre_pressure_psi - latest.recommended_pressure_psi)
        
        if deviation <= self.config.maximum_pressure_deviation_psi:
            return CheckResult(
                check_key=self.key(),
                check_name=self.name(),
                status=CheckStatus.PASS,
                message=f"Tyre pressure is within {self.config.maximum_pressure_deviation_psi} PSI tolerance.",
                evidence_used=[str(latest.evidence_id)]
            )
        else:
            return CheckResult(
                check_key=self.key(),
                check_name=self.name(),
                status=CheckStatus.FAIL,
                message=f"Tyre pressure deviation exceeds {self.config.maximum_pressure_deviation_psi} PSI.",
                evidence_used=[str(latest.evidence_id)],
                metadata={"deviation_psi": deviation}
            )
