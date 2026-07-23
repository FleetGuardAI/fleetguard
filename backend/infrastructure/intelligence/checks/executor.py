"""
Fleet Intelligence Engine - Check Executor
"""

import time
import traceback
from typing import List
from infrastructure.intelligence.evidence.package import EvidencePackage
from infrastructure.intelligence.checks.registry import CheckRegistry
from infrastructure.intelligence.checks.models import CheckResult, CheckStatus


class CheckExecutor:
    """
    Executes registered checks against an EvidencePackage.
    
    Responsibilities:
    - Determines whether required evidence is available.
    - Executes checks in a deterministic order.
    - Captures unexpected faults to isolate check failures.
    - Returns a collection of CheckResults.
    """
    
    def __init__(self, registry: CheckRegistry):
        self._registry = registry

    def execute_all(self, package: EvidencePackage) -> List[CheckResult]:
        """
        Executes all registered checks deterministically against the provided EvidencePackage.
        """
        results = []
        checks = self._registry.enumerate_checks()
        
        for check_cls in checks:
            check_key = check_cls.key()
            check_name = check_cls.name()
            
            # 1. Verify required evidence is present
            missing_required = []
            for req_ev_type in check_cls.required_evidence():
                if not package.has_evidence(req_ev_type):
                    missing_required.append(req_ev_type.__name__)
            
            if missing_required:
                # Bypass execution, yield SKIPPED
                results.append(CheckResult(
                    check_key=check_key,
                    check_name=check_name,
                    status=CheckStatus.SKIPPED,
                    message=f"Missing required evidence: {', '.join(missing_required)}",
                    evidence_used=[],
                    metadata={"missing_required_evidence": missing_required},
                    execution_time=0.0
                ))
                continue
                
            # 2. Execute the check safely
            start_time = time.perf_counter()
            try:
                # Instantiate statelessly for execution
                check_instance = check_cls()
                result = check_instance.execute(package)
                
                # If the check didn't explicitly track execution time, we can optionally override it,
                # but since CheckResult is frozen, we would need to rebuild it or let the check do it.
                # Since Pydantic models are frozen, we'll assume the executor wraps the time if not provided,
                # but to be safe with frozen models, we'll just accept what the check returned, 
                # or we can reconstruct it to inject the executor-measured time.
                
                # To guarantee executor timing, reconstruct the result:
                final_result = CheckResult(
                    check_key=result.check_key,
                    check_name=result.check_name,
                    status=result.status,
                    message=result.message,
                    evidence_used=result.evidence_used,
                    metadata=result.metadata,
                    execution_time=time.perf_counter() - start_time
                )
                results.append(final_result)
                
            except Exception as e:
                # A failed check must not stop execution of the remaining checks.
                end_time = time.perf_counter()
                results.append(CheckResult(
                    check_key=check_key,
                    check_name=check_name,
                    status=CheckStatus.ERROR,
                    message=f"Unhandled exception during check execution: {str(e)}",
                    evidence_used=[],
                    metadata={"traceback": traceback.format_exc()},
                    execution_time=end_time - start_time
                ))
                
        return results
