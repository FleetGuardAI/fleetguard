from typing import List, Type
from infrastructure.intelligence.evidence.models import BaseEvidence, DrivingSessionEvidence
from infrastructure.intelligence.evidence.package import EvidencePackage
from infrastructure.intelligence.checks.base import BaseCheck
from infrastructure.intelligence.checks.models import CheckResult, CheckStatus
from infrastructure.intelligence.driver_domain.config import DriverIntelligenceConfig


class DriverOverspeedCheck(BaseCheck):
    def __init__(self, config: DriverIntelligenceConfig = None):
        self.config = config or DriverIntelligenceConfig()

    @classmethod
    def key(cls) -> str:
        return "driver.overspeed"

    @classmethod
    def name(cls) -> str:
        return "Driver Overspeed Check"

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
                message="No telemetry points available in the driving session.",
                evidence_used=evidence_ids
            )
            
        max_speed = max([pt.get("speed_kmh", 0.0) for pt in session.telemetry_points])
        
        if max_speed > self.config.max_speed_kmh:
            return CheckResult(
                check_key=self.key(),
                check_name=self.name(),
                status=CheckStatus.FAIL,
                message=f"Maximum speed {max_speed} km/h exceeded limit of {self.config.max_speed_kmh} km/h.",
                evidence_used=evidence_ids
            )
        else:
            return CheckResult(
                check_key=self.key(),
                check_name=self.name(),
                status=CheckStatus.PASS,
                message=f"Maximum speed {max_speed} km/h is within limit of {self.config.max_speed_kmh} km/h.",
                evidence_used=evidence_ids
            )
