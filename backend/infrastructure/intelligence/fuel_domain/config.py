from dataclasses import dataclass

@dataclass(frozen=True)
class FuelIntelligenceConfig:
    """
    Business thresholds for the Fuel Intelligence pipeline.
    In a real system, this could be loaded dynamically per customer.
    """
    quantity_tolerance_liters: float = 5.0
    location_radius_meters: float = 100.0
    timing_window_seconds: int = 1800  # 30 minutes
    tank_capacity_tolerance_liters: float = 2.0
