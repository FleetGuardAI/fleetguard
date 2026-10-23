"""
FleetGuard — Vehicle Economics & Fleet Roll-Up Schemas
Defines strongly-typed Pydantic schemas for vehicle-level and fleet-level financial economics.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class VehicleEconomicsResponse(BaseModel):
    vehicle_id: int
    registration_number: str
    reporting_period_start: Optional[datetime] = None
    reporting_period_end: Optional[datetime] = None
    
    # Revenue & Costs
    realized_revenue: float = 0.0
    trip_linked_costs: float = 0.0
    vehicle_only_costs: float = 0.0
    total_operating_costs: float = 0.0
    operating_profit: float = 0.0
    operating_margin_pct: Optional[float] = None
    
    # Telemetry & Efficiency
    total_actual_distance_km: Optional[float] = None
    total_actual_fuel_liters: Optional[float] = None
    cost_per_km: Optional[float] = None
    revenue_per_km: Optional[float] = None
    fuel_efficiency_kmpl: Optional[float] = None
    
    # Operations & Utilization
    completed_trips_count: int = 0
    active_trips_count: int = 0
    utilization_rate_pct: Optional[float] = None
    activity_score: Optional[float] = None
    
    # Maintenance State
    maintenance_status: str = "NOT_DUE"
    last_service_date: Optional[datetime] = None
    last_service_odometer: Optional[float] = None
    current_odometer: Optional[float] = None


class FleetRollUpResponse(BaseModel):
    company_id: int
    reporting_period_start: Optional[datetime] = None
    reporting_period_end: Optional[datetime] = None
    
    # Vehicle Counts
    total_vehicles: int = 0
    active_vehicles: int = 0
    
    # Financial Attribution Scopes
    fleet_realized_revenue: float = 0.0
    fleet_trip_linked_costs: float = 0.0
    fleet_vehicle_only_costs: float = 0.0
    company_overhead_costs: float = 0.0
    total_fleet_costs: float = 0.0
    
    # Fleet Profitability
    fleet_operating_profit: float = 0.0
    fleet_net_profit: float = 0.0
    fleet_profit_margin_pct: Optional[float] = None
    
    # Fleet Telemetry & Efficiency
    total_actual_distance_km: Optional[float] = None
    total_actual_fuel_liters: Optional[float] = None
    fleet_cost_per_km: Optional[float] = None
    fleet_revenue_per_km: Optional[float] = None
    fleet_fuel_efficiency_kmpl: Optional[float] = None
    
    # Fleet Operations
    total_completed_trips: int = 0
    fleet_utilization_rate_pct: Optional[float] = None
    fleet_activity_score: Optional[float] = None
    
    # Vehicle-level Breakdown
    vehicles: List[VehicleEconomicsResponse] = Field(default_factory=list)
