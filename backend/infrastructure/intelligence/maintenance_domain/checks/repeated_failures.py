from typing import List, Type, Dict
from datetime import datetime, timezone
from infrastructure.intelligence.evidence.models import BaseEvidence, MaintenanceHistoryEvidence
from infrastructure.intelligence.evidence.package import EvidencePackage
from infrastructure.intelligence.checks.base import BaseCheck
from infrastructure.intelligence.checks.models import CheckResult, CheckStatus
from infrastructure.intelligence.maintenance_domain.config import MaintenanceIntelligenceConfig


class RepeatedFailureCheck(BaseCheck):
    def __init__(self, config: MaintenanceIntelligenceConfig = None):
        self.config = config or MaintenanceIntelligenceConfig()

    @classmethod
    def key(cls) -> str:
        return "maintenance.repeated_failures"

    @classmethod
    def name(cls) -> str:
        return "Repeated Component Failure Check"

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
                message="No maintenance history records available.",
                evidence_used=[]
            )
            
        now = datetime.now(timezone.utc)
        evidence_ids = []
        failure_counts: Dict[str, int] = {}
        
        for record in history_records:
            evidence_ids.append(str(record.evidence_id))
            
            service_date = record.service_date
            if service_date.tzinfo is None:
                service_date = service_date.replace(tzinfo=timezone.utc)
                
            days_ago = (now - service_date).days
            if days_ago <= self.config.repeated_failure_time_window_days:
                for failure in record.reported_component_failures:
                    failure_counts[failure] = failure_counts.get(failure, 0) + 1
                    
        repeated_failures = []
        for component, count in failure_counts.items():
            if count >= self.config.repeated_failure_threshold_count:
                repeated_failures.append(f"{component} ({count} times)")
                
        if repeated_failures:
            return CheckResult(
                check_key=self.key(),
                check_name=self.name(),
                status=CheckStatus.FAIL,
                message=f"Repeated failures detected within {self.config.repeated_failure_time_window_days} days: {', '.join(repeated_failures)}.",
                evidence_used=evidence_ids
            )
        else:
            return CheckResult(
                check_key=self.key(),
                check_name=self.name(),
                status=CheckStatus.PASS,
                message="No repeated component failures detected.",
                evidence_used=evidence_ids
            )
