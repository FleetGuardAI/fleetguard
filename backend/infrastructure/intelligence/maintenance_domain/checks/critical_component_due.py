from typing import List, Type
from infrastructure.intelligence.evidence.models import BaseEvidence, MaintenanceHistoryEvidence
from infrastructure.intelligence.evidence.package import EvidencePackage
from infrastructure.intelligence.checks.base import BaseCheck
from infrastructure.intelligence.checks.models import CheckResult, CheckStatus
from infrastructure.intelligence.maintenance_domain.config import MaintenanceIntelligenceConfig


class CriticalComponentDueCheck(BaseCheck):
    def __init__(self, config: MaintenanceIntelligenceConfig = None):
        self.config = config or MaintenanceIntelligenceConfig()

    @classmethod
    def key(cls) -> str:
        return "maintenance.critical_component_due"

    @classmethod
    def name(cls) -> str:
        return "Critical Component Maintenance Due Check"

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
                message="No maintenance history records available to determine component wear.",
                evidence_used=[]
            )
            
        recent_history = max(history_records, key=lambda r: r.service_date)
        evidence_ids = [str(recent_history.evidence_id)]
        
        # Simple heuristic for this milestone: if odometer has crossed tyre or oil rotation intervals 
        # since the last specific service type, flag it.
        # Since we don't have full history tracking in evidence (just single records), 
        # we'll look for active diagnostic codes or assume missing history is a problem if odometer is high.
        
        critical_codes = []
        for code in recent_history.diagnostic_codes:
            if code.startswith("CRIT_"):
                critical_codes.append(code)
                
        if critical_codes:
            return CheckResult(
                check_key=self.key(),
                check_name=self.name(),
                status=CheckStatus.FAIL,
                message=f"Critical safety components require immediate inspection: {', '.join(critical_codes)}.",
                evidence_used=evidence_ids
            )
        else:
            return CheckResult(
                check_key=self.key(),
                check_name=self.name(),
                status=CheckStatus.PASS,
                message="No critical components are explicitly due for maintenance.",
                evidence_used=evidence_ids
            )
