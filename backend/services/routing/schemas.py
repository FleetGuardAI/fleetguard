"""
FleetGuard — Routing Domain Schemas and Contracts
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class CostEstimate(BaseModel):
    distance_km: float
    fuel_liters: Optional[float] = None
    fuel_cost: Optional[float] = None
    fuel_price_per_liter: Optional[float] = None
    vehicle_mileage_km_per_liter: Optional[float] = None
    toll_estimate: Optional[float] = None
    tolls_available: bool = True
    direct_travel_cost: Optional[float] = None
    currency: str = "INR"
    disclosures: List[str] = []


class RouteOption(BaseModel):
    id: str = Field(description="Unique identifier for this route option (e.g. route-0)")
    category: str = Field(description="RECOMMENDED | FASTEST | LOWEST_COST | ALTERNATIVE")
    category_label: str = Field(description="Human readable label e.g. 'Recommended (Balanced)'")
    distance_km: float
    duration_hours: float
    duration_seconds: int
    polyline: str = Field(description="Google-encoded polyline string")
    cost_estimate: CostEstimate
    summary: Optional[str] = None
    toll_estimate: Optional[float] = None
    tolls_available: bool = True
    provider: str
    traffic_aware: bool = False
    vehicle_restrictions_supported: bool = False
    suitability_warning: Optional[str] = None
    score: float = Field(default=0.0, description="Normalized optimization score")
    selection_reason: Optional[str] = None


class RouteCalculationInput(BaseModel):
    origin_lat: float
    origin_lng: float
    destination_lat: float
    destination_lng: float
    origin_address: Optional[str] = None
    destination_address: Optional[str] = None
    vehicle_id: Optional[int] = None
    vehicle_class: Optional[str] = None
    vehicle_mileage: Optional[float] = None
    fuel_price: Optional[float] = None
    avoid_tolls: bool = False
    avoid_highways: bool = False


class RouteCalculationOutput(BaseModel):
    origin_lat: float
    origin_lng: float
    destination_lat: float
    destination_lng: float
    provider: str
    recommended_route: RouteOption
    routes: List[RouteOption]
    calculated_at: datetime
    execution_time_ms: float
