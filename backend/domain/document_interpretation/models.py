"""
FleetGuard Document Interpretation Framework - Models
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class BusinessDocumentType(str, Enum):
    """
    Explicit FleetGuard business document types.
    """
    FUEL_RECEIPT = "FUEL_RECEIPT"
    MAINTENANCE_INVOICE = "MAINTENANCE_INVOICE"
    TYRE_INVOICE = "TYRE_INVOICE"
    INSURANCE_CERTIFICATE = "INSURANCE_CERTIFICATE"
    REGISTRATION_CERTIFICATE = "REGISTRATION_CERTIFICATE"
    FITNESS_CERTIFICATE = "FITNESS_CERTIFICATE"
    POLLUTION_CERTIFICATE = "POLLUTION_CERTIFICATE"
    DRIVER_LICENSE = "DRIVER_LICENSE"
    UNKNOWN = "UNKNOWN"


class ValidationIssue(BaseModel):
    """
    Immutable representation of a business validation issue.
    """
    field_name: str
    severity: str  # e.g., "ERROR", "WARNING"
    error_code: str
    message: str

    model_config = {
        "frozen": True,
        "extra": "forbid"
    }


class InterpretationResult(BaseModel):
    """
    Immutable wrapper for the output of document interpretation.
    """
    interpretation_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    structured_document_id: str
    business_document_type: BusinessDocumentType
    operational_events: List[Any] = Field(default_factory=list)  # List of BaseOperationalEvent
    validation_results: List[ValidationIssue] = Field(default_factory=list)
    interpreted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "frozen": True,
        "extra": "forbid"
    }
