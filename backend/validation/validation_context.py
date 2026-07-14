"""
FleetGuard — Validation Context

Carries all information a validator may need during a validation run.

Design principles
-----------------
• A ``ValidationContext`` is constructed **once per event** by the
  ``ValidationEngine`` and passed unchanged to every registered validator.
• Validators must treat it as **read-only**.  They must NOT mutate the event
  or the context.  All output is expressed through ``ValidationResult``.
• The context intentionally carries only what validators need.  It does not
  expose the database session or the repository — validators must not perform
  their own database queries.  If a validator needs additional data, it should
  be fetched by the ``ValidationEngine`` and placed on the context before
  validators run.

Fields
------
event : OperationalEventResponse
    The fully validated Pydantic response of the event being validated.
    Read-only.
raw_payload : dict[str, Any] | None
    Convenience alias of ``event.payload``.  Validators access this frequently
    so it is exposed directly to avoid repeated attribute navigation.
capture_method : CaptureMethod
    The channel through which the event was captured.  Validators use this
    to apply different trust levels (e.g. TELEMATICS events require less
    manual verification than WHATSAPP_BOT events).
extra : dict[str, Any]
    Arbitrary additional context the engine populates before running
    validators.  Examples:
      • Historical fuel average for this vehicle
      • Latest GPS coordinates for the entity
      • Fleet-wide median price per litre
    Validators read from ``extra`` but never write to it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from schemas.operational_event import OperationalEventResponse
    from models.operational_event import CaptureMethod


@dataclass(frozen=True)
class ValidationContext:
    """
    Immutable bundle of information passed to every validator.

    Constructed once per event by ``ValidationEngine`` and shared across
    all validators registered for that event's type.

    Parameters
    ----------
    event : OperationalEventResponse
        The event being validated.  Read-only.
    extra : dict[str, Any]
        Optional additional data fetched by the engine before validation
        begins.  Validators read from this; they never write to it.

    Derived properties
    ------------------
    raw_payload     — ``event.payload`` shortcut.
    capture_method  — ``event.capture_method`` shortcut.
    """

    event: "OperationalEventResponse"
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def raw_payload(self) -> dict[str, Any] | None:
        """Shortcut to the event's schemaless payload dict."""
        return self.event.payload

    @property
    def capture_method(self) -> "CaptureMethod":
        """Shortcut to the event's capture method."""
        return self.event.capture_method

    def __repr__(self) -> str:
        return (
            f"<ValidationContext event_id={self.event.id} "
            f"event_type={self.event.event_type.value} "
            f"extra_keys={list(self.extra.keys())}>"
        )
