"""
Route Intelligence - Trip Delay Check
"""

from typing import List, Optional
from infrastructure.intelligence.checks.models import CheckResult, CheckStatus
from infrastructure.intelligence.checks.base import BaseCheck
from infrastructure.intelligence.evidence.package import EvidencePackage
from infrastructure.intelligence.evidence.models import PlannedRouteEvidence, TripExecutionEvidence
from infrastructure.intelligence.route_domain.config import RouteIntelligenceConfig


class TripDelayCheck(BaseCheck):
    """
    Determines whether the trip exceeded the planned arrival window.
    """
    
    def __init__(self, config: Optional[RouteIntelligenceConfig] = None):
        self.config = config or RouteIntelligenceConfig()

    @classmethod
    def key(cls) -> str:
        return "route.trip_delay"

    @classmethod
    def name(cls) -> str:
        return "Trip Delay Check"

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
        
        delay_seconds = (execution.actual_end_time - planned.planned_end_time).total_seconds()
        delay_minutes = delay_seconds / 60.0
        
        if delay_minutes > self.config.maximum_trip_delay_minutes:
            return CheckResult(
                check_key=self.key(),
                check_name=self.name(),
                status=CheckStatus.FAIL,
                message=f"Trip delay of {delay_minutes:.1f} minutes exceeds the {self.config.maximum_trip_delay_minutes} minute threshold.",
                evidence_used=[str(planned.evidence_id), str(execution.evidence_id)],
                metadata={"delay_minutes": delay_minutes}
            )
        elif delay_minutes > 0:
            return CheckResult(
                check_key=self.key(),
                check_name=self.name(),
                status=CheckStatus.PASS,
                message=f"Trip arrived {delay_minutes:.1f} minutes late, but within threshold.",
                evidence_used=[str(planned.evidence_id), str(execution.evidence_id)],
                metadata={"delay_minutes": delay_minutes}
            )
        else:
            return CheckResult(
                check_key=self.key(),
                check_name=self.name(),
                status=CheckStatus.PASS,
                message=f"Trip arrived on time or early ({-delay_minutes:.1f} minutes ahead of schedule).",
                evidence_used=[str(planned.evidence_id), str(execution.evidence_id)],
                metadata={"delay_minutes": delay_minutes}
            )
