"""
Fleet Intelligence Engine - Evidence Models
"""

from enum import Enum
from typing import Dict, Any, Optional, List
import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class Reliability(str, Enum):
    """Typed reliability indicator for evidence."""
    UNKNOWN = "UNKNOWN"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    VERIFIED = "VERIFIED"


class BaseEvidence(BaseModel):
    """
    Base Evidence Model.
    
    Immutable, pure domain object containing only common metadata.
    Does NOT contain a generic payload. All business fields must be 
    strongly typed in subclasses.
    """
    evidence_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    evidence_type: str
    source: str
    origin: str
    collected_at: datetime
    reliability: Reliability
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = {
        "frozen": True,
        "extra": "forbid"
    }


# ===========================================================================
# Evidence Subtypes (Strongly Typed)
# ===========================================================================

class ReceiptEvidence(BaseEvidence):
    evidence_type: str = "ReceiptEvidence"
    quantity: Optional[float] = None
    amount: Optional[float] = None
    station_name: Optional[str] = None
    invoice_number: Optional[str] = None


class GPSEvidence(BaseEvidence):
    evidence_type: str = "GPSEvidence"
    latitude: float
    longitude: float
    accuracy: float


class FuelSensorEvidence(BaseEvidence):
    evidence_type: str = "FuelSensorEvidence"
    fuel_before: float
    fuel_after: float


class VehicleEvidence(BaseEvidence):
    evidence_type: str = "VehicleEvidence"
    vehicle_id: str
    tank_capacity: float


class DriverEvidence(BaseEvidence):
    evidence_type: str = "DriverEvidence"
    driver_id: str
    assigned_vehicle: Optional[str] = None


class DrivingSessionEvidence(BaseEvidence):
    """
    Contains the raw telemetry points for a driving session/journey.
    This preserves the separation between immutable observations and the
    deterministic calculations (e.g. max_speed, idle_duration) performed by checks.
    """
    evidence_type: str = "DrivingSessionEvidence"
    # List of dictionaries, each containing raw point data.
    # Expected keys: timestamp, speed_kmh, acceleration_g, latitude, longitude, engine_on
    telemetry_points: List[Dict[str, Any]] = Field(default_factory=list)
    # Optional list of dicts with 'lat' and 'lon' representing the permitted geofence
    expected_route_polygon: Optional[List[Dict[str, float]]] = None


class MaintenanceHistoryEvidence(BaseEvidence):
    evidence_type: str = "MaintenanceHistoryEvidence"
    vehicle_id: str
    service_date: datetime
    odometer_km: float
    engine_hours: Optional[float] = None
    service_type: str
    reported_component_failures: List[str] = Field(default_factory=list)
    diagnostic_codes: List[str] = Field(default_factory=list)


class MaintenanceScheduleEvidence(BaseEvidence):
    evidence_type: str = "MaintenanceScheduleEvidence"
    vehicle_id: str
    next_service_due_date: Optional[datetime] = None
    next_service_due_km: Optional[float] = None


# ===========================================================================
# Tyre Intelligence Models
# ===========================================================================

class TyrePosition(str, Enum):
    FRONT_LEFT = "FRONT_LEFT"
    FRONT_RIGHT = "FRONT_RIGHT"
    REAR_LEFT = "REAR_LEFT"
    REAR_RIGHT = "REAR_RIGHT"
    SPARE = "SPARE"

class WearPatternCategory(str, Enum):
    NORMAL = "NORMAL"
    UNEVEN = "UNEVEN"
    CENTER_WEAR = "CENTER_WEAR"
    EDGE_WEAR = "EDGE_WEAR"
    CUPPING = "CUPPING"
    FEATHERING = "FEATHERING"

class DamageSeverity(str, Enum):
    NONE = "NONE"
    MINOR = "MINOR"
    MODERATE = "MODERATE"
    SEVERE = "SEVERE"
    CRITICAL = "CRITICAL"


class TyreInspectionEvidence(BaseEvidence):
    evidence_type: str = "TyreInspectionEvidence"
    vehicle_id: str
    tyre_position: TyrePosition
    inspection_date: datetime
    tread_depth_mm: float
    tyre_installation_date: datetime
    wear_pattern: WearPatternCategory = WearPatternCategory.NORMAL
    observed_damage_severity: DamageSeverity = DamageSeverity.NONE
    observed_damage_description: Optional[str] = None


class TyrePressureEvidence(BaseEvidence):
    evidence_type: str = "TyrePressureEvidence"
    vehicle_id: str
    tyre_position: TyrePosition
    reading_date: datetime
    tyre_pressure_psi: float
    recommended_pressure_psi: float


class TyreReplacementEvidence(BaseEvidence):
    evidence_type: str = "TyreReplacementEvidence"
    vehicle_id: str
    tyre_position: TyrePosition
    replacement_date: datetime
    reason: str


# ===========================================================================
# Route Intelligence Models
# ===========================================================================

class GeofenceEventType(str, Enum):
    ENTER = "ENTER"
    EXIT = "EXIT"


class PlannedRouteEvidence(BaseEvidence):
    evidence_type: str = "PlannedRouteEvidence"
    trip_id: str
    planned_route_id: str
    vehicle_id: str
    driver_id: Optional[str] = None
    planned_start_time: datetime
    planned_end_time: datetime
    # List of expected coordinates [{"lat": float, "lon": float}]
    gps_track: List[Dict[str, float]] = Field(default_factory=list)


class TripExecutionEvidence(BaseEvidence):
    evidence_type: str = "TripExecutionEvidence"
    trip_id: str
    vehicle_id: str
    driver_id: Optional[str] = None
    actual_start_time: datetime
    actual_end_time: datetime
    # List of actual coordinates over time [{"timestamp": datetime, "lat": float, "lon": float, "speed": float}]
    gps_track: List[Dict[str, Any]] = Field(default_factory=list)
    # Stop durations at specific locations [{"lat": float, "lon": float, "duration_minutes": float, "start_time": datetime}]
    stop_locations: List[Dict[str, Any]] = Field(default_factory=list)


class GeofenceEventEvidence(BaseEvidence):
    evidence_type: str = "GeofenceEventEvidence"
    vehicle_id: str
    geofence_id: str
    event_type: GeofenceEventType
    event_time: datetime
    latitude: float
    longitude: float


class ApprovedStopEvidence(BaseEvidence):
    evidence_type: str = "ApprovedStopEvidence"
    trip_id: str
    # List of explicit permitted stop locations [{"lat": float, "lon": float, "radius_meters": float}] or known stop IDs
    approved_stops: List[Dict[str, Any]] = Field(default_factory=list)
    approved_stop_ids: List[str] = Field(default_factory=list)


# ===========================================================================
# Compliance Intelligence Models
# ===========================================================================

class VehicleRegistrationEvidence(BaseEvidence):
    evidence_type: str = "VehicleRegistrationEvidence"
    vehicle_id: str
    document_number: str
    issuing_authority: str
    issue_date: datetime
    expiry_date: datetime
    jurisdiction: str


class InsuranceEvidence(BaseEvidence):
    evidence_type: str = "InsuranceEvidence"
    vehicle_id: str
    document_number: str
    issuing_authority: str
    issue_date: datetime
    expiry_date: datetime
    document_category: str
    document_status: str


class FitnessCertificateEvidence(BaseEvidence):
    evidence_type: str = "FitnessCertificateEvidence"
    vehicle_id: str
    document_number: str
    issuing_authority: str
    issue_date: datetime
    expiry_date: datetime
    document_status: str


class PollutionCertificateEvidence(BaseEvidence):
    evidence_type: str = "PollutionCertificateEvidence"
    vehicle_id: str
    document_number: str
    issuing_authority: str
    issue_date: datetime
    expiry_date: datetime


class PermitEvidence(BaseEvidence):
    evidence_type: str = "PermitEvidence"
    vehicle_id: str
    document_number: str
    issuing_authority: str
    issue_date: datetime
    expiry_date: datetime
    document_category: str
    jurisdiction: str


class DriverLicenseEvidence(BaseEvidence):
    evidence_type: str = "DriverLicenseEvidence"
    driver_id: str
    document_number: str
    issuing_authority: str
    issue_date: datetime
    expiry_date: datetime
    document_category: str
    jurisdiction: str
