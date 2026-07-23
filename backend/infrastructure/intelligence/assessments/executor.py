"""
Fleet Intelligence Engine - Assessment Executor
"""

import time
import traceback
from typing import List
from infrastructure.intelligence.checks.models import CheckResult
from infrastructure.intelligence.assessments.registry import AssessmentRegistry
from infrastructure.intelligence.assessments.models import AssessmentResult, AssessmentStatus


class AssessmentExecutor:
    """
    Executes registered assessments against a collection of CheckResults.
    
    Responsibilities:
    - Iterates over all registered assessments deterministically.
    - Captures unexpected faults to isolate assessment failures.
    - Collects AssessmentResults.
    - Does NOT decide whether an assessment is COMPLETE, PARTIAL, or INCONCLUSIVE.
    """
    
    def __init__(self, registry: AssessmentRegistry):
        self._registry = registry

    def execute_all(self, checks: List[CheckResult]) -> List[AssessmentResult]:
        """
        Executes all registered assessments deterministically against the provided CheckResults.
        """
        results = []
        assessments = self._registry.enumerate_assessments()
        
        for assessment_cls in assessments:
            start_time = time.perf_counter()
            try:
                # Instantiate statelessly for execution
                assessment_instance = assessment_cls()
                
                # The execution logic (including deciding COMPLETE/PARTIAL/INCONCLUSIVE)
                # is entirely encapsulated within the assessment itself.
                result = assessment_instance.execute(checks)
                
                # Ensure execution time is tracked safely if the assessment didn't inject it properly,
                # by reconstructing the frozen model.
                final_result = AssessmentResult(
                    assessment_id=result.assessment_id,
                    assessment_key=result.assessment_key,
                    assessment_name=result.assessment_name,
                    assessment_version=result.assessment_version,
                    status=result.status,
                    summary=result.summary,
                    findings=result.findings,
                    contributing_checks=result.contributing_checks,
                    metadata=result.metadata,
                    execution_time=time.perf_counter() - start_time
                )
                results.append(final_result)
                
            except Exception as e:
                # A failed assessment must not stop execution of the remaining assessments.
                end_time = time.perf_counter()
                results.append(AssessmentResult(
                    assessment_key=assessment_cls.key(),
                    assessment_name=assessment_cls.name(),
                    assessment_version=assessment_cls.version(),
                    status=AssessmentStatus.ERROR,
                    summary=f"Unhandled exception during assessment execution: {str(e)}",
                    findings=[],
                    contributing_checks=[],
                    metadata={"traceback": traceback.format_exc()},
                    execution_time=end_time - start_time
                ))
                
        return results
