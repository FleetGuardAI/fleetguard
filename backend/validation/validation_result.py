"""
FleetGuard — Validation Result

Represents the complete output of a single validator's assessment.

A ``ValidationResult`` is produced by every ``BaseValidator.validate()`` call
and collected by the ``ValidationEngine`` for aggregation.

Design notes
------------
• ``reasons``          — human-readable explanation of the outcome.
• ``evidence``         — structured data the validator used to reach its
                         conclusion (e.g. price per litre, GPS delta km).
                         Stored so auditors can understand decisions.
• ``warnings``         — non-blocking observations that do not change the
                         outcome but should be surfaced to fleet managers.
• ``enrichment_data``  — additional structured data the validator wants to
                         attach to the event's ``event_metadata`` field.
                         The engine merges this into the event after all
                         validators have run.
• ``validator_name``   — automatically set by ``BaseValidator``; identifies
                         which validator produced this result.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from validation.validation_outcome import ValidationOutcome


@dataclass
class ValidationResult:
    """
    Output of a single validator's assessment of one Operational Event.

    Produced by ``BaseValidator.validate()`` and consumed by
    ``ValidationEngine`` for aggregation.

    Attributes
    ----------
    outcome : ValidationOutcome
        The validator's verdict on this event.
    validator_name : str
        Name of the validator that produced this result.  Set automatically
        by ``BaseValidator`` — do not set manually in ``validate()``.
    reasons : list[str]
        Human-readable explanations for the outcome.  Required for
        REJECTED and NEEDS_MANUAL_REVIEW outcomes so fleet managers
        understand why the event was flagged.
    evidence : dict[str, Any]
        Structured data used to reach the conclusion.  Stored for audit
        trail.  Example: ``{"claimed_litres": 80, "tank_capacity_litres": 60}``.
    warnings : list[str]
        Non-blocking observations.  Do not change outcome but should be
        surfaced to fleet managers in the UI.
    enrichment_data : dict[str, Any]
        Additional data to merge into the event's ``event_metadata`` field.
        Validators use this to annotate events with derived context
        (e.g. calculated price per litre, resolved GPS location name).
    """

    outcome: ValidationOutcome
    validator_name: str = ""
    reasons: list[str] = field(default_factory=list)
    evidence: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    enrichment_data: dict[str, Any] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Factory helpers
    # ------------------------------------------------------------------

    @classmethod
    def verified(
        cls,
        *,
        reasons: list[str] | None = None,
        evidence: dict[str, Any] | None = None,
        warnings: list[str] | None = None,
        enrichment_data: dict[str, Any] | None = None,
    ) -> "ValidationResult":
        """Return a VERIFIED result."""
        return cls(
            outcome=ValidationOutcome.VERIFIED,
            reasons=reasons or [],
            evidence=evidence or {},
            warnings=warnings or [],
            enrichment_data=enrichment_data or {},
        )

    @classmethod
    def rejected(
        cls,
        reasons: list[str],
        *,
        evidence: dict[str, Any] | None = None,
        warnings: list[str] | None = None,
        enrichment_data: dict[str, Any] | None = None,
    ) -> "ValidationResult":
        """Return a REJECTED result.  At least one reason is required."""
        return cls(
            outcome=ValidationOutcome.REJECTED,
            reasons=reasons,
            evidence=evidence or {},
            warnings=warnings or [],
            enrichment_data=enrichment_data or {},
        )

    @classmethod
    def needs_review(
        cls,
        reasons: list[str],
        *,
        evidence: dict[str, Any] | None = None,
        warnings: list[str] | None = None,
        enrichment_data: dict[str, Any] | None = None,
    ) -> "ValidationResult":
        """Return a NEEDS_MANUAL_REVIEW result.  At least one reason is required."""
        return cls(
            outcome=ValidationOutcome.NEEDS_MANUAL_REVIEW,
            reasons=reasons,
            evidence=evidence or {},
            warnings=warnings or [],
            enrichment_data=enrichment_data or {},
        )

    @classmethod
    def pending_more_data(
        cls,
        reasons: list[str],
        *,
        evidence: dict[str, Any] | None = None,
        enrichment_data: dict[str, Any] | None = None,
    ) -> "ValidationResult":
        """Return a PENDING_MORE_DATA result."""
        return cls(
            outcome=ValidationOutcome.PENDING_MORE_DATA,
            reasons=reasons,
            evidence=evidence or {},
            enrichment_data=enrichment_data or {},
        )

    def __repr__(self) -> str:
        return (
            f"<ValidationResult outcome={self.outcome.value} "
            f"validator={self.validator_name!r} "
            f"reasons={self.reasons}>"
        )
