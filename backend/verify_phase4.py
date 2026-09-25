"""
Phase 4 Verification Script
Tests deterministic logic, condition persistence, and anomaly lifecycle.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from database import async_session_factory
from models.vehicle_domain import Vehicle, VehicleStatus
from models.driver_domain import Driver, EmploymentStatus, DutyStatus
from models.trip_domain import Trip, TripStatus
from models.location_tracking import VehicleCurrentLocation, LocationSource, LocationAlert, AlertType
from models.intelligence_condition import IntelligenceCondition, ConditionType, ConditionStatus
from services.driver_vehicle_intelligence import DriverVehicleIntelligenceService
from services.driver_vehicle_intelligence_config import intelligence_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("verify_phase4")

async def setup_test_data(db: AsyncSession) -> tuple:
    # Cleanup previous tests
    await db.execute(text("DELETE FROM intelligence_conditions"))
    await db.execute(text("DELETE FROM location_alerts"))
    await db.execute(text("DELETE FROM vehicle_current_locations"))
    await db.execute(text("DELETE FROM trips"))
    await db.flush()

    # Get or create company
    company_id = (await db.execute(select(text("id FROM companies LIMIT 1")))).scalar()
    if not company_id:
        company_id = (await db.execute(text("INSERT INTO companies (name) VALUES ('Test Corp') RETURNING id"))).scalar()

    # Get or create driver
    driver_id = (await db.execute(select(text("id FROM drivers WHERE company_id = :cid LIMIT 1")).params(cid=company_id))).scalar()
    if not driver_id:
        driver = Driver(company_id=company_id, name="Test Driver", employment_status=EmploymentStatus.FULL_TIME, duty_status=DutyStatus.ON_DUTY, phone_number="123456789")
        db.add(driver)
        await db.flush()
        driver_id = driver.id

    # Get or create vehicle
    vehicle_id = (await db.execute(select(text("id FROM vehicles WHERE company_id = :cid LIMIT 1")).params(cid=company_id))).scalar()
    if not vehicle_id:
        vehicle = Vehicle(company_id=company_id, registration_number="TEST-001", status=VehicleStatus.ACTIVE, assigned_driver_id=driver_id)
        db.add(vehicle)
        await db.flush()
        vehicle_id = vehicle.id

    # Assign driver to vehicle
    await db.execute(text("UPDATE vehicles SET assigned_driver_id = :did WHERE id = :vid").params(did=driver_id, vid=vehicle_id))

    # Create trip
    trip = Trip(trip_id="T1", company_id=company_id, driver_id=driver_id, vehicle_id=vehicle_id, status=TripStatus.IN_PROGRESS)
    db.add(trip)
    await db.commit()

    return company_id, driver_id, vehicle_id, trip.id

async def test_distance_and_separation(db: AsyncSession, company_id, vehicle_id, driver_id):
    logger.info("Running Test: Distance & Separation (Condition Start)")
    now = datetime.now(timezone.utc)
    
    # Phone GPS at origin
    loc_phone = VehicleCurrentLocation(
        vehicle_id=vehicle_id, source=LocationSource.PHONE_GPS,
        latitude=40.7128, longitude=-74.0060, speed=0.0, accuracy=5.0,
        last_timestamp=now, last_received_at=now, driver_id=driver_id
    )
    # Hardware GPS 500m away
    # roughly 0.0045 degrees lat = 500m
    loc_hw = VehicleCurrentLocation(
        vehicle_id=vehicle_id, source=LocationSource.HARDWARE_GPS,
        latitude=40.7173, longitude=-74.0060, speed=0.0, accuracy=5.0,
        last_timestamp=now, last_received_at=now
    )
    db.add_all([loc_phone, loc_hw])
    await db.commit()

    service = DriverVehicleIntelligenceService(db)
    signals = await service.compute_signals(vehicle_id, company_id)
    
    assert signals.distance_meters > 400.0, f"Distance calculated as {signals.distance_meters}"
    assert signals.proximity_state.value == "AWAY_FROM_VEHICLE", f"Proximity: {signals.proximity_state}"
    
    await service.process_conditions(signals, now)
    await db.commit()
    
    # Verify Condition Created
    cond_query = select(IntelligenceCondition).where(IntelligenceCondition.condition_type == ConditionType.POTENTIAL_DRIVER_VEHICLE_SEPARATION)
    cond = (await db.execute(cond_query)).scalars().first()
    assert cond is not None, "Condition should be created"
    assert cond.status == ConditionStatus.ACTIVE
    assert cond.alert_id is None, "Alert should not be created yet"
    logger.info("✅ Distance & Separation logic passed")

async def test_duration_threshold_and_duplicate_eval(db: AsyncSession, company_id, vehicle_id):
    logger.info("Running Test: Duration Threshold & Duplicate Evaluation")
    
    # Fast-forward time to simulate threshold met
    future = datetime.now(timezone.utc) + timedelta(seconds=intelligence_config.MINIMUM_ANOMALY_DURATION_SECONDS + 10)
    
    service = DriverVehicleIntelligenceService(db)
    signals = await service.compute_signals(vehicle_id, company_id)
    
    # Eval 1
    await service.process_conditions(signals, future)
    await db.commit()
    
    cond_query = select(IntelligenceCondition).where(IntelligenceCondition.condition_type == ConditionType.POTENTIAL_DRIVER_VEHICLE_SEPARATION)
    cond = (await db.execute(cond_query)).scalars().first()
    
    assert cond.alert_id is not None, "Alert should be spawned"
    
    alert_query = select(LocationAlert).where(LocationAlert.id == cond.alert_id)
    alert = (await db.execute(alert_query)).scalars().first()
    assert alert.alert_type == AlertType.DRIVER_VEHICLE_SEPARATION
    assert alert.is_resolved == False
    
    # Eval 2 (Duplicate Eval)
    await service.process_conditions(signals, future)
    await db.commit()
    
    alert_count = (await db.execute(select(func.count()).select_from(LocationAlert).where(LocationAlert.alert_type == AlertType.DRIVER_VEHICLE_SEPARATION))).scalar()
    assert alert_count == 1, f"Expected 1 separation alert, got {alert_count}. Duplicate eval failed."
    logger.info("✅ Duration Threshold & Idempotency passed")

async def test_time_skew(db: AsyncSession, company_id, vehicle_id):
    logger.info("Running Test: Time Skew")
    # Make phone GPS stale
    await db.execute(
        text("UPDATE vehicle_current_locations SET last_timestamp = :ts WHERE source = 'PHONE_GPS'"),
        {"ts": datetime.now(timezone.utc) - timedelta(seconds=500)}
    )
    await db.commit()
    
    service = DriverVehicleIntelligenceService(db)
    signals = await service.compute_signals(vehicle_id, company_id)
    
    assert signals.is_temporally_compatible == False
    assert signals.proximity_state.value == "UNKNOWN"
    assert signals.movement_state.value == "UNKNOWN"
    logger.info("✅ Time Skew passed")

async def run_all():
    async with async_session_factory() as db:
        try:
            c, d, v, t = await setup_test_data(db)
            await test_distance_and_separation(db, c, v, d)
            await test_duration_threshold_and_duplicate_eval(db, c, v)
            await test_time_skew(db, c, v)
            logger.info("🎉 All Phase 4 Unit/Integration tests passed!")
        except Exception as e:
            logger.error(f"❌ Test Failed: {e}")
            raise e

if __name__ == "__main__":
    from sqlalchemy.sql import func
    asyncio.run(run_all())
