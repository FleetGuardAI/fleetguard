"""
FleetGuard — Rule Executor
Executes validation rules with support for future telemetry, timeouts, and parallelization.
"""

import asyncio
import logging
from typing import List

from infrastructure.validation.rule import BaseValidationRule
from schemas.validation_sdk import ValidationContext, RuleResult, RuleSeverity, RuleCategory

logger = logging.getLogger("fleetguard.infrastructure.validation.executor")


class RuleExecutor:
    """
    Responsible for safely executing a single rule or a batch of rules.
    Provides isolation, error handling, and future tracing/metrics hooks.
    """
    
    async def execute_rule(self, rule: BaseValidationRule, context: ValidationContext) -> RuleResult:
        """
        Executes a single validation rule safely.
        If the rule raises an unhandled exception, it is caught here and converted
        into a RuleResult with WARNING severity (which flags the event as DISPUTED),
        preventing a single bad rule from completely rejecting the event or crashing the engine.
        """
        logger.debug(f"Executing rule '{rule.name}' (Category: {rule.category}, Priority: {rule.priority})")
        try:
            # Future: add timeout support using asyncio.wait_for
            # Future: emit execution metrics (start time, end time)
            return await rule.evaluate(context)
        except Exception as e:
            logger.exception(f"Rule '{rule.name}' failed with an unhandled exception: {e}")
            return RuleResult(
                rule_name=rule.name,
                passed=False,
                severity=RuleSeverity.WARNING,
                message=f"Rule crashed during execution: {e}",
                recommendation="Investigate rule implementation and input data."
            )

    async def execute_all(self, rules: List[BaseValidationRule], context: ValidationContext) -> List[RuleResult]:
        """
        Executes all rules. Currently executes sequentially based on priority,
        but can be refactored to execute rules with the same priority concurrently.
        """
        results = []
        for rule in rules:
            try:
                if rule.applies_to(context):
                    result = await self.execute_rule(rule, context)
                    results.append(result)
            except Exception as e:
                logger.error(f"Failed to evaluate applicability for rule '{rule.name}': {e}")
                
        return results
