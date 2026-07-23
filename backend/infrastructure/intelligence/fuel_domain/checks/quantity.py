from typing import List, Type
from infrastructure.intelligence.evidence.models import BaseEvidence, ReceiptEvidence, FuelSensorEvidence
from infrastructure.intelligence.evidence.package import EvidencePackage
from infrastructure.intelligence.checks.base import BaseCheck
from infrastructure.intelligence.checks.models import CheckResult, CheckStatus
from infrastructure.intelligence.fuel_domain.config import FuelIntelligenceConfig


class FuelQuantityCheck(BaseCheck):
    """
    Verifies that the Receipt quantity matches the Fuel Sensor increase.
    """
    def __init__(self, config: FuelIntelligenceConfig = None):
        self.config = config or FuelIntelligenceConfig()

    @classmethod
    def key(cls) -> str:
        return "fuel.quantity_match"
        
    @classmethod
    def name(cls) -> str:
        return "Fuel Quantity Match"

    @classmethod
    def required_evidence(cls) -> List[Type[BaseEvidence]]:
        return [ReceiptEvidence, FuelSensorEvidence]

    def execute(self, package: EvidencePackage) -> CheckResult:
        receipt = package.get_evidence(ReceiptEvidence)
        sensor = package.get_evidence(FuelSensorEvidence)
        
        evidence_ids = [str(receipt.evidence_id), str(sensor.evidence_id)]
        
        if receipt.quantity is None:
            return CheckResult(
                check_key=self.key(),
                check_name=self.name(),
                status=CheckStatus.ERROR,
                message="Receipt is missing quantity field.",
                evidence_used=evidence_ids
            )
            
        sensor_increase = max(0.0, sensor.fuel_after - sensor.fuel_before)
        diff = abs(receipt.quantity - sensor_increase)
        
        if diff <= self.config.quantity_tolerance_liters:
            return CheckResult(
                check_key=self.key(),
                check_name=self.name(),
                status=CheckStatus.PASS,
                message=f"Quantity matches. Receipt: {receipt.quantity}L, Sensor: {sensor_increase}L",
                evidence_used=evidence_ids
            )
        else:
            return CheckResult(
                check_key=self.key(),
                check_name=self.name(),
                status=CheckStatus.FAIL,
                message=f"Quantity mismatch. Receipt: {receipt.quantity}L, Sensor: {sensor_increase}L. Diff: {diff}L",
                evidence_used=evidence_ids
            )
