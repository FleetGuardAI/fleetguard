import pytest
from datetime import datetime, timezone, timedelta
from models.user import User, UserRole
from models.company import Company
from models.driver_domain import Driver, DriverStatus, DutyStatus
from models.vehicle_domain import Vehicle, VehicleStatus
from models.trip_domain import Trip, TripStatus
from models.location_tracking import DriverLocation, LocationSource
from services.auth_service import get_current_user


@pytest.fixture
def mock_owner_user():
    return User(
        id=101,
        email="owner101@test.com",
        full_name="Fleet Owner 101",
        role=UserRole.COMPANY_ADMIN,
        company_id=10,
        is_active=True
    )


@pytest.fixture
def other_owner_user():
    return User(
        id=102,
        email="owner102@test.com",
        full_name="Fleet Owner 102",
        role=UserRole.COMPANY_ADMIN,
        company_id=99,
        is_active=True
    )


@pytest.mark.asyncio
async def test_tracking_endpoints_end_to_end(client, db_session, mock_owner_user):
    from main import app
    app.dependency_overrides[get_current_user] = lambda: mock_owner_user

    # 1. Setup Company, Vehicle, Driver, Trip, and GPS Points in company 10
    comp = Company(id=10, company_name="Fleet 10 Logistics", owner_name="Fleet Owner 101", mobile_number="+919876543210")
    db_session.add(comp)

    driver = Driver(
        id=501,
        name="Ramesh Sharma",
        phone_number="+919876543211",
        company_id=10,
        status=DriverStatus.ACTIVE,
        duty_status=DutyStatus.ON_DUTY,
        last_known_lat=30.4061,
        last_known_lng=77.9693,
        last_location_at=datetime(2026, 9, 22, 18, 30, 0, tzinfo=timezone.utc),
    )
    db_session.add(driver)

    vehicle = Vehicle(
        id=601,
        registration_number="HR26DX1234",
        make="Tata",
        model="Signa",
        company_id=10,
        assigned_driver_id=501,
        status=VehicleStatus.ACTIVE
    )
    db_session.add(vehicle)

    trip = Trip(
        id=701,
        trip_id="TRP-TEST-001",
        driver_id=501,
        vehicle_id=601,
        company_id=10,
        status=TripStatus.IN_PROGRESS,
        origin_location="Delhi Gateway",
        destination_location="Dehradun Hub",
        actual_start_time=datetime(2026, 9, 22, 18, 0, 0, tzinfo=timezone.utc),
        actual_end_time=None,
        route_distance_km=250.0,
    )
    db_session.add(trip)

    # Add 5 GPS points
    t0 = datetime(2026, 9, 22, 18, 5, 0, tzinfo=timezone.utc)
    for i in range(5):
        pt = DriverLocation(
            id=800 + i,
            driver_id=501,
            company_id=10,
            latitude=30.4000 + i * 0.002,
            longitude=77.9600 + i * 0.002,
            speed=12.5 + i,  # m/s (~45-55 km/h)
            heading=45.0,
            accuracy=4.0,
            timestamp=t0 + timedelta(minutes=i * 2),
            source=LocationSource.PHONE_GPS,
            trip_id="TRP-TEST-001"
        )
        db_session.add(pt)

    await db_session.commit()

    # --- Test 1: List tracking drivers ---
    res_drivers = client.get("/api/v1/tracking/drivers")
    assert res_drivers.status_code == 200
    drivers_data = res_drivers.json()
    assert len(drivers_data) >= 1
    d_match = next((d for d in drivers_data if d["id"] == 501), None)
    assert d_match is not None
    assert d_match["name"] == "Ramesh Sharma"
    assert d_match["vehicle_registration"] == "HR26DX1234"
    assert d_match["total_trips"] == 1
    assert d_match["gps_point_count"] == 5

    # --- Test 2: List driver trips ---
    res_trips = client.get(f"/api/v1/tracking/driver/501/trips")
    assert res_trips.status_code == 200
    trips_data = res_trips.json()
    assert len(trips_data) == 1
    assert trips_data[0]["trip_id"] == "TRP-TEST-001"
    assert trips_data[0]["gps_point_count"] == 5
    assert trips_data[0]["has_gps_data"] is True

    # --- Test 3: Get paginated locations chronologically ---
    res_locs = client.get(f"/api/v1/tracking/driver/501/locations?trip_id=TRP-TEST-001")
    assert res_locs.status_code == 200
    locs_data = res_locs.json()
    assert locs_data["total_points"] == 5
    assert len(locs_data["points"]) == 5
    # Verify chronological order
    p_times = [p["timestamp"] for p in locs_data["points"]]
    assert p_times == sorted(p_times)
    # Verify speed_kmh calculation
    assert locs_data["points"][0]["speed_kmh"] == round(12.5 * 3.6, 1)
    assert locs_data["bounds"] is not None

    # --- Test 4: Driver analytics ---
    res_analytics = client.get(f"/api/v1/tracking/driver/501/analytics?trip_id=TRP-TEST-001")
    assert res_analytics.status_code == 200
    analytics_data = res_analytics.json()
    assert analytics_data["total_trips"] == 1
    assert analytics_data["total_points_analyzed"] == 5
    assert analytics_data["total_recorded_distance_km"] > 0
    assert analytics_data["average_speed_kmh"] > 0

    # --- Test 5: Route history by numeric ID ---
    res_route = client.get(f"/api/v1/tracking/trip/701/route")
    assert res_route.status_code == 200
    route_data = res_route.json()
    assert len(route_data) == 5

    # --- Test 6: Route history by string trip_id ---
    res_route_str = client.get(f"/api/v1/tracking/trip/TRP-TEST-001/route")
    assert res_route_str.status_code == 200
    assert len(res_route_str.json()) == 5

    # --- Test 7: Tenant Isolation: user from another company must get 404 ---
    app.dependency_overrides[get_current_user] = lambda: User(
        id=999,
        email="other@test.com",
        role=UserRole.COMPANY_ADMIN,
        company_id=99,
        is_active=True
    )
    res_forbidden = client.get(f"/api/v1/tracking/driver/501/locations")
    assert res_forbidden.status_code == 404

    res_forbidden_trips = client.get(f"/api/v1/tracking/driver/501/trips")
    assert res_forbidden_trips.status_code == 404
