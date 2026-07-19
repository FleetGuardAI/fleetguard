"""
Route Intelligence - Route Deviation Check
"""

import math
from typing import List, Optional
from infrastructure.intelligence.checks.models import CheckResult, CheckStatus
from infrastructure.intelligence.checks.base import BaseCheck
from infrastructure.intelligence.evidence.package import EvidencePackage
from infrastructure.intelligence.evidence.models import PlannedRouteEvidence, TripExecutionEvidence
from infrastructure.intelligence.route_domain.config import RouteIntelligenceConfig


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great circle distance in meters between two points on the earth."""
    R = 6371000  # radius of Earth in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda / 2.0) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


class RouteDeviationCheck(BaseCheck):
    """
    Determines whether the executed route exceeds the configured route deviation threshold 
    by calculating the maximum distance (in meters) of any GPS point from the planned route line.
    """
    
    def __init__(self, config: Optional[RouteIntelligenceConfig] = None):
        self.config = config or RouteIntelligenceConfig()

    @classmethod
    def key(cls) -> str:
        return "route.deviation"

    @classmethod
    def name(cls) -> str:
        return "Route Deviation Check"

    @classmethod
    def version(cls) -> str:
        return "1.0.0"

    @classmethod
    def required_evidence(cls) -> List[type]:
        return [PlannedRouteEvidence, TripExecutionEvidence]

    def execute(self, package: EvidencePackage) -> CheckResult:
        planned_list = package.get_all_evidence(PlannedRouteEvidence)
        exec_list = package.get_all_evidence(TripExecutionEvidence)
        
        if not planned_list or not exec_list:
            return CheckResult(
                check_key=self.key(),
                check_name=self.name(),
                status=CheckStatus.INCONCLUSIVE,
                message="Missing PlannedRouteEvidence or TripExecutionEvidence.",
                evidence_used=[]
            )
            
        planned = planned_list[0]
        execution = exec_list[0]
        
        if not planned.gps_track or not execution.gps_track:
            return CheckResult(
                check_key=self.key(),
                check_name=self.name(),
                status=CheckStatus.INCONCLUSIVE,
                message="GPS tracks are missing in the evidence.",
                evidence_used=[str(planned.evidence_id), str(execution.evidence_id)]
            )

        max_deviation = 0.0
        
        # Simple point-to-point shortest distance evaluation for deviation
        for actual_pt in execution.gps_track:
            act_lat = actual_pt["lat"]
            act_lon = actual_pt["lon"]
            
            min_dist_to_route = float('inf')
            for plan_pt in planned.gps_track:
                dist = haversine_distance(act_lat, act_lon, plan_pt["lat"], plan_pt["lon"])
                if dist < min_dist_to_route:
                    min_dist_to_route = dist
                    
            if min_dist_to_route > max_deviation:
                max_deviation = min_dist_to_route
                
        if max_deviation > self.config.maximum_route_deviation_meters:
            return CheckResult(
                check_key=self.key(),
                check_name=self.name(),
                status=CheckStatus.FAIL,
                message=f"Maximum route deviation of {max_deviation:.1f}m exceeds the {self.config.maximum_route_deviation_meters}m threshold.",
                evidence_used=[str(planned.evidence_id), str(execution.evidence_id)],
                metadata={"max_deviation_meters": max_deviation}
            )
        else:
            return CheckResult(
                check_key=self.key(),
                check_name=self.name(),
                status=CheckStatus.PASS,
                message=f"Maximum route deviation ({max_deviation:.1f}m) is within acceptable limits.",
                evidence_used=[str(planned.evidence_id), str(execution.evidence_id)]
            )
