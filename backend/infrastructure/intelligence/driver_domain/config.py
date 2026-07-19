"""
Fleet Intelligence Engine - Driver Domain Configuration
"""

class DriverIntelligenceConfig:
    def __init__(
        self,
        max_speed_kmh: float = 110.0,
        harsh_acceleration_g: float = 0.35,
        harsh_braking_g: float = -0.35, # Expected to be negative or absolute magnitude
        max_idle_seconds: int = 300,
        route_deviation_meters: float = 500.0
    ):
        self.max_speed_kmh = max_speed_kmh
        self.harsh_acceleration_g = harsh_acceleration_g
        self.harsh_braking_g = harsh_braking_g
        self.max_idle_seconds = max_idle_seconds
        self.route_deviation_meters = route_deviation_meters
