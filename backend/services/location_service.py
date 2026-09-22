import hashlib
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional

from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException

from models.location_tracking import VehicleLocation, VehicleCurrentLocation, LocationSource
from models.trip_domain import Trip
from models.vehicle_domain import Vehicle
from models.driver_domain import Driver
from models.asset_domain import Asset, AssetType
from models.operational_event import OperationalEvent, EventType, EntityType, CaptureMethod
from schemas.operational_event import OperationalEventResponse
from schemas.telematics import NormalizedHardwareEvent

logger = logging.getLogger("fleetguard.tracking.service")

# Configurable freshness window for live assignment fallback
LIVE_LOCATION_ASSIGNMENT_WINDOW_MINUTES = 30


class LocationService:
    @staticmethod
    def _generate_fingerprint(
        source: str, 
        identity_id: int, 
        timestamp: datetime, 
        latitude: float, 
        longitude: float
    ) -> str:
        """
        Generates a canonical, deterministic fingerprint for idempotency.
        """
        # Normalize to UTC and ISO8601
        utc_ts = timestamp.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        
        # Canonical representation of coordinates (e.g. 28.610000)
        # 6 decimal places is ~0.11m precision, standard for GPS
        lat_str = f"{latitude:.6f}"
        lng_str = f"{longitude:.6f}"
        
        canonical_str = f"{source}:{identity_id}:{utc_ts}:{lat_str}:{lng_str}"
        return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()

    @staticmethod
    async def _resolve_vehicle_id(
        db: AsyncSession, 
        driver_id: int, 
        timestamp: datetime,
    ) -> tuple[Optional[int], str]:
        """
        Resolves the correct vehicle ID for a given event timestamp.
        Returns (vehicle_id, resolution_status)
        """
        # 1. Trip Coverage
        trip_query = select(Trip).where(
            and_(
                Trip.driver_id == driver_id,
                Trip.actual_start_time <= timestamp,
                or_(Trip.actual_end_time >= timestamp, Trip.actual_end_time.is_(None))
            )
        )
        trip_result = await db.execute(trip_query)
        trips = trip_result.scalars().all()

        if len(trips) == 1:
            return trips[0].vehicle_id, "resolved_via_trip"
        elif len(trips) > 1:
            return None, "ambiguous_vehicle"

        # 2. Current Assignment Fallback (Only for live/recent events)
        now = datetime.now(timezone.utc)
        time_diff = now - timestamp
        if time_diff <= timedelta(minutes=LIVE_LOCATION_ASSIGNMENT_WINDOW_MINUTES) and time_diff >= timedelta(minutes=-5):
            # It's a recent event (allowing up to 5 mins future drift)
            vehicle_query = select(Vehicle).where(Vehicle.assigned_driver_id == driver_id)
            vehicle_result = await db.execute(vehicle_query)
            vehicle = vehicle_result.scalars().first()
            if vehicle:
                return vehicle.id, "resolved_via_assignment"

        # 3. Unresolvable
        return None, "unresolved_vehicle"

    @classmethod
    async def process_batch(
        cls, 
        db: AsyncSession, 
        driver_id: int, 
        company_id: int, 
        locations: List[Any], 
        source: str = LocationSource.PHONE_GPS.value
    ) -> Dict[str, Any]:
        """
        Processes a batch of location events transactionally.
        """
        result = {
            "accepted": 0,
            "duplicates": 0,
            "rejected": 0,
            "items": []
        }

        for loc in locations:
            item_status = {"timestamp": loc.timestamp}
            
            try:
                ts = datetime.fromisoformat(loc.timestamp.replace("Z", "+00:00"))
            except ValueError:
                item_status["status"] = "invalid"
                item_status["reason"] = "invalid_timestamp"
                result["rejected"] += 1
                result["items"].append(item_status)
                continue

            # Validate coordinates
            if not (-90 <= loc.latitude <= 90) or not (-180 <= loc.longitude <= 180):
                item_status["status"] = "invalid"
                item_status["reason"] = "invalid_coordinates"
                result["rejected"] += 1
                result["items"].append(item_status)
                continue

            # Resolve Vehicle
            vehicle_id, resolution_status = await cls._resolve_vehicle_id(db, driver_id, ts)
            if not vehicle_id:
                item_status["status"] = resolution_status
                if resolution_status == "ambiguous_vehicle":
                    item_status["reason"] = "Multiple overlapping trips"
                else:
                    item_status["reason"] = "No trip or recent assignment"
                result["rejected"] += 1
                result["items"].append(item_status)
                continue

            # Verify Tenant Isolation
            vehicle = await db.get(Vehicle, vehicle_id)
            if not vehicle or vehicle.company_id != company_id:
                item_status["status"] = "invalid"
                item_status["reason"] = "tenant_violation_or_not_found"
                result["rejected"] += 1
                result["items"].append(item_status)
                continue

            # Generate Fingerprint
            fingerprint = cls._generate_fingerprint(
                source=source,
                identity_id=driver_id,
                timestamp=ts,
                latitude=loc.latitude,
                longitude=loc.longitude
            )
            
            # Prepare metadata
            metadata = {}
            if getattr(loc, "battery_percent", None) is not None:
                metadata["battery_percent"] = loc.battery_percent
            if getattr(loc, "activity_state", None) is not None:
                metadata["activity_state"] = loc.activity_state

            # Savepoint transaction for this specific event
            try:
                async with db.begin_nested():
                    # 1. Insert into VehicleLocation
                    db_loc = VehicleLocation(
                        vehicle_id=vehicle_id,
                        driver_id=driver_id,
                        company_id=company_id,
                        latitude=loc.latitude,
                        longitude=loc.longitude,
                        speed=getattr(loc, "speed", None),
                        heading=getattr(loc, "heading", None),
                        accuracy=getattr(loc, "accuracy", None),
                        timestamp=ts,
                        source=LocationSource(source),
                        event_fingerprint=fingerprint,
                        source_metadata=metadata if metadata else None
                    )
                    db.add(db_loc)
                    await db.flush() # Force DB check for constraint
                    
                    # 2. Check and Update Current State
                    current_query = select(VehicleCurrentLocation).where(
                        and_(
                            VehicleCurrentLocation.vehicle_id == vehicle_id,
                            VehicleCurrentLocation.source == source
                        )
                    ).with_for_update()
                    current_result = await db.execute(current_query)
                    current_loc = current_result.scalars().first()

                    is_newer = False
                    if not current_loc:
                        current_loc = VehicleCurrentLocation(
                            vehicle_id=vehicle_id,
                            source=LocationSource(source),
                            latitude=loc.latitude,
                            longitude=loc.longitude,
                            speed=getattr(loc, "speed", None),
                            heading=getattr(loc, "heading", None),
                            accuracy=getattr(loc, "accuracy", None),
                            last_timestamp=ts,
                            last_received_at=datetime.now(timezone.utc),
                            driver_id=driver_id,
                            source_metadata=metadata if metadata else None
                        )
                        db.add(current_loc)
                        is_newer = True
                    elif ts > current_loc.last_timestamp:
                        current_loc.latitude = loc.latitude
                        current_loc.longitude = loc.longitude
                        current_loc.speed = getattr(loc, "speed", None)
                        current_loc.heading = getattr(loc, "heading", None)
                        current_loc.accuracy = getattr(loc, "accuracy", None)
                        current_loc.last_timestamp = ts
                        current_loc.last_received_at = datetime.now(timezone.utc)
                        current_loc.driver_id = driver_id
                        current_loc.source_metadata = metadata if metadata else None
                        is_newer = True
                    else:
                        # Stale event, but we still received communication from the device
                        current_loc.last_received_at = datetime.now(timezone.utc)

                    # 3. Update Vehicle Cache if newer
                    if is_newer:
                        vehicle.last_known_lat = loc.latitude
                        vehicle.last_known_lng = loc.longitude
                        vehicle.last_location_at = ts
                        vehicle.last_location_source = source
                        
                        # Emit LOCATION_UPDATED event
                        op_event = OperationalEvent(
                            event_type=EventType.LOCATION_UPDATED,
                            entity_type=EntityType.VEHICLE,
                            entity_id=str(vehicle_id),
                            occurred_at=ts,
                            capture_method=CaptureMethod.API,
                            created_by=str(driver_id),
                            company_id=company_id,
                            payload={
                                "vehicle_id": vehicle_id,
                                "company_id": company_id,
                                "source": source,
                                "location_timestamp": ts.isoformat(),
                                "received_at": datetime.now(timezone.utc).isoformat()
                            }
                        )
                        db.add(op_event)
                        await db.flush()
                        
                        outbox_payload = OperationalEventResponse.model_validate(op_event).model_dump(mode="json")
                        outbox_msg = OutboxMessage(
                            topic=settings.KAFKA_OPERATIONAL_EVENTS_TOPIC,
                            payload=outbox_payload,
                            event_id=str(op_event.id)
                        )
                        db.add(outbox_msg)

                item_status["status"] = "accepted"
                result["accepted"] += 1
                result["items"].append(item_status)

            except IntegrityError as e:
                # Deduplication logic
                if "event_fingerprint" in str(e):
                    item_status["status"] = "duplicate"
                    result["duplicates"] += 1
                    result["items"].append(item_status)
                else:
                    item_status["status"] = "failed"
                    item_status["reason"] = "db_error"
                    result["rejected"] += 1
                    result["items"].append(item_status)
                    logger.error(f"Integrity error processing location: {e}")
            except Exception as e:
                item_status["status"] = "failed"
                item_status["reason"] = "unexpected_error"
                result["rejected"] += 1
                result["items"].append(item_status)
                logger.error(f"Unexpected error processing location: {e}")

        # The outer commit will happen in the router after process_batch returns
        return result


    @classmethod
    async def process_hardware_batch(
        cls, 
        db: AsyncSession, 
        locations: List[NormalizedHardwareEvent], 
        allow_registration_only: bool = False
    ) -> Dict[str, Any]:
        result = {
            "accepted": 0,
            "duplicates": 0,
            "rejected": 0,
            "items": []
        }

        for loc in locations:
            item_status = {"timestamp": loc.timestamp}
            
            # Extract timestamp
            ts = loc.timestamp
            
            # Validate coordinates
            if not (-90 <= loc.latitude <= 90) or not (-180 <= loc.longitude <= 180):
                item_status["status"] = "invalid"
                item_status["reason"] = "invalid_coordinates"
                result["rejected"] += 1
                result["items"].append(item_status)
                continue
                
            # Resolve Device and Vehicle
            vehicle_id = None
            company_id = None
            device_id = None
            
            if loc.device_imei:
                # 1. Resolve by IMEI
                asset_query = select(Asset).where(
                    and_(
                        Asset.serial_number == loc.device_imei,
                        Asset.asset_type == AssetType.GPS_DEVICE
                    )
                )
                asset_res = await db.execute(asset_query)
                assets = asset_res.scalars().all()
                
                if len(assets) == 0:
                    item_status["status"] = "unknown_device"
                    result["rejected"] += 1
                    result["items"].append(item_status)
                    continue
                elif len(assets) > 1:
                    item_status["status"] = "ambiguous_device"
                    result["rejected"] += 1
                    result["items"].append(item_status)
                    continue
                    
                asset = assets[0]
                device_id = asset.id
                
                if not asset.current_vehicle_id:
                    item_status["status"] = "device_not_assigned"
                    result["rejected"] += 1
                    result["items"].append(item_status)
                    continue
                    
                vehicle_id = asset.current_vehicle_id
                
                # Double check with registration if provided
                if loc.vehicle_registration:
                    v_query = select(Vehicle).where(Vehicle.registration_number == loc.vehicle_registration)
                    v_res = await db.execute(v_query)
                    v_match = v_res.scalars().first()
                    if not v_match or v_match.id != vehicle_id:
                        item_status["status"] = "device_vehicle_mismatch"
                        result["rejected"] += 1
                        result["items"].append(item_status)
                        continue
                        
                # We need company_id from vehicle
                vehicle = await db.get(Vehicle, vehicle_id)
                company_id = vehicle.company_id
                
            elif loc.vehicle_registration and allow_registration_only:
                # 2. Fallback to registration (ONLY IF ALLOWED)
                v_query = select(Vehicle).where(Vehicle.registration_number == loc.vehicle_registration)
                v_res = await db.execute(v_query)
                v_match = v_res.scalars().first()
                if not v_match:
                    item_status["status"] = "invalid"
                    item_status["reason"] = "vehicle_not_found"
                    result["rejected"] += 1
                    result["items"].append(item_status)
                    continue
                
                vehicle_id = v_match.id
                company_id = v_match.company_id
                vehicle = v_match
            else:
                item_status["status"] = "invalid"
                item_status["reason"] = "missing_identifiers"
                result["rejected"] += 1
                result["items"].append(item_status)
                continue
                
            # Fingerprint (source, device_id or 'reg:'+reg, ts, lat, lng)
            identity = str(device_id) if device_id else f"reg:{loc.vehicle_registration}"
            fingerprint = cls._generate_fingerprint(
                source=LocationSource.HARDWARE_GPS.value,
                identity_id=identity,
                timestamp=ts,
                latitude=loc.latitude,
                longitude=loc.longitude
            )
            
            metadata = loc.source_metadata or {}
            if loc.ignition_status is not None:
                metadata["ignition_status"] = loc.ignition_status

            try:
                async with db.begin_nested():
                    # 1. Insert into VehicleLocation
                    db_loc = VehicleLocation(
                        vehicle_id=vehicle_id,
                        company_id=company_id,
                        device_id=device_id,
                        latitude=loc.latitude,
                        longitude=loc.longitude,
                        speed=loc.speed,
                        heading=loc.heading,
                        accuracy=loc.accuracy,
                        timestamp=ts,
                        source=LocationSource.HARDWARE_GPS,
                        event_fingerprint=fingerprint,
                        source_metadata=metadata if metadata else None
                    )
                    db.add(db_loc)
                    await db.flush()
                    
                    # 2. Update VehicleCurrentLocation (Independent)
                    current_query = select(VehicleCurrentLocation).where(
                        and_(
                            VehicleCurrentLocation.vehicle_id == vehicle_id,
                            VehicleCurrentLocation.source == LocationSource.HARDWARE_GPS.value
                        )
                    ).with_for_update()
                    current_result = await db.execute(current_query)
                    current_loc = current_result.scalars().first()

                    is_stale_for_hardware = False
                    is_newer_than_cache = False
                    
                    if not current_loc:
                        current_loc = VehicleCurrentLocation(
                            vehicle_id=vehicle_id,
                            source=LocationSource.HARDWARE_GPS,
                            latitude=loc.latitude,
                            longitude=loc.longitude,
                            speed=loc.speed,
                            heading=loc.heading,
                            accuracy=loc.accuracy,
                            last_timestamp=ts,
                            last_received_at=datetime.now(timezone.utc),
                            device_id=device_id,
                            source_metadata=metadata if metadata else None
                        )
                        db.add(current_loc)
                        is_newer_than_cache = True
                    elif ts > current_loc.last_timestamp:
                        current_loc.latitude = loc.latitude
                        current_loc.longitude = loc.longitude
                        current_loc.speed = loc.speed
                        current_loc.heading = loc.heading
                        current_loc.accuracy = loc.accuracy
                        current_loc.last_timestamp = ts
                        current_loc.last_received_at = datetime.now(timezone.utc)
                        current_loc.device_id = device_id
                        current_loc.source_metadata = metadata if metadata else None
                        is_newer_than_cache = True
                    else:
                        # Event is successfully recorded but it's older than the current hardware state
                        current_loc.last_received_at = datetime.now(timezone.utc)
                        is_stale_for_hardware = True

                    # 3. Cross-source vehicle cache
                    if vehicle.last_location_at is None or ts > vehicle.last_location_at:
                        vehicle.last_known_lat = loc.latitude
                        vehicle.last_known_lng = loc.longitude
                        vehicle.last_location_at = ts
                        vehicle.last_location_source = LocationSource.HARDWARE_GPS.value
                        
                    if is_newer_than_cache:
                        # Emit LOCATION_UPDATED event
                        op_event = OperationalEvent(
                            event_type=EventType.LOCATION_UPDATED,
                            entity_type=EntityType.VEHICLE,
                            entity_id=str(vehicle_id),
                            occurred_at=ts,
                            capture_method=CaptureMethod.API,
                            created_by=str(device_id),
                            company_id=company_id,
                            payload={
                                "vehicle_id": vehicle_id,
                                "company_id": company_id,
                                "source": LocationSource.HARDWARE_GPS.value,
                                "location_timestamp": ts.isoformat(),
                                "received_at": datetime.now(timezone.utc).isoformat()
                            }
                        )
                        db.add(op_event)
                        await db.flush()
                        
                        outbox_payload = OperationalEventResponse.model_validate(op_event).model_dump(mode="json")
                        outbox_msg = OutboxMessage(
                            topic=settings.KAFKA_OPERATIONAL_EVENTS_TOPIC,
                            payload=outbox_payload,
                            event_id=str(op_event.id)
                        )
                        db.add(outbox_msg)
                        
                if is_stale_for_hardware:
                    item_status["status"] = "stale_event"
                else:
                    item_status["status"] = "accepted"
                    
                result["accepted"] += 1
                result["items"].append(item_status)

            except IntegrityError as e:
                if "event_fingerprint" in str(e):
                    item_status["status"] = "duplicate"
                    result["duplicates"] += 1
                    result["items"].append(item_status)
                else:
                    item_status["status"] = "failed"
                    item_status["reason"] = "db_error"
                    result["rejected"] += 1
                    result["items"].append(item_status)
                    logger.error(f"Integrity error processing location: {e}")
            except Exception as e:
                item_status["status"] = "failed"
                item_status["reason"] = "unexpected_error"
                result["rejected"] += 1
                result["items"].append(item_status)
                logger.error(f"Unexpected error processing location: {e}")

        return result
