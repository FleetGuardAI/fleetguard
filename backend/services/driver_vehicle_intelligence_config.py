"""
FleetGuard — Driver Vehicle Intelligence Configuration
Centralized thresholds and configuration constants for Phase 4 deterministic intelligence.
"""

import os
import json
from dataclasses import dataclass

@dataclass
class DriverVehicleIntelligenceConfig:
    # --- Freshness/Staleness ---
    PHONE_GPS_EVENT_STALE_AFTER_SECONDS: int = 300
    PHONE_GPS_INGESTION_STALE_AFTER_SECONDS: int = 300
    
    HARDWARE_GPS_EVENT_STALE_AFTER_SECONDS: int = 120
    HARDWARE_GPS_INGESTION_STALE_AFTER_SECONDS: int = 120

    # --- Time Skew ---
    MAX_LOCATION_COMPARISON_TIMESTAMP_DELTA_SECONDS: int = 120

    # --- Proximity ---
    DRIVER_VEHICLE_PROXIMITY_METERS: float = 50.0
    DRIVER_VEHICLE_POSSIBLE_PROXIMITY_METERS: float = 200.0

    # --- Divergence ---
    SIGNIFICANT_SOURCE_DIVERGENCE_METERS: float = 500.0
    SOURCE_DIVERGENCE_DURATION_SECONDS: int = 180

    # --- Movement ---
    VEHICLE_MOVING_SPEED_THRESHOLD_KMH: float = 10.0
    DRIVER_STATIONARY_SPEED_THRESHOLD_KMH: float = 2.0

    # --- Anomaly Lifecycle ---
    MINIMUM_ANOMALY_DURATION_SECONDS: int = 300

# Global singleton
    # ---------------------------------------------------------
    # Replay / Calibration Support
    # ---------------------------------------------------------
    def load_from_json(self, filepath: str):
        """Loads candidate thresholds from a JSON file, overriding defaults."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Config file not found: {filepath}")
            
        with open(filepath, 'r') as f:
            data = json.load(f)
            
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)

intelligence_config = DriverVehicleIntelligenceConfig()
