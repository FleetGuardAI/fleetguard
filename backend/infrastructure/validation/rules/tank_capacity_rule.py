"""
FleetGuard — Tank Capacity Validation Rule (FI-002)
Ensures a claimed fuel fill quantity can physically fit inside the vehicle's tank.
"""

from models.operational_event import EventType
from infrastructure.validation.rule import BaseValidationRule
from schemas.validation_sdk import ValidationContext, RuleResult, RuleSeverity, RuleCategory, RuleStatus
from schemas.fuel_domain import CurrentFuelState


class TankCapacityRule(BaseValidationRule):
    """
    Validates that a claimed fuel fill does not exceed the physical capacity
    of the vehicle's fuel tank, factoring in the current fuel level.
    """

    @property
    def name(self) -> str:
        return "tank_capacity_rule"

    @property
    def category(self) -> RuleCategory:
        return RuleCategory.BUSINESS_LOGIC

    @property
    def priority(self) -> int:
        # Runs after structural (100) and leaves room for compliance checks
        return 500

    def applies_to(self, context: ValidationContext) -> bool:
        """Runs only for FUEL_FILLED events."""
        return context.event.event_type == EventType.FUEL_FILLED

    async def evaluate(self, context: ValidationContext) -> RuleResult:
        """
        Check that the current fuel + claimed fuel <= tank capacity.
        """
        # 1. Extract required inputs
        payload = context.event.payload or {}
        claimed_fuel_quantity = payload.get("liters")
        
        fuel_state: CurrentFuelState = context.business_state.get("current_fuel_state")

        # 2. Handle missing dependencies (SKIPPED)
        if claimed_fuel_quantity is None:
            return RuleResult(
                rule_name=self.name,
                status=RuleStatus.SKIPPED,
                severity=RuleSeverity.INFO,
                message="Skipped: Claimed fuel quantity (liters) is missing from the event payload."
            )

        if not fuel_state:
            return RuleResult(
                rule_name=self.name,
                status=RuleStatus.SKIPPED,
                severity=RuleSeverity.INFO,
                message="Skipped: CurrentFuelState is missing from the business context."
            )

        # Handle potential type mismatches (if structural validation didn't catch it)
        try:
            claimed_fuel_quantity = float(claimed_fuel_quantity)
        except (ValueError, TypeError):
            return RuleResult(
                rule_name=self.name,
                status=RuleStatus.ERROR,
                severity=RuleSeverity.CRITICAL,
                message="Error: Claimed fuel quantity is not a valid number."
            )

        # 3. Calculate validation logic
        fuel_after_fill = fuel_state.current_fuel_liters + claimed_fuel_quantity
        
        metadata = {
            "capacity_liters": fuel_state.capacity_liters,
            "fuel_before_fill": fuel_state.current_fuel_liters,
            "claimed_fill": claimed_fuel_quantity,
            "fuel_after_fill": fuel_after_fill
        }

        # 4. Determine Decision
        if fuel_after_fill <= fuel_state.capacity_liters:
            return RuleResult(
                rule_name=self.name,
                status=RuleStatus.PASS,
                severity=RuleSeverity.INFO,
                message="Claimed fuel quantity fits within the tank capacity.",
                metadata=metadata
            )
        else:
            overflow = fuel_after_fill - fuel_state.capacity_liters
            metadata["overflow_liters"] = overflow
            return RuleResult(
                rule_name=self.name,
                status=RuleStatus.FAIL,
                severity=RuleSeverity.CRITICAL,
                message=f"Claimed fuel exceeds tank capacity by {overflow} liters.",
                metadata=metadata
            )
