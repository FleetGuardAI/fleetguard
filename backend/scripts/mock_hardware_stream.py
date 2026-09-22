import asyncio
import argparse
import random
import time
from datetime import datetime, timezone, timedelta
from sqlalchemy import text
from database import engine

# Constants for drift
MAX_DRIFT_METERS = 10.0

def add_meters(lat, lng, dx, dy):
    r_earth = 6378137
    import math
    new_lat = lat + (dy / r_earth) * (180 / math.pi)
    new_lng = lng + (dx / r_earth) * (180 / math.pi) / math.cos(lat * math.pi / 180)
    return new_lat, new_lng

async def get_latest_phone_location(vehicle_id: int):
    async with engine.connect() as conn:
        res = await conn.execute(
            text("""
                SELECT latitude, longitude, speed, heading
                FROM vehicle_locations
                WHERE vehicle_id = :vid AND source = 'PHONE_GPS'
                ORDER BY timestamp DESC
                LIMIT 1
            """),
            {"vid": vehicle_id}
        )
        row = res.fetchone()
        return row

async def inject_hardware_gps(vehicle_id: int, lat: float, lng: float, speed: float, heading: float, driver_id: int, company_id: int):
    # Add random drift
    dx = random.uniform(-MAX_DRIFT_METERS, MAX_DRIFT_METERS)
    dy = random.uniform(-MAX_DRIFT_METERS, MAX_DRIFT_METERS)
    drifted_lat, drifted_lng = add_meters(lat, lng, dx, dy)
    
    # Random hardware accuracy
    accuracy = random.uniform(2.0, 5.0)
    
    timestamp = datetime.now(timezone.utc)
    
    async with engine.begin() as conn:
        await conn.execute(
            text("""
                INSERT INTO vehicle_locations 
                (vehicle_id, driver_id, company_id, latitude, longitude, speed, heading, accuracy, timestamp, source, event_fingerprint, created_at)
                VALUES (:vid, :did, :cid, :lat, :lng, :spd, :hdg, :acc, :ts, 'HARDWARE_GPS', :fingerprint, :created)
            """),
            {
                "vid": vehicle_id,
                "did": driver_id,
                "cid": company_id,
                "lat": drifted_lat,
                "lng": drifted_lng,
                "spd": speed,
                "hdg": heading,
                "acc": accuracy,
                "ts": timestamp,
                "fingerprint": f"mock_hw_{timestamp.timestamp()}",
                "created": timestamp
            }
        )
    print(f"[{timestamp.isoformat()}] Injected mock HARDWARE_GPS for Vehicle {vehicle_id} at {drifted_lat:.6f}, {drifted_lng:.6f}")

async def main():
    parser = argparse.ArgumentParser(description="Mock Hardware GPS Stream")
    parser.add_argument("--vehicle-id", type=int, default=9999)
    parser.add_argument("--driver-id", type=int, default=9999)
    parser.add_argument("--company-id", type=int, default=9999)
    parser.add_argument("--interval", type=int, default=30, help="Seconds between GPS pings")
    args = parser.parse_args()
    
    print(f"Starting mock HARDWARE_GPS stream for Vehicle {args.vehicle_id}...")
    print(f"Will ping every {args.interval} seconds based on the latest PHONE_GPS location.")
    print("Press Ctrl+C to stop.")
    
    while True:
        try:
            latest = await get_latest_phone_location(args.vehicle_id)
            if latest:
                lat, lng, speed, heading = latest
                # Handle possible None values in latest
                if speed is None: speed = 0.0
                if heading is None: heading = 0.0
                
                await inject_hardware_gps(args.vehicle_id, lat, lng, speed, heading, args.driver_id, args.company_id)
            else:
                print(f"[{datetime.now().isoformat()}] No PHONE_GPS found for Vehicle {args.vehicle_id}. Waiting for driver app to connect...")
        except Exception as e:
            print(f"Error injecting GPS: {e}")
            
        await asyncio.sleep(args.interval)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopped mock hardware stream.")
