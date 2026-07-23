from typing import List, Type
from infrastructure.intelligence.evidence.models import BaseEvidence, DrivingSessionEvidence
from infrastructure.intelligence.evidence.package import EvidencePackage
from infrastructure.intelligence.checks.base import BaseCheck
from infrastructure.intelligence.checks.models import CheckResult, CheckStatus
from infrastructure.intelligence.driver_domain.config import DriverIntelligenceConfig


class HarshBrakingCheck(BaseCheck):
    def __init__(self, config: DriverIntelligenceConfig = None):
        self.config = config or DriverIntelligenceConfig()

    @classmethod
    def key(cls) -> str:
        return "driver.harsh_braking"

    @classmethod
    def name(cls) -> str:
        return "Harsh Braking Check"

    @classmethod
    def required_evidence(cls) -> List[Type[BaseEvidence]]:
        return [DrivingSessionEvidence]

    def execute(self, package: EvidencePackage) -> CheckResult:
        session = package.get_evidence(DrivingSessionEvidence)
        evidence_ids = [str(session.evidence_id)]
        
        if not session.telemetry_points:
            return CheckResult(
                check_key=self.key(),
                check_name=self.name(),
                status=CheckStatus.SKIPPED,
                message="No telemetry points available.",
                evidence_used=evidence_ids
            )
            
        # Braking is expected to be negative acceleration, find the minimum (most negative)
        min_accel = min([pt.get("acceleration_g", 0.0) for pt in session.telemetry_points])
        
        if min_accel < self.config.harsh_braking_g:
            return CheckResult(
                check_key=self.key(),
                check_name=self.name(),
                status=CheckStatus.FAIL,
                message=f"Harsh braking detected: {min_accel}g exceeds limit {self.config.harsh_braking_g}g.",
                evidence_used=evidence_ids
            )
        else:
            return CheckResult(
                check_key=self.key(),
                check_name=self.name(),
                status=CheckStatus.PASS,
                message=f"Maximum braking force {min_accel}g is within limits.",
                evidence_used=evidence_ids
            )
