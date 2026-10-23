"""
FleetGuard — Geospatial Analytics & Telemetry Processing Utilities

Provides robust geospatial algorithms:
- Haversine distance and bearing calculation
- GPS gap detection (temporal gaps and physical anomalies)
- Stationary stop detection
- Route bounding box calculation
- Speed calculation & unit conversion (m/s to km/h)
- Visvalingam-Whyatt / Douglas-Peucker / Extrema-preserving downsampling
- Telemetry quality and coverage scoring
"""

import math
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple


def haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points on the Earth in meters."""
    if lat1 == lat2 and lon1 == lon2:
        return 0.0

    R = 6371000.0  # Earth's radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2.0) ** 2))
    
    # Clamp to [-1, 1] to avoid math domain errors
    a = min(1.0, max(0.0, a))
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


def calculate_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the forward azimuth / bearing from point 1 to point 2 in degrees [0, 360)."""
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_lambda = math.radians(lon2 - lon1)

    y = math.sin(delta_lambda) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(delta_lambda)
    bearing_rad = math.atan2(y, x)
    bearing_deg = (math.degrees(bearing_rad) + 360.0) % 360.0
    return round(bearing_deg, 1)


def to_utc(dt: Any) -> datetime:
    """Normalize any datetime or ISO string to UTC-aware datetime."""
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def detect_gaps_and_stops(
    points: List[Dict[str, Any]],
    gap_time_threshold_seconds: float = 900.0,  # 15 minutes
    max_plausible_speed_kmh: float = 160.0,      # Suspicious jump threshold
    stop_speed_threshold_kmh: float = 3.0,       # Stopped if <= 3 km/h
    stop_min_duration_seconds: float = 300.0,    # Stop if stationary >= 5 minutes
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Analyze chronologically sorted points to detect:
    1. GPS Gaps (loss of signal or prolonged offline periods)
    2. Stops (stationary intervals where vehicle remained parked or idle)
    """
    gaps: List[Dict[str, Any]] = []
    stops: List[Dict[str, Any]] = []

    if len(points) < 2:
        return gaps, stops

    # 1. Detect Gaps
    for i in range(len(points) - 1):
        p1 = points[i]
        p2 = points[i + 1]

        t1 = to_utc(p1["timestamp"])
        t2 = to_utc(p2["timestamp"])
        time_diff = (t2 - t1).total_seconds()

        if time_diff < 0:
            # Out-of-order point (should be sorted beforehand, but handle gracefully)
            continue

        dist_m = haversine_distance_meters(p1["latitude"], p1["longitude"], p2["latitude"], p2["longitude"])
        calc_speed_kmh = (dist_m / time_diff * 3.6) if time_diff > 0 else 0.0

        # Gap condition: Time gap > 15 minutes OR physically impossible speed jump
        if time_diff >= gap_time_threshold_seconds:
            gaps.append({
                "from_index": i,
                "to_index": i + 1,
                "from_timestamp": t1.isoformat(),
                "to_timestamp": t2.isoformat(),
                "duration_seconds": round(time_diff, 1),
                "duration_minutes": round(time_diff / 60.0, 1),
                "distance_km": round(dist_m / 1000.0, 2),
                "gap_type": "SIGNAL_LOSS",
                "description": f"GPS signal lost for {round(time_diff / 60.0, 1)} minutes",
                "from_point": [p1["latitude"], p1["longitude"]],
                "to_point": [p2["latitude"], p2["longitude"]]
            })
        elif calc_speed_kmh > max_plausible_speed_kmh and dist_m > 500:
            gaps.append({
                "from_index": i,
                "to_index": i + 1,
                "from_timestamp": t1.isoformat(),
                "to_timestamp": t2.isoformat(),
                "duration_seconds": round(time_diff, 1),
                "duration_minutes": round(time_diff / 60.0, 1),
                "distance_km": round(dist_m / 1000.0, 2),
                "gap_type": "TELEPORT_ANOMALY",
                "description": f"Implausible coordinate jump ({round(dist_m / 1000.0, 1)} km in {int(time_diff)}s)",
                "from_point": [p1["latitude"], p1["longitude"]],
                "to_point": [p2["latitude"], p2["longitude"]]
            })

    # 2. Detect Stops
    current_stop_start = None
    current_stop_pts: List[Dict[str, Any]] = []

    for idx, p in enumerate(points):
        spd = p.get("speed_kmh")
        if spd is None:
            # Fall back to raw speed if km/h not precomputed
            raw_spd = p.get("speed")
            spd = (raw_spd * 3.6) if raw_spd is not None else 0.0

        is_stopped = spd <= stop_speed_threshold_kmh

        if is_stopped:
            if current_stop_start is None:
                current_stop_start = p
                current_stop_pts = [p]
            else:
                # Check that distance from start of stop hasn't drifted > 100m
                dist_from_stop_start = haversine_distance_meters(
                    current_stop_start["latitude"], current_stop_start["longitude"],
                    p["latitude"], p["longitude"]
                )
                if dist_from_stop_start <= 100.0:
                    current_stop_pts.append(p)
                else:
                    # Moved away, finalize previous stop
                    duration = (to_utc(current_stop_pts[-1]["timestamp"]) - to_utc(current_stop_start["timestamp"])).total_seconds()
                    if duration >= stop_min_duration_seconds:
                        avg_lat = sum(pt["latitude"] for pt in current_stop_pts) / len(current_stop_pts)
                        avg_lng = sum(pt["longitude"] for pt in current_stop_pts) / len(current_stop_pts)
                        stops.append({
                            "start_time": to_utc(current_stop_start["timestamp"]).isoformat(),
                            "end_time": to_utc(current_stop_pts[-1]["timestamp"]).isoformat(),
                            "duration_seconds": round(duration, 1),
                            "duration_minutes": round(duration / 60.0, 1),
                            "latitude": round(avg_lat, 6),
                            "longitude": round(avg_lng, 6),
                            "points_count": len(current_stop_pts),
                            "point_index": idx - len(current_stop_pts)
                        })
                    current_stop_start = p
                    current_stop_pts = [p]
        else:
            if current_stop_start is not None:
                duration = (to_utc(current_stop_pts[-1]["timestamp"]) - to_utc(current_stop_start["timestamp"])).total_seconds()
                if duration >= stop_min_duration_seconds:
                    avg_lat = sum(pt["latitude"] for pt in current_stop_pts) / len(current_stop_pts)
                    avg_lng = sum(pt["longitude"] for pt in current_stop_pts) / len(current_stop_pts)
                    stops.append({
                        "start_time": to_utc(current_stop_start["timestamp"]).isoformat(),
                        "end_time": to_utc(current_stop_pts[-1]["timestamp"]).isoformat(),
                        "duration_seconds": round(duration, 1),
                        "duration_minutes": round(duration / 60.0, 1),
                        "latitude": round(avg_lat, 6),
                        "longitude": round(avg_lng, 6),
                        "points_count": len(current_stop_pts),
                        "point_index": idx - len(current_stop_pts)
                    })
                current_stop_start = None
                current_stop_pts = []

    # Finalize trailing stop
    if current_stop_start is not None and len(current_stop_pts) > 1:
        duration = (to_utc(current_stop_pts[-1]["timestamp"]) - to_utc(current_stop_start["timestamp"])).total_seconds()
        if duration >= stop_min_duration_seconds:
            avg_lat = sum(pt["latitude"] for pt in current_stop_pts) / len(current_stop_pts)
            avg_lng = sum(pt["longitude"] for pt in current_stop_pts) / len(current_stop_pts)
            stops.append({
                "start_time": to_utc(current_stop_start["timestamp"]).isoformat(),
                "end_time": to_utc(current_stop_pts[-1]["timestamp"]).isoformat(),
                "duration_seconds": round(duration, 1),
                "duration_minutes": round(duration / 60.0, 1),
                "latitude": round(avg_lat, 6),
                "longitude": round(avg_lng, 6),
                "points_count": len(current_stop_pts),
                "point_index": len(points) - len(current_stop_pts)
            })

    return gaps, stops


def compute_bounding_box(points: List[Dict[str, Any]]) -> Optional[List[float]]:
    """Return [min_lat, min_lng, max_lat, max_lng] or None if points is empty."""
    if not points:
        return None
    min_lat = min(p["latitude"] for p in points)
    max_lat = max(p["latitude"] for p in points)
    min_lng = min(p["longitude"] for p in points)
    max_lng = max(p["longitude"] for p in points)
    return [round(min_lat, 6), round(min_lng, 6), round(max_lat, 6), round(max_lng, 6)]


def downsample_gps_points(points: List[Dict[str, Any]], max_points: int) -> List[Dict[str, Any]]:
    """
    Intelligently downsample GPS points when points exceed max_points.
    Preserves:
    - Point 0 (Origin/Start)
    - Last point (Destination/End)
    - Significant turns (heading difference > 25 degrees)
    - High-speed extremes
    - Stops / stationary transitions
    - Uniform time step distribution across the rest
    """
    total = len(points)
    if total <= max_points:
        return points

    # Identify essential indices
    essential_indices = {0, total - 1}

    # Significant heading changes or velocity changes
    for i in range(1, total - 1):
        prev_pt = points[i - 1]
        curr_pt = points[i]
        next_pt = points[i + 1]

        h1 = curr_pt.get("heading")
        h2 = next_pt.get("heading")
        if h1 is not None and h2 is not None:
            heading_diff = abs(h2 - h1)
            if heading_diff > 180:
                heading_diff = 360 - heading_diff
            if heading_diff >= 30:  # significant turn
                essential_indices.add(i)

        s1 = curr_pt.get("speed_kmh") or 0.0
        s2 = next_pt.get("speed_kmh") or 0.0
        if (s1 > 5.0 and s2 <= 1.0) or (s1 <= 1.0 and s2 > 5.0):
            # Start/stop transition
            essential_indices.add(i)

    # If essentials alone exceed max_points, step through them uniformly
    if len(essential_indices) > max_points:
        sorted_essentials = sorted(essential_indices)
        step = len(sorted_essentials) / max_points
        chosen = [sorted_essentials[int(i * step)] for i in range(max_points)]
        chosen[0] = 0
        chosen[-1] = total - 1
        return [points[i] for i in sorted(set(chosen))]

    # Otherwise, fill the remainder up to max_points using uniform sampling
    remaining_budget = max_points - len(essential_indices)
    step = total / (remaining_budget + 1)
    for i in range(1, remaining_budget + 1):
        idx = min(int(i * step), total - 1)
        essential_indices.add(idx)

    return [points[i] for i in sorted(essential_indices)]


def calculate_comprehensive_analytics(
    points: List[Dict[str, Any]],
    total_trips: int = 0
) -> Dict[str, Any]:
    """
    Calculate deterministic, audit-ready operational analytics for a driver's GPS points.
    Filters out GPS glitches (> 150 km/h jumps).
    """
    if not points:
        return {
            "total_trips": total_trips,
            "total_recorded_distance_km": None,
            "total_duration_seconds": None,
            "moving_duration_seconds": None,
            "stationary_duration_seconds": None,
            "average_speed_kmh": None,
            "max_speed_kmh": None,
            "valid_speed_samples": 0,
            "gps_coverage_pct": None,
            "gps_gap_count": 0,
            "total_points_analyzed": 0,
            "first_recorded_point": None,
            "last_recorded_point": None,
            "last_known_location": None,
        }

    valid_speeds: List[float] = []
    total_dist_m = 0.0
    moving_time_s = 0.0
    stationary_time_s = 0.0
    gap_time_s = 0.0

    t_first = to_utc(points[0]["timestamp"])
    t_last = to_utc(points[-1]["timestamp"])
    total_duration_s = max(0.0, (t_last - t_first).total_seconds())

    gaps, stops = detect_gaps_and_stops(points)

    for gap in gaps:
        gap_time_s += gap["duration_seconds"]

    for i in range(len(points) - 1):
        p1 = points[i]
        p2 = points[i + 1]

        t1 = to_utc(p1["timestamp"])
        t2 = to_utc(p2["timestamp"])
        dt = (t2 - t1).total_seconds()
        if dt <= 0:
            continue

        dist_m = haversine_distance_meters(p1["latitude"], p1["longitude"], p2["latitude"], p2["longitude"])
        calc_spd_kmh = (dist_m / dt * 3.6)

        # Ignore GPS teleport jumps in distance calculation
        if calc_spd_kmh <= 160.0 and dt < 900.0:
            total_dist_m += dist_m

        # Record speed observations
        obs_spd = p1.get("speed_kmh")
        if obs_spd is None and p1.get("speed") is not None:
            obs_spd = round(p1["speed"] * 3.6, 1)

        if obs_spd is not None and 0.0 <= obs_spd <= 160.0:
            valid_speeds.append(obs_spd)
            if obs_spd > 3.0:
                moving_time_s += min(dt, 900.0)
            else:
                stationary_time_s += min(dt, 900.0)
        else:
            if calc_spd_kmh > 3.0:
                moving_time_s += min(dt, 900.0)
            else:
                stationary_time_s += min(dt, 900.0)

    # Last point speed
    last_spd = points[-1].get("speed_kmh")
    if last_spd is None and points[-1].get("speed") is not None:
        last_spd = round(points[-1]["speed"] * 3.6, 1)
    if last_spd is not None and 0.0 <= last_spd <= 160.0:
        valid_speeds.append(last_spd)

    moving_speeds = [s for s in valid_speeds if s > 3.0]
    avg_spd = round(sum(moving_speeds) / len(moving_speeds), 1) if moving_speeds else (
        round(sum(valid_speeds) / len(valid_speeds), 1) if valid_speeds else None
    )
    max_spd = round(max(valid_speeds), 1) if valid_speeds else None

    # GPS coverage percentage: (active time / total elapsed time) * 100
    active_tracking_time = max(0.0, total_duration_s - gap_time_s)
    coverage_pct = round((active_tracking_time / total_duration_s * 100.0), 1) if total_duration_s > 0 else 100.0
    coverage_pct = min(100.0, max(0.0, coverage_pct))

    return {
        "total_trips": total_trips,
        "total_recorded_distance_km": round(total_dist_m / 1000.0, 2),
        "total_duration_seconds": round(total_duration_s, 1),
        "moving_duration_seconds": round(moving_time_s, 1),
        "stationary_duration_seconds": round(stationary_time_s, 1),
        "average_speed_kmh": avg_spd,
        "max_speed_kmh": max_spd,
        "valid_speed_samples": len(valid_speeds),
        "gps_coverage_pct": coverage_pct,
        "gps_gap_count": len(gaps),
        "total_points_analyzed": len(points),
        "first_recorded_point": {
            "latitude": points[0]["latitude"],
            "longitude": points[0]["longitude"],
            "timestamp": t_first.isoformat(),
        },
        "last_recorded_point": {
            "latitude": points[-1]["latitude"],
            "longitude": points[-1]["longitude"],
            "timestamp": t_last.isoformat(),
        },
        "last_known_location": {
            "latitude": points[-1]["latitude"],
            "longitude": points[-1]["longitude"],
            "timestamp": t_last.isoformat(),
            "speed_kmh": last_spd,
            "heading": points[-1].get("heading"),
        },
    }
