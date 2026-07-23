from typing import List, Type
from datetime import datetime, timezone
from infrastructure.intelligence.evidence.models import BaseEvidence, MaintenanceHistoryEvidence
from infrastructure.intelligence.evidence.package import EvidencePackage
from infrastructure.intelligence.checks.base import BaseCheck
from infrastructure.intelligence.checks.models import CheckResult, CheckStatus
from infrastructure.intelligence.maintenance_domain.config import MaintenanceIntelligenceConfig


class MaintenanceTimeOverdueCheck(BaseCheck):
    def __init__(self, config: MaintenanceIntelligenceConfig = None):
        self.config = config or MaintenanceIntelligenceConfig()

    @classmethod
    def key(cls) -> str:
        return "maintenance.time_overdue"

    @classmethod
    def name(cls) -> str:
        return "Maintenance Time Interval Overdue Check"

    @classmethod
    def required_evidence(cls) -> List[Type[BaseEvidence]]:
        return [MaintenanceHistoryEvidence]

    def execute(self, package: EvidencePackage) -> CheckResult:
        history_records = package.get_all_evidence(MaintenanceHistoryEvidence)
        
        if not history_records:
            return CheckResult(
                check_key=self.key(),
                check_name=self.name(),
                status=CheckStatus.SKIPPED,
                message="No maintenance history records available to determine time interval.",
                evidence_used=[]
            )
            
        recent_history = max(history_records, key=lambda r: r.service_date)
        evidence_ids = [str(recent_history.evidence_id)]
        
        now = datetime.now(timezone.utc)
        
        service_date = recent_history.service_date
        if service_date.tzinfo is None:
            service_date = service_date.replace(tzinfo=timezone.utc)
            
        days_since_last_service = (now - service_date).days
        
        if days_since_last_service > self.config.service_interval_days:
            overdue_days = days_since_last_service - self.config.service_interval_days
            return CheckResult(
                check_key=self.key(),
                check_name=self.name(),
                status=CheckStatus.FAIL,
                message=f"Maintenance interval exceeded by {overdue_days} days.",
                evidence_used=evidence_ids
            )
        else:
            remaining_days = self.config.service_interval_days - days_since_last_service
            return CheckResult(
                check_key=self.key(),
                check_name=self.name(),
                status=CheckStatus.PASS,
                message=f"Maintenance interval expires in {remaining_days} days.",
                evidence_used=evidence_ids
            )
