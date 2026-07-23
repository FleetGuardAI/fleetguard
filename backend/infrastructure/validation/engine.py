"""
FleetGuard — Validation Engine
"""

import logging
from typing import List

from infrastructure.validation.registry import ValidationRuleRegistry
from infrastructure.validation.executor import RuleExecutor
from schemas.validation_sdk import ValidationContext, RuleResult, RuleSeverity, RuleStatus
from schemas.validation_result import ValidationResult, ValidationVerdict

logger = logging.getLogger("fleetguard.infrastructure.validation.engine")


class ValidationEngine:
    """
    Evaluates an Evidence Package against applicable Validation Rules.
    Returns a deterministic ValidationResult without mutating any state.
    """
    def __init__(self, registry: ValidationRuleRegistry, executor: RuleExecutor = None) -> None:
        self.registry = registry
        self.executor = executor or RuleExecutor()

    async def evaluate(self, context: ValidationContext) -> ValidationResult:
        """
        Run applicable rules and compute the final ValidationResult.
        """
        rules = self.registry.list()
        
        # Execute all applicable rules via the executor
        results = await self.executor.execute_all(rules, context)
        
        passed_rules: List[str] = []
        failed_rules: List[RuleResult] = []
        warnings: List[RuleResult] = []
        scores: List[float] = []
        
        verdict = ValidationVerdict.VERIFIED

        if not results:
            logger.info(f"No validation rules applicable for Event {context.event.id}.")
        
        for result in results:
            if result.status == RuleStatus.PASS:
                passed_rules.append(result.rule_name)
            elif result.status == RuleStatus.SKIPPED:
                logger.info(f"Rule {result.rule_name} was skipped: {result.message}")
            elif result.status == RuleStatus.FAIL or result.status == RuleStatus.ERROR:
                if result.severity == RuleSeverity.CRITICAL:
                    failed_rules.append(result)
                    verdict = ValidationVerdict.REJECTED
                elif result.severity == RuleSeverity.WARNING:
                    warnings.append(result)
                    if verdict != ValidationVerdict.REJECTED:
                        verdict = ValidationVerdict.DISPUTED
                elif result.severity == RuleSeverity.INFO:
                    warnings.append(result)

            # Extract optional score from metadata if present
            score = result.metadata.get("score")
            if score is not None and isinstance(score, (int, float)):
                scores.append(float(score))

        # Calculate optional aggregate score
        final_score = None
        if scores:
            final_score = sum(scores) / len(scores)

        return ValidationResult(
            verdict=verdict,
            validation_score=final_score,
            passed_rules=passed_rules,
            failed_rules=failed_rules,
            warnings=warnings,
            metadata={"evaluated_rules_count": len(results)}
        )
