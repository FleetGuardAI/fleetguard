"""
FleetGuard — Fuel Structural Validator

Performs purely structural validation on fuel-related Operational Events.

It verifies that the payload contains all required fields, that the data types
are correct, and that numeric values fall within reasonable physical bounds.

It does NOT verify whether the fuel transaction actually occurred. That is
the responsibility of future Evidence Providers (e.g., GPS cross-reference,
receipt OCR, telemetry matching).

Fields expected in payload:
- liters (float/int) > 0
- amount (float/int) > 0
- odometer (int) >= 0 (optional, but if present must be >= 0)
- currency (str) (optional, defaults to INR)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from models.operational_event import EventType
from validation.base_validator import BaseValidator
from validation.validation_result import ValidationResult

if TYPE_CHECKING:
    from validation.validation_context import ValidationContext


class FuelStructuralValidator(BaseValidator):
    """
    Validates the structural integrity of FUEL_FILLED event payloads.
    """

    name = "fuel_structural_validator"

    async def applies_to(self, context: "ValidationContext") -> bool:
        """Runs only for FUEL_FILLED events."""
        return context.event.event_type == EventType.FUEL_FILLED

    async def validate(self, context: "ValidationContext") -> "ValidationResult":
        """
        Check that required payload fields exist and are of correct types/ranges.
        """
        payload = context.raw_payload

        if not payload:
            return ValidationResult.rejected(["Payload is entirely missing."])

        if not isinstance(payload, dict):
            return ValidationResult.rejected(["Payload must be a JSON object."])

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
            return ValidationResult.rejected(reasons=reasons)

        return ValidationResult.verified()
