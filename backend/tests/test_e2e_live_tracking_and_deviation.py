"""
FleetGuard — Comprehensive End-to-End Live Tracking & Route Deviation Verification Suite
Tests GPS ingestion, accuracy filtering, corridor calculation, state machine transitions,
manager alerts, recovery detection, company isolation, and edge cases.
"""

import pytest
import math
import polyline
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch

from sqlalchemy import select, desc
from models.company import Company
from models.user import User, UserRole
from models.driver_domain import Driver, DriverStatus, VerificationStatus, DutyStatus
from models.vehicle_domain import Vehicle
from models.trip_domain import Trip, TripStatus
from models.route_domain import (
    RouteVersion, RouteDeviationEvent, RouteVersionStatus, RouteType,
    DeviationStatus, DeviationSeverity, ObstructionReason
)
from models.notification import Notification, NotificationCategory
from models.location_tracking import DriverLocation, LocationSource
from services.deviation_service import (
    RouteDeviationService,
    calculate_min_distance_to_polyline,
    haversine_distance,
    point_to_segment_distance
)
from routers.location_tracking import (
    LocationPoint,
    LocationBatchRequest,
    batch_upload_locations
)


# ==============================================================================
# Helper setup fixtures
# ==============================================================================

async def setup_test_trip(db_session, company_name="Tracking E2E Logistics", trip_code="TRP-E2E-001"):
    """Seeds a complete active trip with approved route version and driver."""
    company = Company(
        company_name=company_name,
        owner_name="Test Owner",
        mobile_number=f"98{str(abs(hash(company_name)))[:8]}"
    )
    db_session.add(company)
    await db_session.flush()

    vehicle = Vehicle(
        company_id=company.id,
        registration_number=f"MH-{str(abs(hash(trip_code)))[:4]}-AA",
        make="Tata",
        model="Prima 4928.S",
        year=2024
    )
    db_session.add(vehicle)
    await db_session.flush()

    driver = Driver(
        company_id=company.id,
        name="Sunil Kumar",
        phone_number=f"+9197{str(abs(hash(trip_code)))[:8]}",
        status=DriverStatus.ACTIVE,
        verification_status=VerificationStatus.APPROVED,
        duty_status=DutyStatus.ON_DUTY,
        last_known_lat=28.6139,
        last_known_lng=77.2090
    )
    db_session.add(driver)
    await db_session.flush()

    # Create straight horizontal corridor from West (28.60, 77.00) to East (28.60, 77.20)
    # Approx 19.5 km length
    route_coords = [(28.6000, 77.0000), (28.6000, 77.1000), (28.6000, 77.2000)]
    encoded_route = polyline.encode(route_coords)

    trip = Trip(
        trip_id=trip_code,
        status=TripStatus.IN_PROGRESS,
        company_id=company.id,
        driver_id=driver.id,
        vehicle_id=vehicle.id,
        origin_lat=28.6000,
        origin_lng=77.0000,
        destination_lat=28.6000,
        destination_lng=77.2000,
        origin_location="Delhi Hub West",
        destination_location="Delhi Hub East",
        route_polyline=encoded_route,
        route_distance_km=19.5,
        route_duration_hours=0.5
    )
    db_session.add(trip)
    await db_session.flush()

    # Route Version 1 (Approved)
    route_v1 = RouteVersion(
        trip_id=trip.id,
        company_id=company.id,
        version_number=1,
        route_type=RouteType.RECOMMENDED,
        status=RouteVersionStatus.APPROVED,
        origin_lat=28.6000, origin_lng=77.0000,
        destination_lat=28.6000, destination_lng=77.2000,
        polyline=encoded_route,
        distance_km=19.5,
        duration_hours=0.5,
        currency="INR"
    )
    db_session.add(route_v1)
    await db_session.flush()

    trip.approved_route_version_id = route_v1.id
    await db_session.commit()
    await db_session.refresh(trip)
    await db_session.refresh(driver)
    await db_session.refresh(company)

    return {
        "company": company,
        "vehicle": vehicle,
        "driver": driver,
        "trip": trip,
        "route_version": route_v1,
        "route_coords": route_coords
    }


# ==============================================================================
# Phase 3: Route Deviation Logic Scenarios (1 to 10)
# ==============================================================================

@pytest.mark.asyncio
async def test_scenario_1_driver_following_approved_route_no_alert(db_session):
    """Scenario 1: Driver directly on the approved route line produces no alerts."""
    ctx = await setup_test_trip(db_session, trip_code="TRP-SCENARIO-1")
    dev_service = RouteDeviationService(db_session)

    # Coords exactly on route (28.6000, 77.0500)
    result = await dev_service.evaluate_position(
        driver_id=ctx["driver"].id,
        company_id=ctx["company"].id,
        latitude=28.6000,
        longitude=77.0500,
        accuracy=10.0,
        trip_id_hint=ctx["trip"].trip_id
    )

    assert result["status"] == "ON_ROUTE"
    assert result["distance_meters"] < 5.0

    # Verify no deviation events or notifications were created
    events = (await db_session.execute(
        select(RouteDeviationEvent).where(RouteDeviationEvent.trip_id == ctx["trip"].id)
    )).scalars().all()
    assert len(events) == 0

    notifs = (await db_session.execute(
        select(Notification).where(Notification.company_id == ctx["company"].id)
    )).scalars().all()
    assert len(notifs) == 0


@pytest.mark.asyncio
async def test_scenario_2_driver_deviating_under_200m_no_alert(db_session):
    """Scenario 2: Driver deviating by less than 200m threshold (e.g. 110m) produces no alert."""
    ctx = await setup_test_trip(db_session, trip_code="TRP-SCENARIO-2")
    dev_service = RouteDeviationService(db_session)

    # 0.001 degrees latitude difference at Delhi is ~111 meters
    sub_threshold_lat = 28.6010
    sub_threshold_lng = 77.0500

    result = await dev_service.evaluate_position(
        driver_id=ctx["driver"].id,
        company_id=ctx["company"].id,
        latitude=sub_threshold_lat,
        longitude=sub_threshold_lng,
        accuracy=15.0,
        trip_id_hint=ctx["trip"].trip_id
    )

    assert result["status"] == "ON_ROUTE"
    assert 90.0 < result["distance_meters"] < 130.0

    # No incident or notification created
    events = (await db_session.execute(
        select(RouteDeviationEvent).where(RouteDeviationEvent.trip_id == ctx["trip"].id)
    )).scalars().all()
    assert len(events) == 0


@pytest.mark.asyncio
async def test_scenario_3_driver_deviating_beyond_200m_under_3_outliers_no_alert(db_session):
    """Scenario 3: Driver deviating beyond 200m for 1 or 2 updates -> SUSPECTED only, no manager notification."""
    ctx = await setup_test_trip(db_session, trip_code="TRP-SCENARIO-3")
    dev_service = RouteDeviationService(db_session)

    # 0.004 degrees latitude is ~444 meters off corridor
    off_lat = 28.6040
    off_lng = 77.0500

    # 1st Outlier
    res1 = await dev_service.evaluate_position(
        driver_id=ctx["driver"].id, company_id=ctx["company"].id,
        latitude=off_lat, longitude=off_lng, accuracy=12.0,
        trip_id_hint=ctx["trip"].trip_id
    )
    assert res1["status"] == "SUSPECTED_DEVIATION"
    assert res1["distance_meters"] > 400.0

    # 2nd Outlier
    res2 = await dev_service.evaluate_position(
        driver_id=ctx["driver"].id, company_id=ctx["company"].id,
        latitude=off_lat, longitude=off_lng, accuracy=12.0,
        trip_id_hint=ctx["trip"].trip_id
    )
    assert res2["status"] == "SUSPECTED"

    # Verify event is in SUSPECTED status with consecutive_outliers = 2
    event = (await db_session.execute(
        select(RouteDeviationEvent).where(RouteDeviationEvent.trip_id == ctx["trip"].id)
    )).scalar_one()
    assert event.status == DeviationStatus.SUSPECTED
    assert event.consecutive_outliers == 2

    # CRITICAL: Verify NO manager notification has been triggered yet!
    notifs = (await db_session.execute(
        select(Notification).where(Notification.company_id == ctx["company"].id)
    )).scalars().all()
    assert len(notifs) == 0


@pytest.mark.asyncio
async def test_scenario_4_driver_deviating_beyond_200m_for_3_outliers_alert_generated(db_session):
    """Scenario 4: Driver deviating beyond 200m for 3 consecutive valid updates -> transitions to CONFIRMED & generates alert."""
    ctx = await setup_test_trip(db_session, trip_code="TRP-SCENARIO-4")
    dev_service = RouteDeviationService(db_session)

    off_lat = 28.6045  # ~500m off corridor
    off_lng = 77.0500

    with patch("routers.ws_driver.owner_ws_manager.broadcast_to_company", new_callable=AsyncMock) as mock_ws:
        # Pings 1, 2, 3
        await dev_service.evaluate_position(
            driver_id=ctx["driver"].id, company_id=ctx["company"].id,
            latitude=off_lat, longitude=off_lng, accuracy=10.0, trip_id_hint=ctx["trip"].trip_id
        )
        await dev_service.evaluate_position(
            driver_id=ctx["driver"].id, company_id=ctx["company"].id,
            latitude=off_lat, longitude=off_lng, accuracy=10.0, trip_id_hint=ctx["trip"].trip_id
        )
        res3 = await dev_service.evaluate_position(
            driver_id=ctx["driver"].id, company_id=ctx["company"].id,
            latitude=off_lat, longitude=off_lng, accuracy=10.0, trip_id_hint=ctx["trip"].trip_id
        )

        assert res3["status"] == "CONFIRMED_DEVIATION"

        # Verify persistent event in DB
        event = (await db_session.execute(
            select(RouteDeviationEvent).where(RouteDeviationEvent.trip_id == ctx["trip"].id)
        )).scalar_one()
        assert event.status == DeviationStatus.CONFIRMED
        assert event.consecutive_outliers >= 3
        assert event.severity in [DeviationSeverity.MEDIUM, DeviationSeverity.HIGH]

        # Verify persistent notification created for company owner
        notif = (await db_session.execute(
            select(Notification).where(
                Notification.company_id == ctx["company"].id,
                Notification.category == NotificationCategory.ALERT
            )
        )).scalar_one()
        assert "Route Deviation Detected" in notif.title
        assert "500" in notif.description or "meters" in notif.description
        assert ctx["trip"].trip_id in notif.description

        # Verify real-time WebSocket broadcast was triggered
        mock_ws.assert_called_once()
        ws_payload = mock_ws.call_args[0][1]
        assert ws_payload["type"] == "route_deviation"
        assert ws_payload["trip_id"] == ctx["trip"].trip_id
        assert ws_payload["driver_name"] == ctx["driver"].name


@pytest.mark.asyncio
async def test_scenario_5_driver_returning_within_150m_recovery_detected(db_session):
    """Scenario 5: Driver returns within 150m recovery threshold -> transitions to RETURNED_TO_ROUTE & generates recovery alert."""
    ctx = await setup_test_trip(db_session, trip_code="TRP-SCENARIO-5")
    dev_service = RouteDeviationService(db_session)

    # 1. Drive off-route for 3 pings to confirm deviation
    off_lat = 28.6050
    for _ in range(3):
        await dev_service.evaluate_position(
            driver_id=ctx["driver"].id, company_id=ctx["company"].id,
            latitude=off_lat, longitude=77.0500, accuracy=10.0, trip_id_hint=ctx["trip"].trip_id
        )

    # 2. Return within 150m (e.g. 28.6008, 77.0500 is ~88m from line)
    return_lat = 28.6008
    with patch("routers.ws_driver.owner_ws_manager.broadcast_to_company", new_callable=AsyncMock) as mock_ws:
        res = await dev_service.evaluate_position(
            driver_id=ctx["driver"].id, company_id=ctx["company"].id,
            latitude=return_lat, longitude=77.0500, accuracy=10.0, trip_id_hint=ctx["trip"].trip_id
        )

        assert res["status"] == "RETURNED_TO_ROUTE"

        # Verify event updated in DB
        event = (await db_session.execute(
            select(RouteDeviationEvent).where(RouteDeviationEvent.trip_id == ctx["trip"].id)
        )).scalar_one()
        assert event.status == DeviationStatus.RETURNED_TO_ROUTE
        assert event.resolved_at is not None

        # Verify recovery notification created
        rec_notif = (await db_session.execute(
            select(Notification).where(
                Notification.company_id == ctx["company"].id,
                Notification.title == "Vehicle Returned to Route"
            )
        )).scalar_one()
        assert ctx["trip"].trip_id in rec_notif.description

        # Verify WebSocket recovery event
        mock_ws.assert_called_once()
        ws_data = mock_ws.call_args[0][1]
        assert ws_data["type"] == "route_recovery"
        assert ws_data["trip_id"] == ctx["trip"].trip_id


@pytest.mark.asyncio
async def test_scenario_6_gps_accuracy_above_80m_ignored(db_session):
    """Scenario 6: GPS accuracy above 80m (e.g. 150m) does not increment consecutive outlier counter."""
    ctx = await setup_test_trip(db_session, trip_code="TRP-SCENARIO-6")
    dev_service = RouteDeviationService(db_session)

    off_lat = 28.6050

    # 1st ping: good accuracy creates suspected event
    await dev_service.evaluate_position(
        driver_id=ctx["driver"].id, company_id=ctx["company"].id,
        latitude=off_lat, longitude=77.0500, accuracy=15.0, trip_id_hint=ctx["trip"].trip_id
    )

    # 2nd ping: bad accuracy (100m > 80m limit)
    res_bad = await dev_service.evaluate_position(
        driver_id=ctx["driver"].id, company_id=ctx["company"].id,
        latitude=off_lat, longitude=77.0500, accuracy=100.0, trip_id_hint=ctx["trip"].trip_id
    )
    assert res_bad["status"] == "SUSPECTED"

    # Event consecutive outliers must still be 1!
    event = (await db_session.execute(
        select(RouteDeviationEvent).where(RouteDeviationEvent.trip_id == ctx["trip"].id)
    )).scalar_one()
    assert event.consecutive_outliers == 1
    assert event.status == DeviationStatus.SUSPECTED


@pytest.mark.asyncio
async def test_scenario_7_gps_noise_and_isolated_outlier_no_false_alert(db_session):
    """Scenario 7: Single isolated outlier followed by on-route ping silently resolves without manager alert."""
    ctx = await setup_test_trip(db_session, trip_code="TRP-SCENARIO-7")
    dev_service = RouteDeviationService(db_session)

    # 1. Single glitch ping 400m away
    await dev_service.evaluate_position(
        driver_id=ctx["driver"].id, company_id=ctx["company"].id,
        latitude=28.6040, longitude=77.0500, accuracy=10.0, trip_id_hint=ctx["trip"].trip_id
    )

    # 2. Next ping is back on route (< 150m)
    res = await dev_service.evaluate_position(
        driver_id=ctx["driver"].id, company_id=ctx["company"].id,
        latitude=28.6000, longitude=77.0600, accuracy=10.0, trip_id_hint=ctx["trip"].trip_id
    )
    assert res["status"] == "RESOLVED"

    # Event was resolved as false alarm
    event = (await db_session.execute(
        select(RouteDeviationEvent).where(RouteDeviationEvent.trip_id == ctx["trip"].id)
    )).scalar_one()
    assert event.status == DeviationStatus.RESOLVED

    # Zero alert notifications sent to manager!
    notifs = (await db_session.execute(
        select(Notification).where(Notification.company_id == ctx["company"].id)
    )).scalars().all()
    assert len(notifs) == 0


@pytest.mark.asyncio
async def test_scenario_8_missing_gps_updates_no_fabricated_deviation(db_session):
    """Scenario 8: Gaps in GPS pings do not fabricate positions or deviations."""
    ctx = await setup_test_trip(db_session, trip_code="TRP-SCENARIO-8")
    dev_service = RouteDeviationService(db_session)

    now = datetime.now(timezone.utc)
    # Ping 1 at T=0
    await dev_service.evaluate_position(
        driver_id=ctx["driver"].id, company_id=ctx["company"].id,
        latitude=28.6000, longitude=77.0200, accuracy=10.0,
        timestamp=now, trip_id_hint=ctx["trip"].trip_id
    )

    # Ping 2 at T=30 minutes later (e.g. tunnel or dead zone), but vehicle is on-route
    res = await dev_service.evaluate_position(
        driver_id=ctx["driver"].id, company_id=ctx["company"].id,
        latitude=28.6000, longitude=77.1500, accuracy=15.0,
        timestamp=now + timedelta(minutes=30), trip_id_hint=ctx["trip"].trip_id
    )

    assert res["status"] == "ON_ROUTE"
    events = (await db_session.execute(
        select(RouteDeviationEvent).where(RouteDeviationEvent.trip_id == ctx["trip"].id)
    )).scalars().all()
    assert len(events) == 0


@pytest.mark.asyncio
async def test_scenario_9_multiple_deviations_during_one_trip(db_session):
    """Scenario 9: Multiple separate deviations during one trip are independently recorded."""
    ctx = await setup_test_trip(db_session, trip_code="TRP-SCENARIO-9")
    dev_service = RouteDeviationService(db_session)

    # --- Deviation 1 ---
    for _ in range(3):
        await dev_service.evaluate_position(
            driver_id=ctx["driver"].id, company_id=ctx["company"].id,
            latitude=28.6050, longitude=77.0500, accuracy=10.0, trip_id_hint=ctx["trip"].trip_id
        )
    # Return 1
    await dev_service.evaluate_position(
        driver_id=ctx["driver"].id, company_id=ctx["company"].id,
        latitude=28.6000, longitude=77.0600, accuracy=10.0, trip_id_hint=ctx["trip"].trip_id
    )

    # --- Deviation 2 later along route ---
    for _ in range(3):
        await dev_service.evaluate_position(
            driver_id=ctx["driver"].id, company_id=ctx["company"].id,
            latitude=28.6060, longitude=77.1500, accuracy=10.0, trip_id_hint=ctx["trip"].trip_id
        )

    # Must have 2 distinct deviation events in DB
    events = (await db_session.execute(
        select(RouteDeviationEvent)
        .where(RouteDeviationEvent.trip_id == ctx["trip"].id)
        .order_by(RouteDeviationEvent.id)
    )).scalars().all()

    assert len(events) == 2
    assert events[0].status == DeviationStatus.RETURNED_TO_ROUTE
    assert events[1].status == DeviationStatus.CONFIRMED
    assert events[0].event_id != events[1].event_id


@pytest.mark.asyncio
async def test_scenario_10_completed_trip_no_new_deviation_alerts(db_session):
    """Scenario 10: Completed trips do not process or generate deviation alerts."""
    ctx = await setup_test_trip(db_session, trip_code="TRP-SCENARIO-10")
    ctx["trip"].status = TripStatus.COMPLETED
    await db_session.commit()

    dev_service = RouteDeviationService(db_session)
    res = await dev_service.evaluate_position(
        driver_id=ctx["driver"].id, company_id=ctx["company"].id,
        latitude=28.6080, longitude=77.0500, accuracy=10.0,
        trip_id_hint=ctx["trip"].trip_id
    )

    assert res["status"] == "NO_ACTIVE_TRIP"
    events = (await db_session.execute(
        select(RouteDeviationEvent).where(RouteDeviationEvent.trip_id == ctx["trip"].id)
    )).scalars().all()
    assert len(events) == 0


# ==============================================================================
# Phase 2: GPS Ingestion, Validation & Company Isolation Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_gps_coordinate_validation_and_future_timestamp_handling(db_session):
    """Validates coordinate bounds (-90 to 90, -180 to 180) and future timestamp clamping."""
    ctx = await setup_test_trip(db_session, trip_code="TRP-GPS-VAL")

    now = datetime.now(timezone.utc)
    future_ts = (now + timedelta(days=5)).isoformat()
    valid_ts = now.isoformat()

    payload = LocationBatchRequest(
        locations=[
            LocationPoint(latitude=28.60, longitude=77.05, accuracy=10.0, timestamp=valid_ts),
            LocationPoint(latitude=120.0, longitude=77.05, accuracy=10.0, timestamp=valid_ts),  # INVALID LAT
            LocationPoint(latitude=28.60, longitude=-200.0, accuracy=10.0, timestamp=valid_ts), # INVALID LNG
            LocationPoint(latitude=28.60, longitude=77.06, accuracy=10.0, timestamp=future_ts),  # FUTURE TS
        ]
    )

    res = await batch_upload_locations(payload=payload, driver=ctx["driver"], db=db_session)

    # 3 valid coordinates (1 valid + 1 future clamped = 2 valid saved)
    assert res["message"] == "2 locations recorded"

    # Query persisted points
    points = (await db_session.execute(
        select(DriverLocation).where(DriverLocation.driver_id == ctx["driver"].id)
    )).scalars().all()
    assert len(points) == 2


@pytest.mark.asyncio
async def test_company_isolation_on_location_data(db_session):
    """Verifies that location ingestion and deviation evaluation strictly enforce company isolation."""
    ctx1 = await setup_test_trip(db_session, company_name="Company Alpha", trip_code="TRP-ALPHA")
    ctx2 = await setup_test_trip(db_session, company_name="Company Beta", trip_code="TRP-BETA")

    dev_service = RouteDeviationService(db_session)

    # Driver from Company Alpha tries to evaluate with Company Beta ID -> must not find trip
    res = await dev_service.evaluate_position(
        driver_id=ctx1["driver"].id,
        company_id=ctx2["company"].id,  # MISMATCH
        latitude=28.60, longitude=77.05,
        trip_id_hint=ctx1["trip"].trip_id
    )
    assert res["status"] == "NO_ACTIVE_TRIP"

    # Ingest locations for Driver Alpha
    payload = LocationBatchRequest(
        locations=[
            LocationPoint(latitude=28.60, longitude=77.05, accuracy=10.0, timestamp=datetime.now(timezone.utc).isoformat())
        ]
    )
    await batch_upload_locations(payload=payload, driver=ctx1["driver"], db=db_session)

    # Verify Company Beta has zero locations
    beta_locs = (await db_session.execute(
        select(DriverLocation).where(DriverLocation.company_id == ctx2["company"].id)
    )).scalars().all()
    assert len(beta_locs) == 0


@pytest.mark.asyncio
async def test_notification_failure_does_not_corrupt_trip_state(db_session):
    """Verifies that WebSocket broadcast failure does not abort the database transaction or corrupt state."""
    ctx = await setup_test_trip(db_session, trip_code="TRP-FAIL-RESILIENT")
    dev_service = RouteDeviationService(db_session)

    # Force WebSocket broadcast to raise an exception
    with patch("routers.ws_driver.owner_ws_manager.broadcast_to_company", side_effect=RuntimeError("WebSocket Network Error")):
        for _ in range(3):
            await dev_service.evaluate_position(
                driver_id=ctx["driver"].id, company_id=ctx["company"].id,
                latitude=28.6050, longitude=77.0500, accuracy=10.0,
                trip_id_hint=ctx["trip"].trip_id
            )

        # Deviation event must still be confirmed and persisted in DB
        event = (await db_session.execute(
            select(RouteDeviationEvent).where(RouteDeviationEvent.trip_id == ctx["trip"].id)
        )).scalar_one()
        assert event.status == DeviationStatus.CONFIRMED

        # Notification must still be created in DB
        notif = (await db_session.execute(
            select(Notification).where(Notification.company_id == ctx["company"].id)
        )).scalar_one()
        assert notif is not None
