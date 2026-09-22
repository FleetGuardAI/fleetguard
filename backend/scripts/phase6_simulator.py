"""
Phase 6A: Intelligence Logic Validation Simulator

Generates synthetic dual-source GPS telemetry to validate the 
deterministic Driver/Vehicle Intelligence Engine under 17 scenarios.
"""

import asyncio
import json
import logging
import random
import math
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
from typing import List, Optional

from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import engine, async_session_factory
from models.vehicle_domain import Vehicle, VehicleStatus
from models.driver_domain import Driver, EmploymentStatus, DutyStatus
from models.trip_domain import Trip, TripStatus
from models.location_tracking import VehicleCurrentLocation, LocationSource, LocationAlert
from models.intelligence_condition import IntelligenceCondition, ConditionStatus
from services.driver_vehicle_intelligence import DriverVehicleIntelligenceService
from services.driver_vehicle_intelligence_config import intelligence_config

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger("phase6_simulator")

# Configurable Simulator Parameters
class SimConfig:
    PHONE_ACCURACY_MIN = 5.0
    PHONE_ACCURACY_MAX = 25.0
    PHONE_UPDATE_INTERVAL = 15
    
    HARDWARE_ACCURACY_MIN = 2.0
    HARDWARE_ACCURACY_MAX = 10.0
    HARDWARE_UPDATE_INTERVAL = 30

def add_meters_to_latlon(lat, lon, dy, dx):
    """Add dy (meters N) and dx (meters E) to lat/lon"""
    r_earth = 6371000
    new_lat = lat + (dy / r_earth) * (180 / math.pi)
    new_lon = lon + (dx / r_earth) * (180 / math.pi) / math.cos(lat * math.pi / 180)
    return new_lat, new_lon

def generate_noise(acc_min, acc_max):
    # Random radial noise based on accuracy
    acc = random.uniform(acc_min, acc_max)
    angle = random.uniform(0, 2 * math.pi)
    dist = random.uniform(0, acc)
    dy = math.sin(angle) * dist
    dx = math.cos(angle) * dist
    return dy, dx, acc

@dataclass
class SimEvent:
    scenario: str
    time: datetime
    phone_lat: Optional[float]
    phone_lon: Optional[float]
    phone_speed: Optional[float]
    phone_acc: Optional[float]
    hw_lat: Optional[float]
    hw_lon: Optional[float]
    hw_speed: Optional[float]
    hw_acc: Optional[float]
    phone_delay: float = 0.0
    hw_delay: float = 0.0

class ScenarioGenerator:
    def __init__(self):
        self.start_lat = 40.7128
        self.start_lon = -74.0060
        self.base_time = datetime.now(timezone.utc) - timedelta(hours=1)
        
    def _gen_stream(self, duration_sec, p_int, h_int, p_drift_fn, h_drift_fn, speed_fn=None):
        events = []
        for t in range(0, duration_sec, 5): # Tick every 5s
            if t % p_int == 0 or t % h_int == 0:
                ts = self.base_time + timedelta(seconds=t)
                dy_p, dx_p, dy_h, dx_h = p_drift_fn(t), p_drift_fn(t), h_drift_fn(t), h_drift_fn(t)
                speed = speed_fn(t) if speed_fn else 0.0
                
                has_p = (t % p_int == 0)
                has_h = (t % h_int == 0)
                
                p_dy_noise, p_dx_noise, p_acc = generate_noise(SimConfig.PHONE_ACCURACY_MIN, SimConfig.PHONE_ACCURACY_MAX)
                h_dy_noise, h_dx_noise, h_acc = generate_noise(SimConfig.HARDWARE_ACCURACY_MIN, SimConfig.HARDWARE_ACCURACY_MAX)
                
                p_lat, p_lon = add_meters_to_latlon(self.start_lat, self.start_lon, dy_p + p_dy_noise, dx_p + p_dx_noise) if has_p else (None, None)
                h_lat, h_lon = add_meters_to_latlon(self.start_lat, self.start_lon, dy_h + h_dy_noise, dx_h + h_dx_noise) if has_h else (None, None)
                
                events.append({
                    'time': ts,
                    'phone': {'lat': p_lat, 'lon': p_lon, 'speed': speed, 'acc': p_acc} if has_p else None,
                    'hw': {'lat': h_lat, 'lon': h_lon, 'speed': speed, 'acc': h_acc} if has_h else None
                })
        self.base_time += timedelta(seconds=duration_sec + 60) # advance base time
        return events

    def get_scenario_1_normal_driving(self):
        # Moving at 15 m/s (~54 km/h) together
        return self._gen_stream(120, SimConfig.PHONE_UPDATE_INTERVAL, SimConfig.HARDWARE_UPDATE_INTERVAL,
                                lambda t: t * 15, lambda t: t * 15, lambda t: 15.0)

    def get_scenario_2_stationary(self):
        # Parked, GPS drifts normally
        return self._gen_stream(120, SimConfig.PHONE_UPDATE_INTERVAL, SimConfig.HARDWARE_UPDATE_INTERVAL,
                                lambda t: 0, lambda t: 0, lambda t: 0.0)

    def get_scenario_3_brief_exit(self):
        # Driver walks 50m away for 60s then returns
        def p_drift(t):
            if t < 30: return 0
            if t < 90: return 50
            return 0
        return self._gen_stream(120, SimConfig.PHONE_UPDATE_INTERVAL, SimConfig.HARDWARE_UPDATE_INTERVAL,
                                p_drift, lambda t: 0, lambda t: 0.0)

    def get_scenario_4_walk_away(self):
        # Driver walks away progressively up to 500m
        return self._gen_stream(300, SimConfig.PHONE_UPDATE_INTERVAL, SimConfig.HARDWARE_UPDATE_INTERVAL,
                                lambda t: min(t * 2, 500), lambda t: 0, lambda t: 0.0)

    def get_scenario_5_persistent_separation(self):
        # Driver is 600m away for 6 minutes (Alert expected)
        return self._gen_stream(360, SimConfig.PHONE_UPDATE_INTERVAL, SimConfig.HARDWARE_UPDATE_INTERVAL,
                                lambda t: 600, lambda t: 0, lambda t: 0.0)

    def get_scenario_6_driver_returns(self):
        # Following persistent separation, driver returns
        # Requires scenario 5 to run first in the same continuous block
        return self._gen_stream(120, SimConfig.PHONE_UPDATE_INTERVAL, SimConfig.HARDWARE_UPDATE_INTERVAL,
                                lambda t: max(600 - t*10, 0), lambda t: 0, lambda t: 0.0)

    def get_scenario_7_vehicle_moves_driver_stat(self):
        # Truck drives away (15 m/s), phone stays
        return self._gen_stream(360, SimConfig.PHONE_UPDATE_INTERVAL, SimConfig.HARDWARE_UPDATE_INTERVAL,
                                lambda t: 0, lambda t: t * 15, speed_fn=lambda t: 15.0) # Hardware gets 15m/s

    def get_scenario_8_source_divergence(self):
        # Hardware jumps 600m away
        return self._gen_stream(240, SimConfig.PHONE_UPDATE_INTERVAL, SimConfig.HARDWARE_UPDATE_INTERVAL,
                                lambda t: 0, lambda t: 600 if t > 30 else 0, lambda t: 0.0)

    def get_scenario_9_phone_outage(self):
        # Phone drops off
        def p_drift(t): return 0
        events = self._gen_stream(360, SimConfig.PHONE_UPDATE_INTERVAL, SimConfig.HARDWARE_UPDATE_INTERVAL,
                                  p_drift, lambda t: 0, lambda t: 0.0)
        for e in events:
            if (e['time'] - events[0]['time']).total_seconds() > 60:
                e['phone'] = None
        return events

    def get_scenario_10_hardware_outage(self):
        # Hardware drops off
        events = self._gen_stream(360, SimConfig.PHONE_UPDATE_INTERVAL, SimConfig.HARDWARE_UPDATE_INTERVAL,
                                  lambda t: 0, lambda t: 0, lambda t: 0.0)
        for e in events:
            if (e['time'] - events[0]['time']).total_seconds() > 60:
                e['hw'] = None
        return events
        
    def get_scenario_13_jitter(self):
        # High jitter (up to 40m noise) but driver in truck
        events = self._gen_stream(180, SimConfig.PHONE_UPDATE_INTERVAL, SimConfig.HARDWARE_UPDATE_INTERVAL,
                                  lambda t: 0, lambda t: 0, lambda t: 0.0)
        for e in events:
            if e['phone']: e['phone']['acc'] = 40.0
            if e['hw']: e['hw']['acc'] = 40.0
        return events
        
    def get_scenario_14_multipath_jumps(self):
        # Urban multipath: occasional 150m jumps that resolve next tick
        events = self._gen_stream(180, SimConfig.PHONE_UPDATE_INTERVAL, SimConfig.HARDWARE_UPDATE_INTERVAL,
                                  lambda t: 0, lambda t: 0, lambda t: 0.0)
        for i, e in enumerate(events):
            if i % 10 == 0 and e['phone']: 
                e['phone']['lat'], e['phone']['lon'] = add_meters_to_latlon(e['phone']['lat'], e['phone']['lon'], 150, 150)
        return events

    def get_scenario_17_no_false_alert(self):
        # Driver and truck together, phone GPS occasionally spikes 30-100m separation
        events = self._gen_stream(600, SimConfig.PHONE_UPDATE_INTERVAL, SimConfig.HARDWARE_UPDATE_INTERVAL,
                                  lambda t: 0, lambda t: 0, lambda t: 0.0)
        for i, e in enumerate(events):
            if i % 15 == 0 and e['phone']: 
                # Random 80m spike
                e['phone']['lat'], e['phone']['lon'] = add_meters_to_latlon(e['phone']['lat'], e['phone']['lon'], 80, 0)
        return events


async def setup_db(db: AsyncSession):
    await db.execute(text("DELETE FROM intelligence_conditions"))
    await db.execute(text("DELETE FROM location_alerts"))
    await db.execute(text("DELETE FROM vehicle_current_locations"))
    await db.execute(text("DELETE FROM trips"))
    await db.flush()

    company_id = (await db.execute(select(text("id FROM companies LIMIT 1")))).scalar()
    if not company_id:
        company_id = (await db.execute(text("INSERT INTO companies (name) VALUES ('Test Corp') RETURNING id"))).scalar()

    driver_id = (await db.execute(select(text("id FROM drivers WHERE company_id = :cid LIMIT 1")).params(cid=company_id))).scalar()
    if not driver_id:
        driver = Driver(company_id=company_id, name="Test Driver", employment_status=EmploymentStatus.FULL_TIME, duty_status=DutyStatus.ON_DUTY, phone_number="123456789")
        db.add(driver)
        await db.flush()
        driver_id = driver.id

    vehicle_id = (await db.execute(select(text("id FROM vehicles WHERE company_id = :cid LIMIT 1")).params(cid=company_id))).scalar()
    if not vehicle_id:
        vehicle = Vehicle(company_id=company_id, registration_number="TEST-001", status=VehicleStatus.ACTIVE, assigned_driver_id=driver_id)
        db.add(vehicle)
        await db.flush()
        vehicle_id = vehicle.id

    await db.execute(text("UPDATE vehicles SET assigned_driver_id = :did WHERE id = :vid").params(did=driver_id, vid=vehicle_id))
    trip = Trip(trip_id="T1", company_id=company_id, driver_id=driver_id, vehicle_id=vehicle_id, status=TripStatus.IN_PROGRESS)
    db.add(trip)
    await db.commit()

    return company_id, vehicle_id, driver_id

async def run_scenario(scenario_name: str, events: list, db: AsyncSession, company_id, vehicle_id, driver_id, retain_state=False):
    logger.info(f"--- Running Scenario: {scenario_name} ---")
    
    if not retain_state:
        await db.execute(text("DELETE FROM intelligence_conditions"))
        await db.execute(text("DELETE FROM location_alerts"))
        await db.execute(text("DELETE FROM vehicle_current_locations"))
        await db.commit()

    service = DriverVehicleIntelligenceService(db)
    
    alerts_spawned = set()
    alerts_resolved = set()
    conditions_opened = set()
    
    for evt in events:
        ts = evt['time']
        
        for src_name, key in [('PHONE_GPS', 'phone'), ('HARDWARE_GPS', 'hw')]:
            data = evt[key]
            if data:
                stmt = select(VehicleCurrentLocation).where(
                    VehicleCurrentLocation.vehicle_id == vehicle_id,
                    VehicleCurrentLocation.source == src_name
                )
                vcl = (await db.execute(stmt)).scalars().first()
                if not vcl:
                    vcl = VehicleCurrentLocation(vehicle_id=vehicle_id, source=src_name, driver_id=driver_id if key == 'phone' else None)
                    db.add(vcl)
                vcl.latitude = data['lat']
                vcl.longitude = data['lon']
                vcl.speed = data.get('speed', 0.0)
                vcl.accuracy = data.get('acc', 10.0)
                vcl.last_timestamp = ts
                vcl.last_received_at = ts
                await db.commit()

        # Evaluate signals and condition lifecycle
        signals = await service.compute_signals(vehicle_id, company_id, now=ts)
        await service.process_conditions(signals, now=ts)
        await db.commit()
        
        # Track active alerts & conditions
        alerts = (await db.execute(select(LocationAlert).where(LocationAlert.driver_id == driver_id))).scalars().all()
        for a in alerts:
            alerts_spawned.add(a.id)
            # The column is is_resolved, not resolved_at
            if getattr(a, 'is_resolved', False):
                alerts_resolved.add(a.id)
                
        conds = (await db.execute(select(IntelligenceCondition).where(IntelligenceCondition.vehicle_id == vehicle_id))).scalars().all()
        for c in conds:
            conditions_opened.add(c.id)

    res = {
        'scenario': scenario_name,
        'events_count': len(events),
        'conditions_opened': len(conditions_opened),
        'alerts_spawned': len(alerts_spawned),
        'alerts_resolved': len(alerts_resolved)
    }
    logger.info(f"Result {scenario_name}: {res}")
    return res

async def main():
    logger.info("Initializing Phase 6A Simulator")
    async with async_session_factory() as db:
        company_id, vehicle_id, driver_id = await setup_db(db)
        logger.info(f"Ready. Vehicle: {vehicle_id}")
        
        gen = ScenarioGenerator()
        scenarios = [
            ("1. Normal Driving", gen.get_scenario_1_normal_driving()),
            ("2. Stationary", gen.get_scenario_2_stationary()),
            ("3. Brief Exit", gen.get_scenario_3_brief_exit()),
            ("4. Walk Away", gen.get_scenario_4_walk_away()),
            ("5. Persistent Separation", gen.get_scenario_5_persistent_separation()),
            ("6. Driver Returns", gen.get_scenario_6_driver_returns()), # Runs isolated here, but testing standalone return
            ("7. Vehicle Moves, Driver Stat", gen.get_scenario_7_vehicle_moves_driver_stat()),
            ("8. Source Divergence", gen.get_scenario_8_source_divergence()),
            ("9. Phone Outage", gen.get_scenario_9_phone_outage()),
            ("10. Hardware Outage", gen.get_scenario_10_hardware_outage()),
            ("13. Jitter", gen.get_scenario_13_jitter()),
            ("14. Multipath Jumps", gen.get_scenario_14_multipath_jumps()),
            ("17. No False Alert (Noisy)", gen.get_scenario_17_no_false_alert()),
        ]
        
        results = []
        for name, events in scenarios:
            res = await run_scenario(name, events, db, company_id, vehicle_id, driver_id)
            results.append(res)
            
        with open("phase6a_results.json", "w") as f:
            json.dump(results, f, indent=2)
            
    logger.info("Phase 6A Simulator complete. Results written to phase6a_results.json.")

if __name__ == "__main__":
    asyncio.run(main())
