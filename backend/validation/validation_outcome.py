"""
FleetGuard — Validation Outcome Enum

Defines the possible outcomes of a single validator's assessment.

Design notes
------------
• VERIFIED              — validator is satisfied; event data is trustworthy.
• NEEDS_MANUAL_REVIEW   — validator cannot decide automatically; a human must
                          review (maps to VerificationStatus.DISPUTED).
• REJECTED              — validator determined the event is invalid/fraudulent.
• PENDING_MORE_DATA     — validator needs additional data not yet available
                          (e.g. GPS fix pending, receipt upload in progress).

These outcomes are intentionally decoupled from ``VerificationStatus``.
The ``ValidationEngine`` is responsible for aggregating multiple
``ValidationOutcome`` values into a single final ``VerificationStatus``.
"""

from __future__ import annotations

import enum


class ValidationOutcome(str, enum.Enum):
    """
    Outcome of a single validator's assessment of an Operational Event.

    Multiple validators may run for the same event.  The
    ``ValidationEngine`` aggregates their outcomes into a final
    ``VerificationStatus`` that is written back to the event store.

    Values
    ------
    VERIFIED
        The validator's checks all passed.  Data is consistent and
        trustworthy from this validator's perspective.
    NEEDS_MANUAL_REVIEW
        The validator could not make a confident decision.  A fleet
        manager must inspect the event before it can be advanced.
        Corresponds to ``VerificationStatus.DISPUTED``.
    REJECTED
        The validator found the event to be invalid, inconsistent, or
        potentially fraudulent.  Corresponds to ``VerificationStatus.REJECTED``.
    PENDING_MORE_DATA
        Supporting data required by this validator is not yet available.
        The event should remain in ``PENDING`` state and be re-validated
        when the data arrives.
    """

    VERIFIED = "VERIFIED"
    NEEDS_MANUAL_REVIEW = "NEEDS_MANUAL_REVIEW"
    REJECTED = "REJECTED"
    PENDING_MORE_DATA = "PENDING_MORE_DATA"
