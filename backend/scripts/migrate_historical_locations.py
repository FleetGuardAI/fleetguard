import asyncio
import os
import sys

# Add backend dir to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, and_, or_, desc, exists, func, delete
from database import async_session_factory
from models.location_tracking import DriverLocation, VehicleLocation, VehicleCurrentLocation
from models.vehicle_domain import Vehicle
from models.trip_domain import Trip

async def migrate_locations(batch_size=1000):
    audit = {
        "total": 0,
        "migrated_via_historical_trip": 0,
        "unmapped": 0,
        "invalid": 0,
        "already_migrated": 0,
        "company_mismatch": 0,
        "failed": 0
    }
    
    unmapped_ids = []
    failed_ids = []

    async with async_session_factory() as db:
        last_processed_id = 0
        
        # --- PHASE A: RAW DATA MIGRATION ---
        print("Starting raw data migration Phase A...")
        while True:
            locations = (await db.execute(
                select(DriverLocation)
                .where(DriverLocation.id > last_processed_id)
                .order_by(DriverLocation.id.asc())
                .limit(batch_size)
            )).scalars().all()

            if not locations:
                break

            for loc in locations:
                audit["total"] += 1
                last_processed_id = loc.id
                
                try:
                    # 1. Idempotency Check
                    is_migrated = (await db.execute(
                        select(exists().where(VehicleLocation.original_driver_location_id == loc.id))
                    )).scalar()
                    
                    if is_migrated:
                        audit["already_migrated"] += 1
                        continue

                    # 2. Reject invalid coords
                    if not (-90 <= loc.latitude <= 90) or not (-180 <= loc.longitude <= 180):
                        audit["invalid"] += 1
                        continue

                    # 3. Deterministic Trip Match
                    trip = (await db.execute(
                        select(Trip)
                        .where(
                            and_(
                                Trip.driver_id == loc.driver_id,
                                Trip.actual_start_time <= loc.timestamp,
                                or_(
                                    Trip.actual_end_time.is_(None),
                                    Trip.actual_end_time >= loc.timestamp
                                )
                            )
                        )
                        .order_by(desc(Trip.actual_start_time))
                        .limit(1)
                    )).scalar_one_or_none()

                    if not trip or not trip.vehicle_id:
                        audit["unmapped"] += 1
                        unmapped_ids.append(loc.id)
                        continue

                    # 4. Strict Company Consistency
                    vehicle = await db.get(Vehicle, trip.vehicle_id)
                    if not vehicle or loc.company_id != trip.company_id or loc.company_id != vehicle.company_id:
                        audit["company_mismatch"] += 1
                        unmapped_ids.append(loc.id)
                        continue
                    
                    # 5. Create and safely Flush VehicleLocation
                    v_loc = VehicleLocation(
                        vehicle_id=trip.vehicle_id,
                        driver_id=loc.driver_id,
                        company_id=loc.company_id,
                        latitude=loc.latitude,
                        longitude=loc.longitude,
                        speed=loc.speed,
                        heading=loc.heading,
                        accuracy=loc.accuracy,
                        timestamp=loc.timestamp,
                        source=loc.source,
                        original_driver_location_id=loc.id,
                        created_at=loc.created_at # Retain original ingestion time
                    )
                    db.add(v_loc)
                    
                    try:
                        async with db.begin_nested():
                            await db.flush()
                        audit["migrated_via_historical_trip"] += 1
                    except Exception as inner_e:
                        audit["failed"] += 1
                        failed_ids.append(loc.id)
                        print(f"Error flushing location {loc.id}: {inner_e}")

                except Exception as e:
                    audit["failed"] += 1
                    failed_ids.append(loc.id)
                    print(f"Error processing location {loc.id}: {e}")

            # Commit batch
            await db.commit()
            print(f"Processed {audit['total']} locations...")


        # --- PHASE B: STATE RECONSTRUCTION (Restartable UPSERT) ---
        print("Starting state reconstruction Phase B...")
        
        # Fetch max timestamp per vehicle and source
        subq = (
            select(
                VehicleLocation.vehicle_id,
                VehicleLocation.source,
                func.max(VehicleLocation.timestamp).label("max_ts")
            )
            .group_by(VehicleLocation.vehicle_id, VehicleLocation.source)
            .subquery()
        )
        
        latest_keys = (await db.execute(select(subq.c.vehicle_id, subq.c.source, subq.c.max_ts))).all()
        
        for v_id, source, max_ts in latest_keys:
            # Deterministic selection: max(timestamp) tie-broken by max(id)
            latest_loc = (await db.execute(
                select(VehicleLocation)
                .where(and_(
                    VehicleLocation.vehicle_id == v_id,
                    VehicleLocation.source == source,
                    VehicleLocation.timestamp == max_ts
                ))
                .order_by(desc(VehicleLocation.id))
                .limit(1)
            )).scalar_one()
            
            # Upsert Current Location state
            current_loc = VehicleCurrentLocation(
                vehicle_id=latest_loc.vehicle_id,
                source=latest_loc.source,
                latitude=latest_loc.latitude,
                longitude=latest_loc.longitude,
                speed=latest_loc.speed,
                heading=latest_loc.heading,
                accuracy=latest_loc.accuracy,
                last_timestamp=latest_loc.timestamp,
                last_received_at=latest_loc.created_at,
                driver_id=latest_loc.driver_id,
                device_id=latest_loc.device_id
            )
            await db.merge(current_loc)
            
            # Update Denormalized cache on Vehicle (only if newer)
            vehicle = await db.get(Vehicle, v_id)
            if vehicle and (not vehicle.last_location_at or vehicle.last_location_at < latest_loc.timestamp):
                vehicle.last_known_lat = latest_loc.latitude
                vehicle.last_known_lng = latest_loc.longitude
                vehicle.last_location_at = latest_loc.timestamp
                vehicle.last_location_source = latest_loc.source.value
                
        await db.commit()
        
        print("\n=== MIGRATION AUDIT REPORT ===")
        for k, v in audit.items():
            print(f"{k}: {v}")
        if unmapped_ids:
            print("\nUnmapped IDs sample (first 20):", unmapped_ids[:20])
        if failed_ids:
            print("Failed IDs:", failed_ids)
        print("==============================\n")

if __name__ == "__main__":
    asyncio.run(migrate_locations())
