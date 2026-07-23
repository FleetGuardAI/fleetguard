"""
Fleet Intelligence Engine - Intelligence Orchestrator
"""

import time
import traceback
from typing import List

from infrastructure.intelligence.evidence.package import EvidencePackage
from infrastructure.intelligence.checks.executor import CheckExecutor
from infrastructure.intelligence.assessments.executor import AssessmentExecutor
from infrastructure.intelligence.domain_risk.executor import DomainRiskExecutor
from infrastructure.intelligence.global_decision.executor import DecisionExecutor

from infrastructure.intelligence.orchestrator.models import (
    IntelligenceExecutionResult,
    IntelligenceExecutionStatus,
    ExecutionTrace
)


class IntelligenceOrchestrator:
    """
    Single entry point for the Fleet Intelligence Engine pipeline.
    
    Coordinates the execution of Checks -> Assessments -> Domain Risk -> Global Decision.
    It contains absolutely no business logic or domain policies.
    """
    
    def __init__(
        self,
        check_executor: CheckExecutor,
        assessment_executor: AssessmentExecutor,
        risk_executor: DomainRiskExecutor,
        decision_executor: DecisionExecutor
    ):
        self.check_executor = check_executor
        self.assessment_executor = assessment_executor
        self.risk_executor = risk_executor
        self.decision_executor = decision_executor

    def execute(self, package: EvidencePackage) -> IntelligenceExecutionResult:
        """
        Executes the entire intelligence pipeline synchronously.
        """
        start_time = time.perf_counter()
        
        try:
            # 1. Evaluate Facts
            checks = self.check_executor.execute_all(package)
            
            # 2. Form Structural Findings
            assessments = self.assessment_executor.execute_all(checks)
            
            # 3. Calculate Domain Risk
            risks = self.risk_executor.execute_all(assessments)
            
            # 4. Form Final Recommendation
            decisions = self.decision_executor.execute_all(risks)
            
            trace = ExecutionTrace(
                evidence_package=package,
                check_results=checks,
                assessment_results=assessments,
                domain_risk_profiles=risks
            )
            
            return IntelligenceExecutionResult(
                status=IntelligenceExecutionStatus.COMPLETE,
                recommendations=decisions,
                trace=trace,
                execution_time=time.perf_counter() - start_time
            )
            
        except Exception as e:
            # Safely catch any unhandled framework exceptions that leaked through the 
            # individual executor safety nets (e.g. out of memory, fundamental misconfiguration).
            return IntelligenceExecutionResult(
                status=IntelligenceExecutionStatus.ERROR,
                recommendations=[],
                trace=ExecutionTrace(evidence_package=package),
                metadata={
                    "error": str(e),
                    "traceback": traceback.format_exc()
                },
                execution_time=time.perf_counter() - start_time
            )
