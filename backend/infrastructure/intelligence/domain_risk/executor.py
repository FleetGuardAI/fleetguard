"""
Fleet Intelligence Engine - Domain Risk Executor
"""

import time
import traceback
from typing import List
from infrastructure.intelligence.assessments.models import AssessmentResult
from infrastructure.intelligence.domain_risk.registry import DomainRiskRegistry
from infrastructure.intelligence.domain_risk.models import DomainRiskProfile, DomainRiskStatus, RiskLevel


class DomainRiskExecutor:
    """
    Executes registered domain risk engines against a collection of AssessmentResults.
    
    Responsibilities:
    - Iterates over all registered domain risk engines deterministically.
    - Passes the *complete* list of AssessmentResults to each engine.
    - Captures unexpected faults to isolate engine failures.
    - Collects DomainRiskProfiles.
    - Does NOT decide whether an engine's status is COMPLETE, PARTIAL, or INCONCLUSIVE, 
      nor does it determine the RiskLevel (unless an unhandled error occurs).
    """
    
    def __init__(self, registry: DomainRiskRegistry):
        self._registry = registry

    def execute_all(self, assessments: List[AssessmentResult]) -> List[DomainRiskProfile]:
        """
        Executes all registered risk engines deterministically against the provided AssessmentResults.
        """
        results = []
        engines = self._registry.enumerate_engines()
        
        for engine_cls in engines:
            start_time = time.perf_counter()
            try:
                # Instantiate statelessly for execution
                engine_instance = engine_cls()
                
                # The execution logic (including filtering assessments, deciding COMPLETE/PARTIAL/INCONCLUSIVE, 
                # and determining RiskLevel) is entirely encapsulated within the risk engine itself.
                result = engine_instance.execute(assessments)
                
                # Ensure execution time is tracked safely if the engine didn't inject it properly,
                # by reconstructing the frozen model.
                final_result = DomainRiskProfile(
                    profile_id=result.profile_id,
                    risk_engine_key=result.risk_engine_key,
                    risk_engine_name=result.risk_engine_name,
                    risk_engine_version=result.risk_engine_version,
                    status=result.status,
                    risk_level=result.risk_level,
                    summary=result.summary,
                    findings=result.findings,
                    supporting_assessments=result.supporting_assessments,
                    metadata=result.metadata,
                    execution_time=time.perf_counter() - start_time
                )
                results.append(final_result)
                
            except Exception as e:
                # A failed engine must not stop execution of the remaining engines.
                end_time = time.perf_counter()
                results.append(DomainRiskProfile(
                    risk_engine_key=engine_cls.key(),
                    risk_engine_name=engine_cls.name(),
                    risk_engine_version=engine_cls.version(),
                    status=DomainRiskStatus.ERROR,
                    risk_level=RiskLevel.UNKNOWN,
                    summary=f"Unhandled exception during domain risk execution: {str(e)}",
                    findings=[],
                    supporting_assessments=[],
                    metadata={"traceback": traceback.format_exc()},
                    execution_time=end_time - start_time
                ))
                
        return results
