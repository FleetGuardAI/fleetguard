"""
FleetGuard — Validation Rule Registry
"""

import logging
from typing import List, Optional

from infrastructure.validation.rule import BaseValidationRule

logger = logging.getLogger("fleetguard.infrastructure.validation.registry")


class ValidationRuleRegistry:
    """
    Maintains a list of registered Validation Rules.
    Acts purely as a catalog. Contains no orchestration or execution logic.
    """
    def __init__(self) -> None:
        self._rules: List[BaseValidationRule] = []
        self._rule_map: dict[str, BaseValidationRule] = {}

    def register(self, rule: BaseValidationRule) -> None:
        """
        Register a new Validation Rule.
        """
        if rule.name in self._rule_map:
            raise ValueError(f"Validation Rule '{rule.name}' is already registered.")
        
        self._rules.append(rule)
        self._rule_map[rule.name] = rule
        # Keep the list sorted by priority so list() always returns them in order
        self._rules.sort(key=lambda r: r.priority)
        
        logger.info(f"Registered Validation Rule: {rule.name} (Priority: {rule.priority})")

    def get(self, name: str) -> Optional[BaseValidationRule]:
        """
        Retrieve a rule by name.
        """
        return self._rule_map.get(name)

    def list(self) -> List[BaseValidationRule]:
        """
        List all registered rules, sorted by priority.
        """
        return list(self._rules)
