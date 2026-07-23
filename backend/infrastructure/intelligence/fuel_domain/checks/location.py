from typing import List, Type
from infrastructure.intelligence.evidence.models import BaseEvidence, ReceiptEvidence, GPSEvidence
from infrastructure.intelligence.evidence.package import EvidencePackage
from infrastructure.intelligence.checks.base import BaseCheck
from infrastructure.intelligence.checks.models import CheckResult, CheckStatus
from infrastructure.intelligence.fuel_domain.config import FuelIntelligenceConfig
from infrastructure.intelligence.fuel_domain.geo import DistanceCalculator, HaversineDistanceCalculator


class FuelLocationCheck(BaseCheck):
    """
    Verifies that the GPS location is within the allowed radius of the fuel station.
    """
    def __init__(self, config: FuelIntelligenceConfig = None, distance_calculator: DistanceCalculator = None):
        self.config = config or FuelIntelligenceConfig()
        self.distance_calculator = distance_calculator or HaversineDistanceCalculator()

    @classmethod
    def key(cls) -> str:
        return "fuel.location_match"
        
    @classmethod
    def name(cls) -> str:
        return "Fuel Location Match"

    @classmethod
    def required_evidence(cls) -> List[Type[BaseEvidence]]:
        return [ReceiptEvidence, GPSEvidence]

    def execute(self, package: EvidencePackage) -> CheckResult:
        receipt = package.get_evidence(ReceiptEvidence)
        gps = package.get_evidence(GPSEvidence)
        
        evidence_ids = [str(receipt.evidence_id), str(gps.evidence_id)]
        
        # We assume the station coordinates are enriched into the receipt metadata by an earlier process
        station_lat = receipt.metadata.get("station_lat")
        station_lon = receipt.metadata.get("station_lon")
        
        if station_lat is None or station_lon is None:
            return CheckResult(
                check_key=self.key(),
                check_name=self.name(),
                status=CheckStatus.ERROR,
                message="Receipt metadata missing station coordinates for distance calculation.",
                evidence_used=evidence_ids
            )
            
        distance = self.distance_calculator.calculate_distance_meters(
            gps.latitude, gps.longitude,
            station_lat, station_lon
        )
        
        if distance <= self.config.location_radius_meters:
            return CheckResult(
                check_key=self.key(),
                check_name=self.name(),
                status=CheckStatus.PASS,
                message=f"Location matches. Distance: {distance:.2f}m",
                evidence_used=evidence_ids
            )
        else:
            return CheckResult(
                check_key=self.key(),
                check_name=self.name(),
                status=CheckStatus.FAIL,
                message=f"Location mismatch. Distance: {distance:.2f}m exceeds {self.config.location_radius_meters}m limit.",
                evidence_used=evidence_ids
            )
