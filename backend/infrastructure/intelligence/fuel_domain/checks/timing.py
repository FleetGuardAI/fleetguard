from typing import List, Type
from infrastructure.intelligence.evidence.models import BaseEvidence, ReceiptEvidence, GPSEvidence, FuelSensorEvidence
from infrastructure.intelligence.evidence.package import EvidencePackage
from infrastructure.intelligence.checks.base import BaseCheck
from infrastructure.intelligence.checks.models import CheckResult, CheckStatus
from infrastructure.intelligence.fuel_domain.config import FuelIntelligenceConfig


class FuelTimingCheck(BaseCheck):
    """
    Verifies that the timestamps across Receipt, GPS, and Fuel Sensor are within the permitted time window.
    """
    def __init__(self, config: FuelIntelligenceConfig = None):
        self.config = config or FuelIntelligenceConfig()

    @classmethod
    def key(cls) -> str:
        return "fuel.timing_match"
        
    @classmethod
    def name(cls) -> str:
        return "Fuel Timing Match"

    @classmethod
    def required_evidence(cls) -> List[Type[BaseEvidence]]:
        return [ReceiptEvidence, GPSEvidence, FuelSensorEvidence]

    def execute(self, package: EvidencePackage) -> CheckResult:
        receipt = package.get_evidence(ReceiptEvidence)
        gps = package.get_evidence(GPSEvidence)
        sensor = package.get_evidence(FuelSensorEvidence)
        
        timestamps = [
            receipt.collected_at,
            gps.collected_at,
            sensor.collected_at
        ]
        
        # Calculate max time difference
        min_ts = min(timestamps)
        max_ts = max(timestamps)
        diff_seconds = (max_ts - min_ts).total_seconds()
        
        evidence_ids = [str(receipt.evidence_id), str(gps.evidence_id), str(sensor.evidence_id)]
        
        if diff_seconds <= self.config.timing_window_seconds:
            return CheckResult(
                check_key=self.key(),
                check_name=self.name(),
                status=CheckStatus.PASS,
                message=f"Timing matches. Maximum divergence is {diff_seconds} seconds.",
                evidence_used=evidence_ids
            )
        else:
            return CheckResult(
                check_key=self.key(),
                check_name=self.name(),
                status=CheckStatus.FAIL,
                message=f"Timing mismatch. Divergence of {diff_seconds}s exceeds {self.config.timing_window_seconds}s window.",
                evidence_used=evidence_ids
            )
