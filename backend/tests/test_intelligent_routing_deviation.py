"""
FleetGuard — Comprehensive Test Suite for Intelligent Routing, Cost Estimation,
Route Persistence & Versioning, Geospatial Corridor Calculation, Deviation Detection,
Driver Obstruction Reporting, and Multi-Tenant Isolation.
"""

import pytest
import math
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch

from services.routing.schemas import RouteCalculationInput, CostEstimate
from services.routing.cost_service import CostCalculationService, DEFAULT_DIESEL_PRICE_INR, DEFAULT_FLEET_MILEAGE
from services.routing.optimizer import RouteOptimizer
from services.routing.engine import RoutingEngine
from services.routing.base import BaseRoutingProvider
from services.deviation_service import (
    haversine_distance,
    point_to_segment_distance,
    calculate_min_distance_to_polyline,
    RouteDeviationService
)
from models.route_domain import (
    RouteVersion, RouteDeviationEvent, RouteVersionStatus, RouteType,
    DeviationStatus, DeviationSeverity, ObstructionReason
)
from models.trip_domain import Trip, TripStatus
from models.company import Company
from models.user import User
from models.driver_domain import Driver
from models.vehicle_domain import Vehicle
from services.route_version_service import RouteVersionService
import polyline


# ==============================================================================
# 1. Cost Estimation Service Unit Tests
# ==============================================================================

def test_cost_calculation_with_known_mileage_and_tolls():
    # 200 km, 4.0 km/L, 95.0 INR/L, 150.0 INR toll
    cost = CostCalculationService.calculate_cost(
        distance_km=200.0,
        vehicle_mileage=4.0,
        fuel_price=95.0,
        toll_estimate=150.0,
        tolls_available=True
    )
    assert cost.distance_km == 200.0
    assert cost.fuel_liters == 50.0  # 200 / 4
    assert cost.fuel_cost == 4750.0  # 50 * 95
    assert cost.toll_estimate == 150.0
    assert cost.tolls_available is True
    assert cost.direct_travel_cost == 4900.0  # 4750 + 150


def test_cost_calculation_missing_mileage_uses_defaults():
    cost = CostCalculationService.calculate_cost(
        distance_km=100.0,
        vehicle_mileage=None,
        fuel_price=None,
        toll_estimate=None,
        tolls_available=False
    )
    assert cost.vehicle_mileage_km_per_liter == DEFAULT_FLEET_MILEAGE
    assert cost.fuel_price_per_liter == DEFAULT_DIESEL_PRICE_INR
    assert cost.toll_estimate is None
    assert cost.tolls_available is False
    assert len(cost.disclosures) >= 2


def test_cost_calculation_vehicle_class_mileage():
    cost = CostCalculationService.calculate_cost(
        distance_km=80.0,
        vehicle_class="LIGHT_COMMERCIAL",
        fuel_price=90.0,
    )
    assert cost.vehicle_mileage_km_per_liter == 8.0
    assert cost.fuel_liters == 10.0
    assert cost.fuel_cost == 900.0


# ==============================================================================
# 2. Route Optimization & Multi-Criteria Scoring Tests
# ==============================================================================

def test_optimizer_single_route():
    dummy_cost = CostEstimate(
        distance_km=100.0, fuel_liters=25.0, fuel_cost=2250.0,
        toll_estimate=100.0, tolls_available=True, direct_travel_cost=2350.0
    )
    raw = [{
        "distance_km": 100.0,
        "duration_hours": 2.0,
        "duration_seconds": 7200,
        "polyline": "dummy_poly",
        "cost_estimate": dummy_cost,
        "provider": "google"
    }]
    options = RouteOptimizer.optimize_routes(raw)
    assert len(options) == 1
    assert options[0].category == "RECOMMENDED"
    assert "Direct Route" in options[0].category_label


def test_optimizer_multiple_routes_categorization():
    cost_fast = CostEstimate(distance_km=120.0, direct_travel_cost=3200.0)
    cost_cheap = CostEstimate(distance_km=90.0, direct_travel_cost=2400.0)
    cost_balanced = CostEstimate(distance_km=100.0, direct_travel_cost=2600.0)

    raw = [
        {"distance_km": 120.0, "duration_hours": 1.8, "duration_seconds": 6480, "polyline": "p1", "cost_estimate": cost_fast},
        {"distance_km": 90.0, "duration_hours": 2.6, "duration_seconds": 9360, "polyline": "p2", "cost_estimate": cost_cheap},
        {"distance_km": 100.0, "duration_hours": 2.0, "duration_seconds": 7200, "polyline": "p3", "cost_estimate": cost_balanced},
    ]

    options = RouteOptimizer.optimize_routes(raw)
    assert len(options) == 3
    categories = [opt.category for opt in options]
    assert "RECOMMENDED" in categories
    assert "FASTEST" in categories
    assert "LOWEST_COST" in categories


# ==============================================================================
# 3. Geospatial Point-to-Segment & Polyline Distance Tests
# ==============================================================================

def test_haversine_distance_known_points():
    # Delhi (28.6139, 77.2090) to Mumbai (19.0760, 72.8777) approx 1150 km
    d = haversine_distance(28.6139, 77.2090, 19.0760, 72.8777)
    assert 1140000.0 < d < 1170000.0


def test_point_to_segment_on_line():
    # Segment from (28.0, 77.0) to (28.0, 78.0)
    # Point at midpoint (28.0, 77.5) should be distance ~0
    dist = point_to_segment_distance(28.0, 77.5, 28.0, 77.0, 28.0, 78.0)
    assert dist < 1.0  # within 1 meter


def test_point_to_segment_offset():
    # Point 0.001 deg North of line (~111 meters)
    dist = point_to_segment_distance(28.001, 77.5, 28.0, 77.0, 28.0, 78.0)
    assert 105.0 < dist < 115.0


def test_calculate_min_distance_to_polyline():
    coords = [(28.0, 77.0), (28.0, 77.5), (28.5, 77.5)]
    # Point near second segment
    dist = calculate_min_distance_to_polyline(28.25, 77.501, coords)
    assert 90.0 < dist < 120.0


# ==============================================================================
# 4. Routing Engine Validation Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_routing_engine_invalid_coordinates():
    engine = RoutingEngine()
    req = RouteCalculationInput(
        origin_lat=95.0, origin_lng=77.0,  # invalid latitude > 90
        destination_lat=28.0, destination_lng=77.0
    )
    with pytest.raises(ValueError, match="Invalid origin coordinates"):
        await engine.calculate_routes(req)


@pytest.mark.asyncio
async def test_routing_engine_identical_coordinates():
    engine = RoutingEngine()
    req = RouteCalculationInput(
        origin_lat=28.5, origin_lng=77.2,
        destination_lat=28.5, destination_lng=77.2
    )
    with pytest.raises(ValueError, match="identical"):
        await engine.calculate_routes(req)


# ==============================================================================
# 5. Route Deviation Detection State Machine Integration Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_deviation_service_within_corridor(db_session):
    # Setup test company and trip with approved route
    company = Company(company_name="Fleet Corp Test", owner_name="Owner", mobile_number="9876500001")
    db_session.add(company)
    await db_session.flush()

    # Route: line along latitude 28.0 from lon 77.0 to 77.2
    test_polyline = polyline.encode([(28.0, 77.0), (28.0, 77.1), (28.0, 77.2)])

    trip = Trip(
        trip_id="TRP-TEST-001",
        status=TripStatus.IN_PROGRESS,
        company_id=company.id,
        origin_lat=28.0, origin_lng=77.0,
        destination_lat=28.0, destination_lng=77.2,
        route_polyline=test_polyline,
        route_distance_km=22.0,
        route_duration_hours=0.5
    )
    db_session.add(trip)
    await db_session.commit()
    await db_session.refresh(trip)

    dev_service = RouteDeviationService(db_session)
    dev_service.threshold_meters = 200.0

    # Point directly on route
    result = await dev_service.evaluate_position(
        driver_id=1,
        company_id=company.id,
        latitude=28.0,
        longitude=77.05,
        accuracy=10.0,
        trip_id_hint="TRP-TEST-001"
    )
    assert result["status"] == "ON_ROUTE"
    assert result["distance_meters"] < 20.0


@pytest.mark.asyncio
async def test_deviation_service_outlier_confirmation_state_machine(db_session):
    company = Company(company_name="Fleet Corp Dev", owner_name="Owner", mobile_number="9876500002")
    db_session.add(company)
    await db_session.flush()

    test_polyline = polyline.encode([(28.0, 77.0), (28.0, 77.1), (28.0, 77.2)])
    trip = Trip(
        trip_id="TRP-TEST-002",
        status=TripStatus.IN_PROGRESS,
        company_id=company.id,
        origin_lat=28.0, origin_lng=77.0,
        destination_lat=28.0, destination_lng=77.2,
        route_polyline=test_polyline,
    )
    db_session.add(trip)
    await db_session.commit()
    await db_session.refresh(trip)

    dev_service = RouteDeviationService(db_session)
    dev_service.threshold_meters = 200.0
    dev_service.confirmation_count = 3

    # Off-route point: 0.005 deg North (~550 meters off corridor)
    off_lat, off_lng = 28.005, 77.05

    # 1st Outlier: Should create SUSPECTED incident (NOT yet confirmed)
    res1 = await dev_service.evaluate_position(
        driver_id=1, company_id=company.id,
        latitude=off_lat, longitude=off_lng, accuracy=15.0,
        trip_id_hint="TRP-TEST-002"
    )
    assert res1["status"] == "SUSPECTED_DEVIATION"
    assert res1["distance_meters"] > 400.0

    # 2nd Outlier: Still SUSPECTED
    res2 = await dev_service.evaluate_position(
        driver_id=1, company_id=company.id,
        latitude=off_lat, longitude=off_lng, accuracy=15.0,
        trip_id_hint="TRP-TEST-002"
    )
    assert res2["status"] == "SUSPECTED"

    # 3rd Consecutive Outlier: Should transition to CONFIRMED and generate notification!
    res3 = await dev_service.evaluate_position(
        driver_id=1, company_id=company.id,
        latitude=off_lat, longitude=off_lng, accuracy=15.0,
        trip_id_hint="TRP-TEST-002"
    )
    assert res3["status"] == "CONFIRMED_DEVIATION"

    # Now simulate vehicle returning within corridor (< 150m)
    on_lat, on_lng = 28.0005, 77.05  # ~55m from route
    res4 = await dev_service.evaluate_position(
        driver_id=1, company_id=company.id,
        latitude=on_lat, longitude=on_lng, accuracy=10.0,
        trip_id_hint="TRP-TEST-002"
    )
    assert res4["status"] == "RETURNED_TO_ROUTE"


@pytest.mark.asyncio
async def test_gps_noise_filtering(db_session):
    company = Company(company_name="Fleet Noise Test", owner_name="Owner", mobile_number="9876500003")
    db_session.add(company)
    await db_session.flush()

    test_polyline = polyline.encode([(28.0, 77.0), (28.0, 77.1), (28.0, 77.2)])
    trip = Trip(
        trip_id="TRP-TEST-NOISE",
        status=TripStatus.IN_PROGRESS,
        company_id=company.id,
        origin_lat=28.0, origin_lng=77.0,
        destination_lat=28.0, destination_lng=77.2,
        route_polyline=test_polyline,
    )
    db_session.add(trip)
    await db_session.commit()

    dev_service = RouteDeviationService(db_session)
    dev_service.threshold_meters = 200.0
    dev_service.confirmation_count = 3

    # Point with poor accuracy (120 meters > 80m limit)
    res = await dev_service.evaluate_position(
        driver_id=1, company_id=company.id,
        latitude=28.005, longitude=77.05, accuracy=120.0,
        trip_id_hint="TRP-TEST-NOISE"
    )
    # Created suspected, but poor accuracy does NOT count as valid for confirmation progression
    assert res["status"] == "SUSPECTED_DEVIATION"


# ==============================================================================
# 6. Route Versioning & Immutability Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_route_version_persistence_and_superseding(db_session):
    company = Company(company_name="Fleet Version Test", owner_name="Owner", mobile_number="9876500004")
    db_session.add(company)
    await db_session.flush()

    trip = Trip(
        trip_id="TRP-VERSIONS",
        status=TripStatus.CREATED,
        company_id=company.id,
        origin_lat=28.0, origin_lng=77.0,
        destination_lat=28.5, destination_lng=77.5,
    )
    db_session.add(trip)
    await db_session.commit()
    await db_session.refresh(trip)

    version_service = RouteVersionService(db_session)

    # Version 1 (Planned)
    v1_data = {
        "polyline": "poly_v1",
        "distance_km": 100.0,
        "duration_hours": 2.0,
        "fuel_cost_estimate": 2000.0,
        "toll_cost_estimate": 150.0,
        "total_cost_estimate": 2150.0,
        "category": "RECOMMENDED"
    }
    v1 = await version_service.persist_route_version(
        trip_id=trip.id,
        company_id=company.id,
        route_option_data=v1_data,
        status=RouteVersionStatus.APPROVED
    )
    assert v1.version_number == 1
    assert v1.status == RouteVersionStatus.APPROVED

    # Verify trip was updated with v1
    await db_session.refresh(trip)
    assert trip.approved_route_version_id == v1.id
    assert trip.route_distance_km == 100.0

    # Version 2 (Recalculated detour approved)
    v2_data = {
        "polyline": "poly_v2",
        "distance_km": 115.0,
        "duration_hours": 2.3,
        "fuel_cost_estimate": 2300.0,
        "toll_cost_estimate": 150.0,
        "total_cost_estimate": 2450.0,
        "category": "RECALCULATED"
    }
    v2 = await version_service.persist_route_version(
        trip_id=trip.id,
        company_id=company.id,
        route_option_data=v2_data,
        status=RouteVersionStatus.APPROVED,
        reason_for_change="Approved detour around road construction"
    )
    assert v2.version_number == 2
    assert v2.status == RouteVersionStatus.APPROVED

    # Verify v1 was automatically superseded
    await db_session.refresh(v1)
    assert v1.status == RouteVersionStatus.SUPERSEDED

    # Verify trip now references v2
    await db_session.refresh(trip)
    assert trip.approved_route_version_id == v2.id
    assert trip.route_distance_km == 115.0


# ==============================================================================
# 7. Multi-Tenant Isolation Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_tenant_isolation_route_access(db_session):
    company_a = Company(company_name="Company A", owner_name="Owner A", mobile_number="9876500005")
    company_b = Company(company_name="Company B", owner_name="Owner B", mobile_number="9876500006")
    db_session.add_all([company_a, company_b])
    await db_session.flush()

    trip_a = Trip(
        trip_id="TRP-A-001",
        status=TripStatus.IN_PROGRESS,
        company_id=company_a.id,
        origin_lat=28.0, origin_lng=77.0,
        destination_lat=28.5, destination_lng=77.5,
        route_polyline="poly_a"
    )
    db_session.add(trip_a)
    await db_session.commit()

    version_service = RouteVersionService(db_session)

    # Company B cannot access Company A's active route
    active_b = await version_service.get_active_route_version(trip_a.id, company_id=company_b.id)
    assert active_b is None

    # Company B cannot persist a route for Company A's trip
    with pytest.raises(ValueError, match="not found in company"):
        await version_service.persist_route_version(
            trip_id=trip_a.id,
            company_id=company_b.id,
            route_option_data={"polyline": "hack"}
        )
