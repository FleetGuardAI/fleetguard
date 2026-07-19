"""
Route Intelligence - Unauthorized Stop Check
"""

import math
from typing import List, Optional
from infrastructure.intelligence.checks.models import CheckResult, CheckStatus
from infrastructure.intelligence.checks.base import BaseCheck
from infrastructure.intelligence.evidence.package import EvidencePackage
from infrastructure.intelligence.evidence.models import TripExecutionEvidence, ApprovedStopEvidence
from infrastructure.intelligence.route_domain.config import RouteIntelligenceConfig
from infrastructure.intelligence.route_domain.checks.deviation import haversine_distance


class UnauthorizedStopCheck(BaseCheck):
    """
    Determines whether the vehicle remained stopped longer than the configured threshold 
    at locations not explicitly listed in ApprovedStopEvidence.
    """
    
    def __init__(self, config: Optional[RouteIntelligenceConfig] = None):
        self.config = config or RouteIntelligenceConfig()

    @classmethod
    def key(cls) -> str:
        return "route.unauthorized_stop"

    @classmethod
    def name(cls) -> str:
        return "Unauthorized Stop Check"

    @classmethod
    def version(cls) -> str:
        return "1.0.0"

    @classmethod
    def required_evidence(cls) -> List[type]:
        return [TripExecutionEvidence, ApprovedStopEvidence]

    def execute(self, package: EvidencePackage) -> CheckResult:
        exec_list = package.get_all_evidence(TripExecutionEvidence)
        approved_list = package.get_all_evidence(ApprovedStopEvidence)
        
        if not exec_list or not approved_list:
            return CheckResult(
                check_key=self.key(),
                check_name=self.name(),
                status=CheckStatus.INCONCLUSIVE,
                message="Missing TripExecutionEvidence or ApprovedStopEvidence.",
                evidence_used=[]
            )
            
        execution = exec_list[0]
        approved = approved_list[0]
        
        unauthorized_stops = []
        
        for stop in execution.stop_locations:
            duration = stop.get("duration_minutes", 0.0)
            if duration <= self.config.unauthorized_stop_threshold_minutes:
                continue
                
            lat = stop.get("lat")
            lon = stop.get("lon")
            
            is_approved = False
            for app_stop in approved.approved_stops:
                app_lat = app_stop.get("lat")
                app_lon = app_stop.get("lon")
                app_radius = app_stop.get("radius_meters", 100.0)
                
                if app_lat is not None and app_lon is not None:
                    dist = haversine_distance(lat, lon, app_lat, app_lon)
                    if dist <= app_radius:
                        is_approved = True
                        break
                        
            if not is_approved:
                unauthorized_stops.append(stop)
                
        if unauthorized_stops:
            return CheckResult(
                check_key=self.key(),
                check_name=self.name(),
                status=CheckStatus.FAIL,
                message=f"Detected {len(unauthorized_stops)} unauthorized stop(s) exceeding {self.config.unauthorized_stop_threshold_minutes} minutes.",
                evidence_used=[str(execution.evidence_id), str(approved.evidence_id)],
                metadata={"unauthorized_stops_count": len(unauthorized_stops)}
            )
        else:
            return CheckResult(
                check_key=self.key(),
                check_name=self.name(),
                status=CheckStatus.PASS,
                message="No unauthorized stops detected.",
                evidence_used=[str(execution.evidence_id), str(approved.evidence_id)]
            )
