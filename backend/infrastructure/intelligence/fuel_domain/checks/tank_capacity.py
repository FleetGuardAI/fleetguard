from typing import List, Type
from infrastructure.intelligence.evidence.models import BaseEvidence, ReceiptEvidence, FuelSensorEvidence, VehicleEvidence
from infrastructure.intelligence.evidence.package import EvidencePackage
from infrastructure.intelligence.checks.base import BaseCheck
from infrastructure.intelligence.checks.models import CheckResult, CheckStatus
from infrastructure.intelligence.fuel_domain.config import FuelIntelligenceConfig


class FuelTankCapacityCheck(BaseCheck):
    """
    Verifies that Previous Fuel Level + Receipt Quantity <= Tank Capacity + tolerance.
    """
    def __init__(self, config: FuelIntelligenceConfig = None):
        self.config = config or FuelIntelligenceConfig()

    @classmethod
    def key(cls) -> str:
        return "fuel.tank_capacity"
        
    @classmethod
    def name(cls) -> str:
        return "Fuel Tank Capacity Check"

    @classmethod
    def required_evidence(cls) -> List[Type[BaseEvidence]]:
        return [ReceiptEvidence, FuelSensorEvidence, VehicleEvidence]

    def execute(self, package: EvidencePackage) -> CheckResult:
        receipt = package.get_evidence(ReceiptEvidence)
        sensor = package.get_evidence(FuelSensorEvidence)
        vehicle = package.get_evidence(VehicleEvidence)
        
        evidence_ids = [str(receipt.evidence_id), str(sensor.evidence_id), str(vehicle.evidence_id)]
        
        if receipt.quantity is None:
            return CheckResult(
                check_key=self.key(),
                check_name=self.name(),
                status=CheckStatus.ERROR,
                message="Receipt is missing quantity field.",
                evidence_used=evidence_ids
            )
            
        projected_fuel = sensor.fuel_before + receipt.quantity
        allowed_capacity = vehicle.tank_capacity + self.config.tank_capacity_tolerance_liters
        
        if projected_fuel <= allowed_capacity:
            return CheckResult(
                check_key=self.key(),
                check_name=self.name(),
                status=CheckStatus.PASS,
                message=f"Capacity OK. Projected {projected_fuel}L fits within {allowed_capacity}L.",
                evidence_used=evidence_ids
            )
        else:
            overflow = projected_fuel - allowed_capacity
            return CheckResult(
                check_key=self.key(),
                check_name=self.name(),
                status=CheckStatus.FAIL,
                message=f"Capacity exceeded. Projected {projected_fuel}L exceeds allowed {allowed_capacity}L by {overflow}L.",
                evidence_used=evidence_ids
            )
