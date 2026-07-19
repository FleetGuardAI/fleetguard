from typing import List, Type
from infrastructure.intelligence.evidence.models import BaseEvidence, MaintenanceScheduleEvidence, MaintenanceHistoryEvidence
from infrastructure.intelligence.evidence.package import EvidencePackage
from infrastructure.intelligence.checks.base import BaseCheck
from infrastructure.intelligence.checks.models import CheckResult, CheckStatus
from infrastructure.intelligence.maintenance_domain.config import MaintenanceIntelligenceConfig


class MaintenanceDistanceOverdueCheck(BaseCheck):
    def __init__(self, config: MaintenanceIntelligenceConfig = None):
        self.config = config or MaintenanceIntelligenceConfig()

    @classmethod
    def key(cls) -> str:
        return "maintenance.distance_overdue"

    @classmethod
    def name(cls) -> str:
        return "Maintenance Distance Overdue Check"

    @classmethod
    def required_evidence(cls) -> List[Type[BaseEvidence]]:
        return [MaintenanceScheduleEvidence, MaintenanceHistoryEvidence]

    def execute(self, package: EvidencePackage) -> CheckResult:
        schedule = package.get_evidence(MaintenanceScheduleEvidence)
        history_records = package.get_all_evidence(MaintenanceHistoryEvidence)
        
        # We need the most recent history record to know current odometer
        if not history_records:
            return CheckResult(
                check_key=self.key(),
                check_name=self.name(),
                status=CheckStatus.SKIPPED,
                message="No maintenance history records available to determine current odometer.",
                evidence_used=[str(schedule.evidence_id)]
            )
            
        recent_history = max(history_records, key=lambda r: r.service_date)
        evidence_ids = [str(schedule.evidence_id), str(recent_history.evidence_id)]
        
        if schedule.next_service_due_km is None:
            return CheckResult(
                check_key=self.key(),
                check_name=self.name(),
                status=CheckStatus.SKIPPED,
                message="No next service due km configured.",
                evidence_used=evidence_ids
            )
            
        current_km = recent_history.odometer_km
        
        if current_km > schedule.next_service_due_km:
            overdue_km = current_km - schedule.next_service_due_km
            return CheckResult(
                check_key=self.key(),
                check_name=self.name(),
                status=CheckStatus.FAIL,
                message=f"Service is distance overdue by {overdue_km:.1f} km.",
                evidence_used=evidence_ids
            )
        else:
            remaining_km = schedule.next_service_due_km - current_km
            return CheckResult(
                check_key=self.key(),
                check_name=self.name(),
                status=CheckStatus.PASS,
                message=f"Service is due in {remaining_km:.1f} km.",
                evidence_used=evidence_ids
            )
