"""
FleetGuard — Route Deviation Detection Engine
Performs real-time geospatial corridor comparison, GPS noise filtering,
state-machine confirmation, incident persistence, and manager alerting.
"""

import math
import uuid
import logging
import polyline
from datetime import datetime, timezone, timedelta
from typing import List, Tuple, Optional, Dict, Any

from sqlalchemy import select, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from models.trip_domain import Trip, TripStatus
from models.route_domain import (
    RouteVersion, RouteDeviationEvent, DeviationStatus, DeviationSeverity
)
from models.notification import Notification, NotificationCategory

logger = logging.getLogger("fleetguard.routing.deviation")

EARTH_RADIUS_METERS = 6371000.0


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great circle distance in meters between two coordinates."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2.0) ** 2
    return 2.0 * EARTH_RADIUS_METERS * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))


def point_to_segment_distance(
    plat: float, plon: float,
    alat: float, alon: float,
    blat: float, blon: float
) -> float:
    """
    Calculates the shortest distance in meters from point P to line segment AB
    using local equirectangular planar projection.
    """
    mean_lat = math.radians((alat + blat) / 2.0)
    cos_lat = math.cos(mean_lat)

    # Convert coordinates to local Cartesian (x: East, y: North) in meters relative to A
    ax, ay = 0.0, 0.0
    bx = (blon - alon) * (math.pi / 180.0) * EARTH_RADIUS_METERS * cos_lat
    by = (blat - alat) * (math.pi / 180.0) * EARTH_RADIUS_METERS
    px = (plon - alon) * (math.pi / 180.0) * EARTH_RADIUS_METERS * cos_lat
    py = (plat - alat) * (math.pi / 180.0) * EARTH_RADIUS_METERS

    dx = bx - ax
    dy = by - ay
    seg_len_sq = dx * dx + dy * dy

    if seg_len_sq < 1e-6:
        # Segment A and B are identical points
        return math.hypot(px, py)

    # Projection factor t of P onto AB
    t = (px * dx + py * dy) / seg_len_sq
    t_clamped = max(0.0, min(1.0, t))

    closest_x = ax + t_clamped * dx
    closest_y = ay + t_clamped * dy

    return math.hypot(px - closest_x, py - closest_y)


def calculate_min_distance_to_polyline(
    lat: float, lon: float, polyline_coords: List[Tuple[float, float]]
) -> float:
    """
    Finds the minimum distance in meters from a coordinate to any segment along a polyline.
    Uses bounding box pre-filtering for fast evaluation of long routes.
    """
    if not polyline_coords:
        return 0.0
    if len(polyline_coords) == 1:
        return haversine_distance(lat, lon, polyline_coords[0][0], polyline_coords[0][1])

    min_dist = float("inf")
    # ~0.05 degrees is approx 5.5 km bounding buffer
    box_buf = 0.05

    for i in range(len(polyline_coords) - 1):
        a_lat, a_lon = polyline_coords[i]
        b_lat, b_lon = polyline_coords[i + 1]

        # Fast bounding box rejection
        seg_min_lat = min(a_lat, b_lat) - box_buf
        seg_max_lat = max(a_lat, b_lat) + box_buf
        seg_min_lon = min(a_lon, b_lon) - box_buf
        seg_max_lon = max(a_lon, b_lon) + box_buf

        if not (seg_min_lat <= lat <= seg_max_lat and seg_min_lon <= lon <= seg_max_lon):
            continue

        d = point_to_segment_distance(lat, lon, a_lat, a_lon, b_lat, b_lon)
        if d < min_dist:
            min_dist = d

    # If bounding box filtered everything (point is very far), fallback to nearest vertex
    if min_dist == float("inf"):
        for a_lat, a_lon in polyline_coords:
            d = haversine_distance(lat, lon, a_lat, a_lon)
            if d < min_dist:
                min_dist = d

    return min_dist


class RouteDeviationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.threshold_meters = getattr(settings, "ROUTE_DEVIATION_THRESHOLD_METERS", 200.0)
        self.recovery_meters = getattr(settings, "ROUTE_DEVIATION_RECOVERY_METERS", 150.0)
        self.confirmation_count = getattr(settings, "ROUTE_DEVIATION_CONFIRMATION_COUNT", 3)
        self.cooldown_minutes = getattr(settings, "ROUTE_DEVIATION_NOTIFICATION_COOLDOWN_MINUTES", 15)

    def _determine_severity(self, distance_meters: float) -> DeviationSeverity:
        if distance_meters >= 3000.0:
            return DeviationSeverity.CRITICAL
        elif distance_meters >= 1500.0:
            return DeviationSeverity.HIGH
        elif distance_meters >= 500.0:
            return DeviationSeverity.MEDIUM
        return DeviationSeverity.LOW

    async def evaluate_position(
        self,
        driver_id: int,
        company_id: int,
        latitude: float,
        longitude: float,
        accuracy: Optional[float] = None,
        speed: Optional[float] = None,
        timestamp: Optional[datetime] = None,
        trip_id_hint: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Authoritative evaluation of a single incoming GPS point against the active trip's route.
        Returns a status dictionary describing the corridor check and state transitions.
        """
        now = datetime.now(timezone.utc)
        eval_time = timestamp or now

        # 1. Resolve Active Trip
        query = select(Trip).where(
            Trip.company_id == company_id,
            Trip.status == TripStatus.IN_PROGRESS
        )
        if trip_id_hint:
            if trip_id_hint.isdigit():
                query = query.where(or_(Trip.id == int(trip_id_hint), Trip.trip_id == trip_id_hint))
            else:
                query = query.where(Trip.trip_id == trip_id_hint)
        else:
            query = query.where(Trip.driver_id == driver_id)

        t_res = await self.db.execute(query.limit(1))
        trip = t_res.scalar_one_or_none()
        if not trip:
            return {"status": "NO_ACTIVE_TRIP", "distance_meters": 0.0}

        # 2. Resolve Active Route Version
        route_version = None
        if trip.approved_route_version_id:
            route_version = await self.db.get(RouteVersion, trip.approved_route_version_id)
        if not route_version:
            # Fallback to trip polyline if version not linked
            if not trip.route_polyline:
                return {"status": "NO_APPROVED_ROUTE", "trip_id": trip.trip_id}
            encoded_poly = trip.route_polyline
        else:
            encoded_poly = route_version.polyline

        if not encoded_poly:
            return {"status": "EMPTY_POLYLINE", "trip_id": trip.trip_id}

        # 3. Decode Route Polyline and Calculate Distance
        try:
            coords = polyline.decode(encoded_poly)
        except Exception as e:
            logger.error(f"Failed to decode polyline for trip #{trip.id}: {e}")
            return {"status": "CORRUPT_POLYLINE", "trip_id": trip.trip_id}

        distance_meters = calculate_min_distance_to_polyline(latitude, longitude, coords)
        severity = self._determine_severity(distance_meters)

        # 4. Filter GPS Noise
        # Unreliable GPS measurements (accuracy > 80m) are not used to confirm deviations
        is_gps_reliable = (accuracy is None) or (accuracy <= 80.0)

        # 5. Check for existing active/unresolved deviation event for this trip
        active_event_stmt = (
            select(RouteDeviationEvent)
            .where(
                RouteDeviationEvent.trip_id == trip.id,
                RouteDeviationEvent.company_id == company_id,
                RouteDeviationEvent.status.in_([
                    DeviationStatus.SUSPECTED,
                    DeviationStatus.CONFIRMED,
                    DeviationStatus.OBSTRUCTION_REPORTED
                ])
            )
            .order_by(desc(RouteDeviationEvent.id))
            .limit(1)
        )
        event_res = await self.db.execute(active_event_stmt)
        active_event = event_res.scalar_one_or_none()

        result_summary = {
            "trip_id": trip.trip_id,
            "distance_meters": round(distance_meters, 2),
            "threshold_meters": self.threshold_meters,
            "severity": severity.value,
            "status": "ON_ROUTE"
        }

        # 6. State Machine Progression
        if distance_meters > self.threshold_meters:
            # Point is outside the route corridor
            if not active_event:
                # First outlier -> Create SUSPECTED event
                event_uuid = f"DEV-{str(uuid.uuid4())[:8].upper()}"
                active_event = RouteDeviationEvent(
                    event_id=event_uuid,
                    trip_id=trip.id,
                    company_id=company_id,
                    driver_id=trip.driver_id,
                    vehicle_id=trip.vehicle_id,
                    route_version_id=route_version.id if route_version else None,
                    status=DeviationStatus.SUSPECTED,
                    severity=severity,
                    distance_from_route_meters=distance_meters,
                    max_distance_meters=distance_meters,
                    last_latitude=latitude,
                    last_longitude=longitude,
                    gps_accuracy=accuracy,
                    consecutive_outliers=1,
                    first_detected_at=eval_time,
                    last_detected_at=eval_time
                )
                self.db.add(active_event)
                await self.db.commit()
                result_summary["status"] = "SUSPECTED_DEVIATION"
                result_summary["event_id"] = active_event.event_id

            else:
                # Existing incident: update coordinates and outlier count
                active_event.last_latitude = latitude
                active_event.last_longitude = longitude
                active_event.last_detected_at = eval_time
                active_event.distance_from_route_meters = distance_meters
                active_event.max_distance_meters = max(active_event.max_distance_meters, distance_meters)
                active_event.severity = severity

                if is_gps_reliable:
                    active_event.consecutive_outliers += 1

                # Check if ready to transition SUSPECTED -> CONFIRMED
                if active_event.status == DeviationStatus.SUSPECTED and active_event.consecutive_outliers >= self.confirmation_count:
                    active_event.status = DeviationStatus.CONFIRMED
                    await self._notify_managers_deviation(trip, active_event, distance_meters)
                    result_summary["status"] = "CONFIRMED_DEVIATION"
                    logger.warning(
                        f"Route Deviation CONFIRMED for Trip #{trip.trip_id}: "
                        f"{distance_meters:.0f}m from route after {active_event.consecutive_outliers} outliers."
                    )
                else:
                    result_summary["status"] = active_event.status.value

                await self.db.commit()
                result_summary["event_id"] = active_event.event_id

        elif distance_meters <= self.recovery_meters:
            # Point has returned safely within corridor
            if active_event:
                if active_event.status in [DeviationStatus.CONFIRMED, DeviationStatus.OBSTRUCTION_REPORTED]:
                    active_event.status = DeviationStatus.RETURNED_TO_ROUTE
                    active_event.resolved_at = eval_time
                    await self._notify_managers_returned(trip, active_event)
                    logger.info(f"Driver on Trip #{trip.trip_id} returned to route (distance={distance_meters:.1f}m).")
                    result_summary["status"] = "RETURNED_TO_ROUTE"
                else:
                    # Suspected false alarm: simply resolve
                    active_event.status = DeviationStatus.RESOLVED
                    active_event.resolved_at = eval_time
                    result_summary["status"] = "RESOLVED"

                await self.db.commit()
                result_summary["event_id"] = active_event.event_id

        return result_summary

    async def _notify_managers_deviation(
        self, trip: Trip, event: RouteDeviationEvent, distance_meters: float
    ) -> None:
        """Emits persistent in-app notification and real-time WebSocket alert."""
        driver_name = trip.driver.name if trip.driver else f"Driver #{trip.driver_id or 'Unknown'}"
        title = "Route Deviation Detected"
        msg = f"Driver {driver_name} on trip {trip.trip_id} is approximately {int(distance_meters)} meters from the approved route."

        # Persistent Notification
        notif = Notification(
            category=NotificationCategory.ALERT,
            title=title,
            description=msg,
            company_id=trip.company_id,
            user_id=None,  # Available to all fleet managers
        )
        self.db.add(notif)

        # Real-time WebSocket Broadcast to Owner Dashboard
        try:
            from routers.ws_driver import owner_ws_manager
            await owner_ws_manager.broadcast_to_company(trip.company_id, {
                "type": "route_deviation",
                "event_id": event.event_id,
                "trip_id": trip.trip_id,
                "trip_numeric_id": trip.id,
                "driver_id": trip.driver_id,
                "driver_name": driver_name,
                "vehicle_id": trip.vehicle_id,
                "distance_meters": round(distance_meters, 1),
                "severity": event.severity.value,
                "latitude": event.last_latitude,
                "longitude": event.last_longitude,
                "timestamp": event.last_detected_at.isoformat()
            })
        except Exception as e:
            logger.error(f"Failed to broadcast WebSocket route deviation alert: {e}")

    async def _notify_managers_returned(self, trip: Trip, event: RouteDeviationEvent) -> None:
        """Notifies fleet managers when driver returns to the approved route."""
        driver_name = trip.driver.name if trip.driver else "Driver"
        notif = Notification(
            category=NotificationCategory.TRIP,
            title="Vehicle Returned to Route",
            description=f"Driver {driver_name} on trip {trip.trip_id} has safely returned to the approved route corridor.",
            company_id=trip.company_id,
            user_id=None,
        )
        self.db.add(notif)

        try:
            from routers.ws_driver import owner_ws_manager
            await owner_ws_manager.broadcast_to_company(trip.company_id, {
                "type": "route_recovery",
                "event_id": event.event_id,
                "trip_id": trip.trip_id,
                "trip_numeric_id": trip.id,
                "timestamp": event.resolved_at.isoformat() if event.resolved_at else datetime.now(timezone.utc).isoformat()
            })
        except Exception as e:
            logger.error(f"Failed to broadcast WebSocket route recovery alert: {e}")
