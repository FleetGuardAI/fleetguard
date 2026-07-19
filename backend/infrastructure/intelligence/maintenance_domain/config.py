"""
Fleet Intelligence Engine - Maintenance Domain Configuration
"""

class MaintenanceIntelligenceConfig:
    def __init__(
        self,
        service_interval_days: int = 180,
        service_interval_km: float = 10000.0,
        engine_oil_interval_km: float = 10000.0,
        brake_inspection_interval_days: int = 90,
        tyre_rotation_interval_km: float = 20000.0,
        critical_overdue_grace_days: int = 14,
        repeated_failure_threshold_count: int = 3,
        repeated_failure_time_window_days: int = 90
    ):
        self.service_interval_days = service_interval_days
        self.service_interval_km = service_interval_km
        self.engine_oil_interval_km = engine_oil_interval_km
        self.brake_inspection_interval_days = brake_inspection_interval_days
        self.tyre_rotation_interval_km = tyre_rotation_interval_km
        self.critical_overdue_grace_days = critical_overdue_grace_days
        self.repeated_failure_threshold_count = repeated_failure_threshold_count
        self.repeated_failure_time_window_days = repeated_failure_time_window_days
