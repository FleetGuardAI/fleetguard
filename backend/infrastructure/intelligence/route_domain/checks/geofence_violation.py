"""
Route Intelligence - Geofence Violation Check
"""

from typing import List, Optional
from infrastructure.intelligence.checks.models import CheckResult, CheckStatus
from infrastructure.intelligence.checks.base import BaseCheck
from infrastructure.intelligence.evidence.package import EvidencePackage
from infrastructure.intelligence.evidence.models import GeofenceEventEvidence, GeofenceEventType
from infrastructure.intelligence.route_domain.config import RouteIntelligenceConfig


class GeofenceViolationCheck(BaseCheck):
    """
    Determines whether the vehicle entered or exited restricted geofenced areas.
    """
    
    def __init__(self, config: Optional[RouteIntelligenceConfig] = None):
        self.config = config or RouteIntelligenceConfig()

    @classmethod
    def key(cls) -> str:
        return "route.geofence_violation"

    @classmethod
    def name(cls) -> str:
        return "Geofence Violation Check"

    @classmethod
    def version(cls) -> str:
        return "1.0.0"

    @classmethod
    def required_evidence(cls) -> List[type]:
        return [GeofenceEventEvidence]

    def execute(self, package: EvidencePackage) -> CheckResult:
        geofence_events = package.get_all_evidence(GeofenceEventEvidence)
        
        if not geofence_events:
            # If no geofence events, there are no violations
            return CheckResult(
                check_key=self.key(),
                check_name=self.name(),
                status=CheckStatus.PASS,
                message="No geofence events detected.",
                evidence_used=[]
            )
            
        violations = []
        evidence_ids = []
        
        for event in geofence_events:
            evidence_ids.append(str(event.evidence_id))
            if event.geofence_id in self.config.restricted_geofence_ids:
                if event.event_type == GeofenceEventType.ENTER:
                    violations.append(event)
                    
        if violations:
            return CheckResult(
                check_key=self.key(),
                check_name=self.name(),
                status=CheckStatus.FAIL,
                message=f"Vehicle entered {len(violations)} restricted geofence(s).",
                evidence_used=evidence_ids,
                metadata={"violation_count": len(violations)}
            )
        else:
            return CheckResult(
                check_key=self.key(),
                check_name=self.name(),
                status=CheckStatus.PASS,
                message="No restricted geofence violations detected.",
                evidence_used=evidence_ids
            )
