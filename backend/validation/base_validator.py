"""
FleetGuard — Base Validator Interface

Every concrete validator must subclass ``BaseValidator`` and implement
``applies_to()`` and ``validate()``.

Design principles
-----------------
• A validator is a **single-responsibility component**.  It assesses one
  dimension of an event's trustworthiness (e.g. fuel quantity plausibility,
  GPS location consistency, OCR receipt match).
• Validators are **stateless**.  They must not store any state between calls.
  All input comes through ``ValidationContext``; all output is expressed
  through ``ValidationResult``.
• ``applies_to()`` lets each validator declare its own applicability rather
  than requiring the engine to maintain a mapping.  This keeps validators
  fully self-contained.
• All validators are async to support I/O-bound lookups (e.g. historical
  price fetch) without blocking the event loop.

Registration
------------
Validators are registered with the ``ValidationEngine`` at startup.
The engine calls ``applies_to(context)`` for every registered validator
before calling ``validate(context)``.  Validators that return ``False``
from ``applies_to`` are skipped silently.

Example
-------
::

    class FuelQuantityValidator(BaseValidator):
        name = "fuel_quantity_validator"

        async def applies_to(self, context: ValidationContext) -> bool:
            return context.event.event_type == EventType.FUEL_FILLED

        async def validate(self, context: ValidationContext) -> ValidationResult:
            payload = context.raw_payload or {}
            litres = payload.get("liters", 0)
            if litres > 200:
                return ValidationResult.rejected(["Claimed litres exceed maximum tank capacity."])
            return ValidationResult.verified()
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from validation.validation_context import ValidationContext
    from validation.validation_result import ValidationResult


class BaseValidator(ABC):
    """
    Abstract base class for all FleetGuard event validators.

    Subclass this and implement ``applies_to`` and ``validate`` to create
    a new validator.  Register it with ``ValidationEngine`` at startup.

    Attributes
    ----------
    name : str
        Unique identifier for this validator.  Used in log output and in
        the ``validator_name`` field of every ``ValidationResult`` it produces.
        Must be unique across all registered validators.

    Methods to implement
    --------------------
    applies_to(context) -> bool
        Return ``True`` if this validator should run for the given context.
        The engine calls this before ``validate``.  Returning ``False`` means
        the validator is silently skipped for this event.
    validate(context) -> ValidationResult
        Perform the validation.  Return a ``ValidationResult`` describing
        the outcome.  Do NOT raise exceptions for expected validation
        failures — express them as ``REJECTED`` or ``NEEDS_MANUAL_REVIEW``
        results.

    Lifecycle guarantees
    --------------------
    • ``applies_to`` is always called before ``validate``.
    • ``validate`` is only called if ``applies_to`` returned ``True``.
    • The engine sets ``result.validator_name = self.name`` automatically.
      Do not set it manually inside ``validate``.
    """

    #: Unique name for this validator.  Override in subclasses.
    name: str = "unnamed_validator"

    @abstractmethod
    async def applies_to(self, context: "ValidationContext") -> bool:
        """
        Declare whether this validator should run for the given context.

        Return ``True`` to run ``validate``; ``False`` to skip silently.

        Parameters
        ----------
        context : ValidationContext
            The immutable validation context for the current event.

        Returns
        -------
        bool
            ``True`` if this validator is applicable; ``False`` to skip.
        """
        ...  # pragma: no cover

    @abstractmethod
    async def validate(self, context: "ValidationContext") -> "ValidationResult":
        """
        Assess the event and return a validation verdict.

        Parameters
        ----------
        context : ValidationContext
            The immutable validation context.  Read-only.

        Returns
        -------
        ValidationResult
            The validator's verdict.  Use the factory classmethods
            (``ValidationResult.verified()``, ``.rejected()``, etc.)
            rather than constructing manually.

        Notes
        -----
        Do NOT raise exceptions for expected validation failures.
        Express them as REJECTED or NEEDS_MANUAL_REVIEW results.

        Unexpected infrastructure errors (network timeout, DB error) may
        raise — they will be caught and logged by the engine, and the
        event will remain in PENDING state.
        """
        ...  # pragma: no cover
