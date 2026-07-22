"""
FleetGuard Document Interpretation Framework - Operational Events
"""

import uuid
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from typing import Dict, Any


class BaseOperationalEvent(BaseModel):
    """
    Immutable representation of an observed business fact.
    """
    event_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    recorded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source_document_id: str
    
    model_config = {
        "frozen": True,
        "extra": "forbid"
    }


class FuelPurchaseRecorded(BaseOperationalEvent):
    fuel_quantity: float
    total_amount: float
    currency: str = "INR"
    purchase_date: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MaintenancePerformed(BaseOperationalEvent):
    total_amount: float
    currency: str = "INR"
    service_date: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TyreReplacementRecorded(BaseOperationalEvent):
    total_amount: float
    currency: str = "INR"
    replacement_date: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class InsuranceUpdated(BaseOperationalEvent):
    policy_number: str
    expiry_date: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class VehicleRegistrationUpdated(BaseOperationalEvent):
    registration_number: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class VehicleFitnessUpdated(BaseOperationalEvent):
    fitness_certificate_number: str
    expiry_date: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class VehiclePollutionUpdated(BaseOperationalEvent):
    pollution_certificate_number: str
    expiry_date: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DriverLicenseUpdated(BaseOperationalEvent):
    license_number: str
    expiry_date: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
