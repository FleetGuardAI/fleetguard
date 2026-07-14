"""
FleetGuard — Validation Package

The Validation & Enrichment Engine (VEE) framework.

Public surface
--------------
ValidationEngine    — orchestrates validators; implements EventSubscriber
BaseValidator       — ABC every concrete validator must implement
ValidationContext   — immutable bundle of event data passed to validators
ValidationResult    — the structured output of a single validator run
ValidationOutcome   — enum of possible single-validator verdicts

Usage
-----
Register validators at startup::

    from validation import ValidationEngine, BaseValidator, ValidationOutcome
    from validation import ValidationContext, ValidationResult

    class MyValidator(BaseValidator):
        name = "my_validator"

        async def applies_to(self, context: ValidationContext) -> bool:
            return True  # applies to all events

        async def validate(self, context: ValidationContext) -> ValidationResult:
            return ValidationResult.verified()

    engine = ValidationEngine(service=event_service)
    engine.register_validator(MyValidator())
    event_dispatcher.register_subscriber(engine)
"""

from validation.validation_outcome import ValidationOutcome
from validation.validation_result import ValidationResult
from validation.validation_context import ValidationContext
from validation.base_validator import BaseValidator
from validation.validation_engine import ValidationEngine

__all__ = [
    "ValidationEngine",
    "BaseValidator",
    "ValidationContext",
    "ValidationResult",
    "ValidationOutcome",
]
