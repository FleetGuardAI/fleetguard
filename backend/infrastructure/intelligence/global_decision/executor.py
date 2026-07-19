"""
Fleet Intelligence Engine - Global Decision Executor
"""

import time
import traceback
from typing import List
from infrastructure.intelligence.domain_risk.models import DomainRiskProfile
from infrastructure.intelligence.global_decision.registry import DecisionRegistry
from infrastructure.intelligence.global_decision.models import Recommendation, DecisionStatus


class DecisionExecutor:
    """
    Executes registered global decision engines against a collection of DomainRiskProfiles.
    
    Responsibilities:
    - Iterates over all registered decision engines deterministically.
    - Passes the *complete* list of DomainRiskProfiles to each engine.
    - Captures unexpected faults to isolate engine failures.
    - Collects Recommendations.
    - Does NOT decide whether an engine's status is COMPLETE, PARTIAL, or INCONCLUSIVE, 
      nor does it determine the RecommendationStatus (unless an unhandled error occurs, 
      in which case it returns None for the recommendation).
    """
    
    def __init__(self, registry: DecisionRegistry):
        self._registry = registry

    def execute_all(self, profiles: List[DomainRiskProfile]) -> List[Recommendation]:
        """
        Executes all registered decision engines deterministically against the provided DomainRiskProfiles.
        """
        results = []
        engines = self._registry.enumerate_engines()
        
        for engine_cls in engines:
            start_time = time.perf_counter()
            try:
                # Instantiate statelessly for execution
                engine_instance = engine_cls()
                
                # The execution logic (including filtering profiles, deciding COMPLETE/PARTIAL/INCONCLUSIVE, 
                # and determining the final recommendation) is entirely encapsulated within the engine itself.
                result = engine_instance.execute(profiles)
                
                # Ensure execution time is tracked safely if the engine didn't inject it properly,
                # by reconstructing the frozen model.
                final_result = Recommendation(
                    recommendation_id=result.recommendation_id,
                    decision_engine_key=result.decision_engine_key,
                    decision_engine_name=result.decision_engine_name,
                    decision_engine_version=result.decision_engine_version,
                    status=result.status,
                    recommendation=result.recommendation,
                    summary=result.summary,
                    findings=result.findings,
                    supporting_profiles=result.supporting_profiles,
                    metadata=result.metadata,
                    execution_time=time.perf_counter() - start_time
                )
                results.append(final_result)
                
            except Exception as e:
                # A failed engine must not stop execution of the remaining engines.
                end_time = time.perf_counter()
                results.append(Recommendation(
                    decision_engine_key=engine_cls.key(),
                    decision_engine_name=engine_cls.name(),
                    decision_engine_version=engine_cls.version(),
                    status=DecisionStatus.ERROR,
                    recommendation=None,
                    summary=f"Unhandled exception during decision execution: {str(e)}",
                    findings=[],
                    supporting_profiles=[],
                    metadata={"traceback": traceback.format_exc()},
                    execution_time=end_time - start_time
                ))
                
        return results
