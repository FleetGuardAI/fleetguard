"""
FleetGuard — Base Validation Rule Interface
"""

from abc import ABC, abstractmethod

from schemas.validation_sdk import ValidationContext, RuleResult, RuleCategory


class BaseValidationRule(ABC):
    """
    Abstract Base Class for a Validation Rule.
    A Validation Rule evaluates a specific aspect of the ValidationContext
    and produces a RuleResult.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """A unique string identifier for this rule."""
        pass

    @property
    @abstractmethod
    def category(self) -> RuleCategory:
        """The category of this rule."""
        pass

    @property
    @abstractmethod
    def priority(self) -> int:
        """
        Execution priority (lower number = higher priority).
        Used by the engine to order execution.
        """
        pass

    @abstractmethod
    def applies_to(self, context: ValidationContext) -> bool:
        """
        Determine if this rule is applicable to the given context.
        """
        pass

    @abstractmethod
    async def evaluate(self, context: ValidationContext) -> RuleResult:
        """
        Execute the validation rule logic.
        
        Args:
            context: The rich ValidationContext without any database dependencies.
            
        Returns:
            A RuleResult indicating pass/fail, severity, and associated message.
        """
        pass
