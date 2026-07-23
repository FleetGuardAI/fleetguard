"""
Route Intelligence - Excessive Detour Check
"""

from typing import List, Optional
from infrastructure.intelligence.checks.models import CheckResult, CheckStatus
from infrastructure.intelligence.checks.base import BaseCheck
from infrastructure.intelligence.evidence.package import EvidencePackage
from infrastructure.intelligence.evidence.models import PlannedRouteEvidence, TripExecutionEvidence
from infrastructure.intelligence.route_domain.config import RouteIntelligenceConfig
from infrastructure.intelligence.route_domain.checks.deviation import haversine_distance


def calculate_track_distance(track: List[dict]) -> float:
    distance = 0.0
    for i in range(1, len(track)):
        prev = track[i-1]
        curr = track[i]
        distance += haversine_distance(prev["lat"], prev["lon"], curr["lat"], curr["lon"])
    return distance


class ExcessiveDetourCheck(BaseCheck):
    """
    Determines whether the actual travelled distance significantly exceeded the planned route.
    """
    
    def __init__(self, config: Optional[RouteIntelligenceConfig] = None):
        self.config = config or RouteIntelligenceConfig()

    @classmethod
    def key(cls) -> str:
        return "route.excessive_detour"

    @classmethod
    def name(cls) -> str:
        return "Excessive Detour Check"

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
            
        planned_distance_meters = calculate_track_distance(planned.gps_track)
        actual_distance_meters = calculate_track_distance(execution.gps_track)
        
        if planned_distance_meters == 0:
            return CheckResult(
                check_key=self.key(),
                check_name=self.name(),
                status=CheckStatus.INCONCLUSIVE,
                message="Planned route distance is zero.",
                evidence_used=[str(planned.evidence_id), str(execution.evidence_id)]
            )

        variance_percentage = ((actual_distance_meters - planned_distance_meters) / planned_distance_meters) * 100
        
        if variance_percentage > self.config.permitted_route_variance_percentage:
            return CheckResult(
                check_key=self.key(),
                check_name=self.name(),
                status=CheckStatus.FAIL,
                message=f"Trip distance variance ({variance_percentage:.1f}%) exceeds permitted threshold ({self.config.permitted_route_variance_percentage}%).",
                evidence_used=[str(planned.evidence_id), str(execution.evidence_id)],
                metadata={"variance_percentage": variance_percentage, "actual_distance_meters": actual_distance_meters, "planned_distance_meters": planned_distance_meters}
            )
        else:
            return CheckResult(
                check_key=self.key(),
                check_name=self.name(),
                status=CheckStatus.PASS,
                message=f"Trip distance variance ({variance_percentage:.1f}%) is within acceptable limits.",
                evidence_used=[str(planned.evidence_id), str(execution.evidence_id)],
                metadata={"variance_percentage": variance_percentage, "actual_distance_meters": actual_distance_meters, "planned_distance_meters": planned_distance_meters}
            )
