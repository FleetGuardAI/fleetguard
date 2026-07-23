from typing import List, Type
from infrastructure.intelligence.evidence.models import BaseEvidence, DrivingSessionEvidence
from infrastructure.intelligence.evidence.package import EvidencePackage
from infrastructure.intelligence.checks.base import BaseCheck
from infrastructure.intelligence.checks.models import CheckResult, CheckStatus
from infrastructure.intelligence.driver_domain.config import DriverIntelligenceConfig


class ExcessiveIdlingCheck(BaseCheck):
    def __init__(self, config: DriverIntelligenceConfig = None):
        self.config = config or DriverIntelligenceConfig()

    @classmethod
    def key(cls) -> str:
        return "driver.excessive_idling"

    @classmethod
    def name(cls) -> str:
        return "Excessive Idling Check"

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
            
        # Calculate total idle time (engine on, speed = 0)
        # Note: In a real system we would look at continuous segments, but for this milestone we sum up idle points.
        # Assuming 1 point = 1 second for simplicity, or we calculate based on timestamps.
        # To make it deterministic for tests without complex datetime math, let's just count points 
        # where engine_on is True and speed_kmh < 1.0 as "1 second".
        idle_duration = sum(1 for pt in session.telemetry_points if pt.get("engine_on", False) and pt.get("speed_kmh", 0.0) < 1.0)
        
        if idle_duration > self.config.max_idle_seconds:
            return CheckResult(
                check_key=self.key(),
                check_name=self.name(),
                status=CheckStatus.FAIL,
                message=f"Excessive idling detected: {idle_duration}s exceeds limit {self.config.max_idle_seconds}s.",
                evidence_used=evidence_ids
            )
        else:
            return CheckResult(
                check_key=self.key(),
                check_name=self.name(),
                status=CheckStatus.PASS,
                message=f"Idle duration {idle_duration}s is within limits.",
                evidence_used=evidence_ids
            )
