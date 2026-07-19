"""
FleetGuard — Example Fuel Structural Validation Rule

This is a REFERENCE IMPLEMENTATION to demonstrate how to build new rules using the Validation SDK.
It is NOT enabled by default.
"""

from models.operational_event import EventType
from infrastructure.validation.rule import BaseValidationRule
from schemas.validation_sdk import ValidationContext, RuleResult, RuleSeverity, RuleCategory, RuleStatus


class ExampleFuelStructuralRule(BaseValidationRule):
    """
    Validates the structural integrity of FUEL_FILLED event payloads.
    Demonstrates usage of the generic Validation SDK.
    """

    @property
    def name(self) -> str:
        return "example_fuel_structural_rule"

    @property
    def category(self) -> RuleCategory:
        return RuleCategory.STRUCTURAL

    @property
    def priority(self) -> int:
        return 100  # High priority (run early)

    def applies_to(self, context: ValidationContext) -> bool:
        """Runs only for FUEL_FILLED events."""
        return context.event.event_type == EventType.FUEL_FILLED

    async def evaluate(self, context: ValidationContext) -> RuleResult:
        """
        Check that required payload fields exist and are of correct types/ranges.
        """
        payload = context.event.payload

        if not payload:
            return RuleResult(
                rule_name=self.name, 
                status=RuleStatus.FAIL, 
                severity=RuleSeverity.CRITICAL,
                message="Payload is entirely missing."
            )

        if not isinstance(payload, dict):
            return RuleResult(
                rule_name=self.name, 
                status=RuleStatus.FAIL, 
                severity=RuleSeverity.CRITICAL,
                message="Payload must be a JSON object."
            )

        reasons = []

        # --- Check liters ---
        liters = payload.get("liters")
        if liters is None:
            reasons.append("Missing required field: 'liters'.")
        elif not isinstance(liters, (int, float)):
            reasons.append("'liters' must be a number.")
        elif liters <= 0:
            reasons.append("'liters' must be greater than 0.")

        # --- Check amount ---
        amount = payload.get("amount")
        if amount is None:
            reasons.append("Missing required field: 'amount'.")
        elif not isinstance(amount, (int, float)):
            reasons.append("'amount' must be a number.")
        elif amount <= 0:
            reasons.append("'amount' must be greater than 0.")

        # --- Check odometer (optional) ---
        odometer = payload.get("odometer")
        if odometer is not None:
            if not isinstance(odometer, int):
                reasons.append("'odometer' must be an integer.")
            elif odometer < 0:
                reasons.append("'odometer' cannot be negative.")

        if reasons:
            return RuleResult(
                rule_name=self.name, 
                status=RuleStatus.FAIL, 
                severity=RuleSeverity.CRITICAL,
                message=" | ".join(reasons),
                recommendation="Ensure the event publisher adheres to the Fuel event schema."
            )

        return RuleResult(
            rule_name=self.name, 
            status=RuleStatus.PASS,
            severity=RuleSeverity.INFO,
            message="Payload structure is valid."
        )
