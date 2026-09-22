"""
FleetGuard Phase 6B — Dry-Run Fixture Generator

Creates a synthetic SQLite database with a single vehicle/driver test
and an accompanying ground-truth CSV. This allows testing the Phase 6B
calibration pipeline without polluting production.
"""

import asyncio
import csv
import json
import math
import os
import random
from datetime import datetime, timezone, timedelta

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import text
from database import Base
import models
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import JSONB, ARRAY, BYTEA, ENUM

@compiles(JSONB, 'sqlite')
def compile_jsonb_sqlite(type_, compiler, **kw):
    return 'JSON'

@compiles(ARRAY, 'sqlite')
def compile_array_sqlite(type_, compiler, **kw):
    return 'JSON'

@compiles(BYTEA, 'sqlite')
def compile_bytea_sqlite(type_, compiler, **kw):
    return 'BLOB'
from models.company import Company
from models.driver_domain import Driver
from models.vehicle_domain import Vehicle
from models.trip_domain import Trip
from models.location_tracking import VehicleLocation, LocationSource, VehicleCurrentLocation, LocationAlert
from models.intelligence_condition import IntelligenceCondition

DB_PATH = "phase6b_dryrun.db"
DB_URL = f"sqlite+aiosqlite:///{DB_PATH}"

# Simple lat/lon progression
START_LAT = 40.7128
START_LNG = -74.0060

def add_meters_to_lat_lng(lat, lng, dx_meters, dy_meters):
    r_earth = 6378137
    pi = math.pi
    new_lat = lat + (dy_meters / r_earth) * (180 / pi)
    new_lng = lng + (dx_meters / r_earth) * (180 / pi) / math.cos(lat * pi / 180)
    return new_lat, new_lng

async def main():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    engine = create_async_engine(DB_URL)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    now = datetime.now(timezone.utc) - timedelta(hours=1)
    
    # 1. Setup Base Data
    async with async_session() as session:
        company = Company(
            company_name="Phase 6B Dry Run",
            owner_name="Test Owner",
            mobile_number="5550000001",
            email="test@example.com",
            status="ACTIVE"
        )
        session.add(company)
        await session.flush()
        
        driver = Driver(
            company_id=company.id, 
            name="Dry Run Driver", 
            phone_number="5551234567",
            status="ACTIVE"
        )
        session.add(driver)
        await session.flush()
        
        vehicle = Vehicle(
            company_id=company.id, 
            registration_number="DRY-0001",
            status="ACTIVE"
        )
        session.add(vehicle)
        await session.flush()
        
        trip = Trip(company_id=company.id, vehicle_id=vehicle.id, driver_id=driver.id, status="ACTIVE", actual_start_time=now, trip_id="TRIP-001")
        session.add(trip)
        await session.commit()
        
        company_id = company.id
        driver_id = driver.id
        vehicle_id = vehicle.id
        
    print("Base data created.")
    
    # 2. Generate dual-GPS track & Ground Truth
    ground_truth = []
    locations = []
    
    def log_gt(event_name, ts):
        ground_truth.append({
            "timestamp": ts.isoformat(),
            "vehicle_id": vehicle_id,
            "driver_id": driver_id,
            "event_type": event_name,
            "notes": ""
        })
        
    current_time = now
    veh_lat, veh_lng = START_LAT, START_LNG
    phone_lat, phone_lng = START_LAT, START_LNG
    
    def emit_tick(dt, v_lat, v_lng, p_lat, p_lng, speed, emit_hw=True, emit_phone=True):
        if emit_hw:
            locations.append(VehicleLocation(
                vehicle_id=vehicle_id, company_id=company_id, driver_id=driver_id,
                latitude=v_lat + random.uniform(-0.00002, 0.00002), 
                longitude=v_lng + random.uniform(-0.00002, 0.00002),
                speed=speed, accuracy=5.0, timestamp=dt, source=LocationSource.HARDWARE_GPS
            ))
        if emit_phone:
            locations.append(VehicleLocation(
                vehicle_id=vehicle_id, company_id=company_id, driver_id=driver_id,
                latitude=p_lat + random.uniform(-0.00005, 0.00005), 
                longitude=p_lng + random.uniform(-0.00005, 0.00005),
                speed=speed, accuracy=15.0, timestamp=dt, source=LocationSource.PHONE_GPS
            ))

    # Phase 1: Driving Together (5 mins)
    log_gt("DRIVING_NORMAL_START", current_time)
    for _ in range(0, 300, 15):
        veh_lat, veh_lng = add_meters_to_lat_lng(veh_lat, veh_lng, 100, 100)
        phone_lat, phone_lng = veh_lat, veh_lng
        emit_tick(current_time, veh_lat, veh_lng, phone_lat, phone_lng, speed=15.0)
        current_time += timedelta(seconds=15)
        
    # Phase 2: Stationary, driver inside (5 mins)
    log_gt("STATIONARY_START", current_time)
    for _ in range(0, 300, 15):
        emit_tick(current_time, veh_lat, veh_lng, phone_lat, phone_lng, speed=0.0)
        current_time += timedelta(seconds=15)
        
    # Phase 3: Walk away 150m (10 mins)
    log_gt("DRIVER_EXIT_CAB", current_time)
    log_gt("WALK_150M", current_time + timedelta(seconds=90))
    for i in range(0, 600, 15):
        # Move phone 150m away, leave vehicle stationary (6 steps of 25m = 150m)
        if i < 90:
            phone_lat, phone_lng = add_meters_to_lat_lng(phone_lat, phone_lng, 25, 0)
        emit_tick(current_time, veh_lat, veh_lng, phone_lat, phone_lng, speed=0.0 if i > 90 else 1.5)
        current_time += timedelta(seconds=15)
        
    # Phase 4: Return (5 mins)
    log_gt("DRIVER_ENTER_CAB", current_time)
    phone_lat, phone_lng = veh_lat, veh_lng
    for _ in range(0, 300, 15):
        emit_tick(current_time, veh_lat, veh_lng, phone_lat, phone_lng, speed=0.0)
        current_time += timedelta(seconds=15)
        
    # Phase 5: Drive (5 mins)
    log_gt("DRIVING_NORMAL_START", current_time)
    for _ in range(0, 300, 15):
        veh_lat, veh_lng = add_meters_to_lat_lng(veh_lat, veh_lng, 100, 100)
        phone_lat, phone_lng = veh_lat, veh_lng
        emit_tick(current_time, veh_lat, veh_lng, phone_lat, phone_lng, speed=15.0)
        current_time += timedelta(seconds=15)
        
    # Insert locations
    async with async_session() as session:
        session.add_all(locations)
        await session.commit()
        
    print(f"Generated {len(locations)} location events.")
    
    # Save CSV
    with open("dryrun_ground_truth.csv", 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["timestamp", "vehicle_id", "driver_id", "event_type", "notes"])
        writer.writeheader()
        writer.writerows(ground_truth)
        
    print("Generated dryrun_ground_truth.csv")
    print("Fixture complete.")
    
if __name__ == "__main__":
    asyncio.run(main())
