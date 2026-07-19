from typing import List, Type
from infrastructure.intelligence.evidence.models import BaseEvidence, DrivingSessionEvidence
from infrastructure.intelligence.evidence.package import EvidencePackage
from infrastructure.intelligence.checks.base import BaseCheck
from infrastructure.intelligence.checks.models import CheckResult, CheckStatus
from infrastructure.intelligence.driver_domain.config import DriverIntelligenceConfig
from infrastructure.intelligence.fuel_domain.geo import HaversineDistanceCalculator


class RouteComplianceCheck(BaseCheck):
    def __init__(self, config: DriverIntelligenceConfig = None):
        self.config = config or DriverIntelligenceConfig()
        self.distance_calculator = HaversineDistanceCalculator()

    @classmethod
    def key(cls) -> str:
        return "driver.route_compliance"

    @classmethod
    def name(cls) -> str:
        return "Route Compliance Check"

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
            
        if not session.expected_route_polygon:
            return CheckResult(
                check_key=self.key(),
                check_name=self.name(),
                status=CheckStatus.SKIPPED,
                message="No expected route provided.",
                evidence_used=evidence_ids
            )
            
        # Simplified point-in-polygon / distance-to-line check for this milestone
        # We'll check if every telemetry point is within `route_deviation_meters` of AT LEAST ONE polygon point.
        # This is a naive nearest-neighbor approach rather than true geometric distance to segments, 
        # but sufficient to prove the framework integration.
        
        max_deviation = 0.0
        
        for pt in session.telemetry_points:
            pt_lat = pt.get("latitude")
            pt_lon = pt.get("longitude")
            
            if pt_lat is None or pt_lon is None:
                continue
                
            # Find distance to closest route point
            min_dist = float('inf')
            for r_pt in session.expected_route_polygon:
                dist = self.distance_calculator.calculate_distance_meters(
                    pt_lat, pt_lon,
                    r_pt["lat"], r_pt["lon"]
                )
                if dist < min_dist:
                    min_dist = dist
                    
            if min_dist > max_deviation:
                max_deviation = min_dist
                
        if max_deviation > self.config.route_deviation_meters:
            return CheckResult(
                check_key=self.key(),
                check_name=self.name(),
                status=CheckStatus.FAIL,
                message=f"Route deviation detected: {max_deviation:.1f}m exceeds limit {self.config.route_deviation_meters}m.",
                evidence_used=evidence_ids
            )
        else:
            return CheckResult(
                check_key=self.key(),
                check_name=self.name(),
                status=CheckStatus.PASS,
                message=f"Maximum route deviation {max_deviation:.1f}m is within limits.",
                evidence_used=evidence_ids
            )
