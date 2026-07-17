"""
FleetGuard — Evidence Schemas

Pydantic schemas for the Evidence API and services.
"""

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from models.evidence import EvidenceType, EvidenceStatus


class EvidenceBase(BaseModel):
    """Base fields shared across all evidence schemas."""
    evidence_type: EvidenceType = Field(
        ...,
        description="Category of the evidence.",
    )
    source: str = Field(
        ...,
        description="The system or user that generated this evidence.",
        examples=["whatsapp_bot", "telematics_gateway"],
    )
    summary: str = Field(
        ...,
        description="Short human-readable summary.",
        max_length=500,
    )
    details: Optional[str] = Field(
        None,
        description="Longer explanation or reasoning.",
    )
    raw_data: Optional[dict[str, Any]] = Field(
        None,
        description="Schema-less JSON payload specific to the evidence type.",
    )


class EvidenceCreate(EvidenceBase):
    """
    Schema for downstream providers to submit new evidence.
    Does not include ID, created_at, or status (defaults to COMPLETED unless specified).
    """
    status: Optional[EvidenceStatus] = Field(
        EvidenceStatus.COMPLETED,
        description="Status of the evidence generation. Defaults to COMPLETED.",
    )


class EvidenceStatusUpdate(BaseModel):
    """
    Schema for updating the status of an existing async evidence request.
    """
    status: EvidenceStatus = Field(
        ...,
        description="New status for the evidence record.",
    )


class EvidenceResponse(EvidenceBase):
    """
    Schema for API responses containing full evidence data.
    """
    id: uuid.UUID = Field(...)
    event_id: uuid.UUID = Field(...)
    status: EvidenceStatus = Field(...)
    created_at: datetime = Field(...)

    model_config = ConfigDict(from_attributes=True)
