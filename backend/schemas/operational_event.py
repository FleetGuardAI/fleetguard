"""
FleetGuard — Operational Event Pydantic Schemas

Request / response models for the Operational Event domain.

These schemas are used by:
  • Event Service           (write path — OperationalEventCreate)
  • Event Processor         (read path — OperationalEventResponse)
  • Validation & Enrichment Engine  (patch path — OperationalEventUpdate)
  • Fleet Intelligence Engine       (read path — OperationalEventResponse)

Schema summary
--------------
OperationalEventCreate   → POST body when a module submits a new event.
OperationalEventUpdate   → PATCH body for mutable fields only
                           (verification_status, notes).
OperationalEventResponse → Full read representation returned by the API
                           and consumed by downstream engines.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from models.operational_event import (
    CaptureMethod,
    EntityType,
    EventType,
    VerificationStatus,
)


# ===========================================================================
# Write Schemas
# ===========================================================================

class OperationalEventCreate(BaseModel):
    """
    Schema for submitting a new Operational Event.

    Used by every module that produces events — WhatsApp bot, telematics
    gateway, manual entry forms, third-party integrations.

    The ``payload`` field is intentionally schemaless at this layer.
    Each event_type has a documented payload contract in the Event Catalogue;
    enforcement is the responsibility of the Validation & Enrichment Engine.
    """

    event_type: EventType = Field(
        ...,
        description="The type of operational event being recorded.",
        examples=[EventType.FUEL_FILLED],
    )
    entity_type: EntityType = Field(
        ...,
        description="The fleet entity domain this event concerns.",
        examples=[EntityType.VEHICLE],
    )
    entity_id: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description=(
            "Identifier of the specific entity (vehicle plate, driver ID, etc.). "
            "String to accommodate heterogeneous key formats."
        ),
        examples=["MH12AB1234"],
    )
    occurred_at: datetime = Field(
        ...,
        description=(
            "When the event occurred in the physical world (UTC). "
            "For offline events this may predate submission time."
        ),
    )
    capture_method: CaptureMethod = Field(
        ...,
        description="Channel through which this event was captured.",
        examples=[CaptureMethod.WHATSAPP_BOT],
    )
    created_by: Optional[str] = Field(
        None,
        max_length=255,
        description=(
            "ID of the user or service submitting this event. "
            "Omit for fully automated / system-generated events."
        ),
        examples=["user-uuid-123"],
    )
    payload: Optional[dict[str, Any]] = Field(
        None,
        description=(
            "Event-specific data.  Structure is defined per event_type "
            "in the FleetGuard Event Catalogue."
        ),
        examples=[{"liters": 45.5, "cost_inr": 4095, "odometer_km": 112340}],
    )
    event_metadata: Optional[dict[str, Any]] = Field(
        None,
        description=(
            "Operational metadata: source IP, device ID, app version, "
            "correlation IDs, etc.  Not business data."
        ),
        examples=[{"source_ip": "10.0.0.1", "app_version": "2.1.0"}],
    )
    notes: Optional[str] = Field(
        None,
        description="Optional free-text annotation.",
    )


# ===========================================================================
# Patch Schema
# ===========================================================================

class OperationalEventUpdate(BaseModel):
    """
    Schema for partially updating an Operational Event.

    Only mutable fields are exposed here.  The event's core data
    (event_type, entity, payload, occurred_at) is immutable once recorded.

    Used by:
      • Validation & Enrichment Engine — to advance verification_status.
      • Fleet manager review UI — to add human notes or mark disputed events.
    """

    verification_status: Optional[VerificationStatus] = Field(
        None,
        description=(
            "Updated verification state.  Follows the state machine: "
            "PENDING → VERIFIED | DISPUTED | REJECTED."
        ),
    )
    notes: Optional[str] = Field(
        None,
        description="Human-readable annotation added during review.",
    )


# ===========================================================================
# Read Schema
# ===========================================================================

class OperationalEventResponse(BaseModel):
    """
    Full representation of an Operational Event as returned by the API.

    Consumed by:
      • Event Processor
      • Fleet Memory
      • Fleet Intelligence Engine
      • Dashboard / audit trail UI
    """

    id: uuid.UUID = Field(..., description="Globally unique event identifier.")
    event_type: EventType = Field(..., description="What happened.")
    entity_type: EntityType = Field(..., description="Domain entity this event concerns.")
    entity_id: str = Field(..., description="ID of the specific entity.")
    occurred_at: datetime = Field(..., description="When the event happened (UTC).")
    recorded_at: datetime = Field(..., description="When the event was stored by the platform (UTC).")
    capture_method: CaptureMethod = Field(..., description="How the event was captured.")
    verification_status: VerificationStatus = Field(..., description="Current validation state.")
    created_by: Optional[str] = Field(None, description="Submitting user or service ID.")
    payload: Optional[dict[str, Any]] = Field(None, description="Event-specific data bag.")
    event_metadata: Optional[dict[str, Any]] = Field(None, description="Operational metadata bag.")
    notes: Optional[str] = Field(None, description="Free-text annotation.")
    created_at: datetime = Field(..., description="Row insert timestamp.")
    updated_at: datetime = Field(..., description="Row last-modified timestamp.")

    model_config = {"from_attributes": True}
