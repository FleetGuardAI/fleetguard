from typing import List, Type
from datetime import datetime, timezone
from infrastructure.intelligence.evidence.models import BaseEvidence, MaintenanceScheduleEvidence
from infrastructure.intelligence.evidence.package import EvidencePackage
from infrastructure.intelligence.checks.base import BaseCheck
from infrastructure.intelligence.checks.models import CheckResult, CheckStatus
from infrastructure.intelligence.maintenance_domain.config import MaintenanceIntelligenceConfig


class MaintenanceServiceOverdueCheck(BaseCheck):
    def __init__(self, config: MaintenanceIntelligenceConfig = None):
        self.config = config or MaintenanceIntelligenceConfig()

    @classmethod
    def key(cls) -> str:
        return "maintenance.service_overdue"

    @classmethod
    def name(cls) -> str:
        return "Maintenance Service Overdue Check"

    @classmethod
    def required_evidence(cls) -> List[Type[BaseEvidence]]:
        return [MaintenanceScheduleEvidence]

    def execute(self, package: EvidencePackage) -> CheckResult:
        schedule = package.get_evidence(MaintenanceScheduleEvidence)
        evidence_ids = [str(schedule.evidence_id)]
        
        if not schedule.next_service_due_date:
            return CheckResult(
                check_key=self.key(),
                check_name=self.name(),
                status=CheckStatus.SKIPPED,
                message="No service due date configured.",
                evidence_used=evidence_ids
            )
            
        now = datetime.now(timezone.utc)
        
        # Ensure timezone-aware comparison
        due_date = schedule.next_service_due_date
        if due_date.tzinfo is None:
            due_date = due_date.replace(tzinfo=timezone.utc)
            
        if now > due_date:
            days_overdue = (now - due_date).days
            return CheckResult(
                check_key=self.key(),
                check_name=self.name(),
                status=CheckStatus.FAIL,
                message=f"Service is overdue by {days_overdue} days.",
                evidence_used=evidence_ids
            )
        else:
            days_remaining = (due_date - now).days
            return CheckResult(
                check_key=self.key(),
                check_name=self.name(),
                status=CheckStatus.PASS,
                message=f"Service is due in {days_remaining} days.",
                evidence_used=evidence_ids
            )
