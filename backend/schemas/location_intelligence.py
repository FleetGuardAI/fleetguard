"""
FleetGuard — Driver Vehicle Intelligence Schemas
Pydantic schemas for derived states and intelligence output.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel
from enum import Enum

class FreshnessState(str, Enum):
    FRESH = "FRESH"
    AGING = "AGING"
    STALE = "STALE"
    OFFLINE = "OFFLINE"
    UNKNOWN = "UNKNOWN"

class ProximityState(str, Enum):
    WITH_VEHICLE = "WITH_VEHICLE"
    POSSIBLY_WITH_VEHICLE = "POSSIBLY_WITH_VEHICLE"
    AWAY_FROM_VEHICLE = "AWAY_FROM_VEHICLE"
    UNKNOWN = "UNKNOWN"

class MovementState(str, Enum):
    BOTH_MOVING = "BOTH_MOVING"
    BOTH_STATIONARY = "BOTH_STATIONARY"
    VEHICLE_MOVING_DRIVER_STATIONARY = "VEHICLE_MOVING_DRIVER_STATIONARY"
    DRIVER_MOVING_VEHICLE_STATIONARY = "DRIVER_MOVING_VEHICLE_STATIONARY"
    MOVING_TOGETHER = "MOVING_TOGETHER"
    UNKNOWN = "UNKNOWN"

class DivergenceState(str, Enum):
    ALIGNED = "ALIGNED"
    MINOR_DIVERGENCE = "MINOR_DIVERGENCE"
    SIGNIFICANT_DIVERGENCE = "SIGNIFICANT_DIVERGENCE"
    STALE_SOURCE = "STALE_SOURCE"
    UNKNOWN = "UNKNOWN"


class LocationStateInfo(BaseModel):
    timestamp: datetime
    received_at: datetime
    latitude: float
    longitude: float
    speed: Optional[float]
    heading: Optional[float]
    accuracy: Optional[float]
    event_age_seconds: float
    ingestion_age_seconds: float
    freshness: FreshnessState


class DriverVehicleSignals(BaseModel):
    # Context
    company_id: int
    vehicle_id: int
    driver_id: Optional[int]
    trip_id: Optional[int]
    
    # Base states
    phone_state: Optional[LocationStateInfo]
    hardware_state: Optional[LocationStateInfo]
    
    # Deltas
    time_delta_seconds: Optional[float]
    is_temporally_compatible: bool
    distance_meters: Optional[float]
    effective_uncertainty_meters: Optional[float]
    
    # Derived States
    proximity_state: ProximityState
    movement_state: MovementState
    divergence_state: DivergenceState
    
    # Operational Context
    driver_duty_status: Optional[str]
    vehicle_status: Optional[str]
    trip_status: Optional[str]

    def to_evidence_dict(self) -> Dict[str, Any]:
        """Convert signals to a flat evidence dictionary suitable for JSONB storage."""
        evidence = {
            "vehicle_id": self.vehicle_id,
            "driver_id": self.driver_id,
            "trip_id": self.trip_id,
            "is_temporally_compatible": self.is_temporally_compatible,
            "distance_meters": self.distance_meters,
            "effective_uncertainty_meters": self.effective_uncertainty_meters,
            "time_delta_seconds": self.time_delta_seconds,
            "proximity_state": self.proximity_state.value,
            "movement_state": self.movement_state.value,
            "divergence_state": self.divergence_state.value,
            "driver_duty_status": self.driver_duty_status,
            "vehicle_status": self.vehicle_status,
            "trip_status": self.trip_status,
        }
        
        if self.phone_state:
            evidence.update({
                "driver_timestamp": self.phone_state.timestamp.isoformat(),
                "driver_received_at": self.phone_state.received_at.isoformat(),
                "driver_latitude": self.phone_state.latitude,
                "driver_longitude": self.phone_state.longitude,
                "driver_speed": self.phone_state.speed,
                "driver_heading": self.phone_state.heading,
                "driver_accuracy": self.phone_state.accuracy,
                "driver_event_age": self.phone_state.event_age_seconds,
                "driver_ingestion_age": self.phone_state.ingestion_age_seconds,
                "driver_freshness": self.phone_state.freshness.value,
            })
            
        if self.hardware_state:
            evidence.update({
                "vehicle_timestamp": self.hardware_state.timestamp.isoformat(),
                "vehicle_received_at": self.hardware_state.received_at.isoformat(),
                "vehicle_latitude": self.hardware_state.latitude,
                "vehicle_longitude": self.hardware_state.longitude,
                "vehicle_speed": self.hardware_state.speed,
                "vehicle_heading": self.hardware_state.heading,
                "vehicle_accuracy": self.hardware_state.accuracy,
                "vehicle_event_age": self.hardware_state.event_age_seconds,
                "vehicle_ingestion_age": self.hardware_state.ingestion_age_seconds,
                "vehicle_freshness": self.hardware_state.freshness.value,
            })
            
        return evidence
