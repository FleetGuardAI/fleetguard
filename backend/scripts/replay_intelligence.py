"""
FleetGuard Phase 5 — Historical Intelligence Replay

Feeds historical VehicleLocation records chronologically into the Phase 4
intelligence signal-calculation logic WITHOUT writing to production tables.

All writes (LocationAlert, IntelligenceCondition, VehicleCurrentLocation, etc.)
are intercepted by an in-memory simulation layer.

Usage:
    python scripts/replay_intelligence.py [--start YYYY-MM-DD] [--end YYYY-MM-DD]
                                          [--vehicles 1,2,3] [--companies 1,2]
                                          [--out-csv phase5_replay_report.csv]
                                          [--out-json phase5_replay_report.json]
                                          [--config candidate_config.json]
"""

import asyncio
import csv
import json
import logging
import math
import argparse
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy import text, create_engine
from sqlalchemy.ext.asyncio import create_async_engine
from database import engine as default_engine
from services.driver_vehicle_intelligence_config import intelligence_config

logging.basicConfig(level=logging.DEBUG, format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger("replay_intelligence")

# ---------------------------------------------------------------------------
# Haversine (same formula used in production service)
# ---------------------------------------------------------------------------
def haversine_m(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ---------------------------------------------------------------------------
# Simulated location state (replaces VehicleCurrentLocation read/write)
# ---------------------------------------------------------------------------
@dataclass
class SimSourceState:
    vehicle_id: int
    source: str
    latitude: float
    longitude: float
    speed: Optional[float]
    heading: Optional[float]
    accuracy: Optional[float]
    last_timestamp: datetime
    last_received_at: datetime


# ---------------------------------------------------------------------------
# Simulated condition state (replaces IntelligenceCondition table)
# ---------------------------------------------------------------------------
@dataclass
class SimCondition:
    condition_type: str
    vehicle_id: int
    driver_id: Optional[int]
    trip_id: Optional[int]
    company_id: int
    first_seen_at: datetime
    last_evaluated_at: datetime
    status: str = "ACTIVE"
    alert_opened_at: Optional[datetime] = None
    alert_resolved_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    distance_at_open: Optional[float] = None
    distance_peak: Optional[float] = None
    transition_count: int = 0  # for hysteresis analysis
    flap_events: int = 0       # rapid open/close cycles


# ---------------------------------------------------------------------------
# Replay row (output record)
# ---------------------------------------------------------------------------
@dataclass
class ReplayRecord:
    vehicle_id: int
    driver_id: Optional[int]
    condition_type: str
    first_seen: str
    alert_open_time: Optional[str]
    alert_resolved_time: Optional[str]
    duration_seconds: Optional[float]
    distance: Optional[float]
    driver_speed_ms: Optional[float]
    vehicle_speed_ms: Optional[float]
    driver_accuracy: Optional[float]
    vehicle_accuracy: Optional[float]
    timestamp_delta_sec: Optional[float]
    trigger_rule: str
    phone_freshness: str
    hardware_freshness: str
    data_quality_exclusion: Optional[str]
    classification: str = "UNKNOWN"


# ---------------------------------------------------------------------------
# Freshness calculation (mirrors Phase 4 logic)
# ---------------------------------------------------------------------------
def get_freshness(state: Optional[SimSourceState], now: datetime, source: str) -> str:
    if state is None:
        return "OFFLINE"
    cfg = intelligence_config
    stale_sec = (
        cfg.PHONE_GPS_EVENT_STALE_AFTER_SECONDS
        if source == "PHONE_GPS"
        else cfg.HARDWARE_GPS_EVENT_STALE_AFTER_SECONDS
    )
    age = (now - state.last_timestamp).total_seconds()
    if age > stale_sec:
        return "STALE"
    return "FRESH"


# ---------------------------------------------------------------------------
# Proximity state
# ---------------------------------------------------------------------------
def get_proximity(dist: Optional[float]) -> str:
    if dist is None:
        return "UNKNOWN"
    if dist <= intelligence_config.DRIVER_VEHICLE_PROXIMITY_METERS:
        return "WITH_VEHICLE"
    if dist <= intelligence_config.DRIVER_VEHICLE_POSSIBLE_PROXIMITY_METERS:
        return "POSSIBLY_NEAR"
    return "AWAY_FROM_VEHICLE"


# ---------------------------------------------------------------------------
# Movement state
# ---------------------------------------------------------------------------
def get_movement(phone: Optional[SimSourceState], hw: Optional[SimSourceState]) -> str:
    if hw is None or hw.speed is None:
        return "UNKNOWN"
    v_kmh = (hw.speed or 0) * 3.6
    d_kmh = ((phone.speed or 0) * 3.6) if phone and phone.speed is not None else None
    if v_kmh > intelligence_config.VEHICLE_MOVING_SPEED_THRESHOLD_KMH:
        if d_kmh is not None and d_kmh < intelligence_config.DRIVER_STATIONARY_SPEED_THRESHOLD_KMH:
            return "VEHICLE_MOVING_DRIVER_STATIONARY"
        return "BOTH_MOVING"
    return "BOTH_STATIONARY"


# ---------------------------------------------------------------------------
# Timestamp compatibility
# ---------------------------------------------------------------------------
def timestamps_compatible(phone: Optional[SimSourceState], hw: Optional[SimSourceState]) -> bool:
    if phone is None or hw is None:
        return False
    delta = abs((phone.last_timestamp - hw.last_timestamp).total_seconds())
    return delta <= intelligence_config.MAX_LOCATION_COMPARISON_TIMESTAMP_DELTA_SECONDS


# ---------------------------------------------------------------------------
# Main replay engine
# ---------------------------------------------------------------------------
async def run_replay(
    start_time: Optional[datetime],
    end_time: Optional[datetime],
    vehicle_ids: Optional[list],
    company_ids: Optional[list],
    out_csv: str,
    out_json: str,
    db_url: Optional[str] = None
):
    logger.info("=== FleetGuard Phase 5 — Historical Intelligence Replay ===")
    logger.info("Mode: READ-ONLY. No production writes will occur.")

    # Build WHERE clauses
    where_clauses = []
    params = {}
    if start_time:
        where_clauses.append("timestamp >= :start_time")
        params["start_time"] = start_time
    if end_time:
        where_clauses.append("timestamp <= :end_time")
        params["end_time"] = end_time
    if vehicle_ids:
        vids_str = ",".join(map(str, vehicle_ids))
        where_clauses.append(f"vehicle_id IN ({vids_str})")
    if company_ids:
        cids_str = ",".join(map(str, company_ids))
        where_clauses.append(f"company_id IN ({cids_str})")

    where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
    query_str = f"""
        SELECT id, vehicle_id, driver_id, company_id, source,
               timestamp, created_at, latitude, longitude,
               speed, heading, accuracy, event_fingerprint
        FROM vehicle_locations
        {where_sql}
        ORDER BY timestamp ASC, id ASC
    """

    # Determine Engine
    if db_url:
        engine = create_async_engine(db_url)
    else:
        engine = default_engine

    # --- Load trip data for context ---
    async with engine.connect() as conn:
        trip_rows = await conn.execute(text(
            "SELECT id, vehicle_id, driver_id, company_id, status, "
            "actual_start_time, actual_end_time FROM trips"
        ))
        trips = [dict(r._mapping) for r in trip_rows]

        rows = await conn.execute(text(query_str), params)
        events = [dict(r._mapping) for r in rows]

    logger.info(f"Loaded {len(events)} location events for replay.")
    logger.info(f"Loaded {len(trips)} trips for context.")

    # --- Counters ---
    stats = {
        "vehicles_replayed": set(),
        "events_replayed": 0,
        "phone_events": 0,
        "hardware_events": 0,
        "comparable_samples": 0,
        "conditions_created": 0,
        "conditions_resolved": 0,
        "alerts_would_open": 0,
        "alerts_would_resolve": 0,
        "duplicate_evals_prevented": 0,
        "data_quality_exclusions": 0,
        "timestamp_skew_exclusions": 0,
        "stale_source_exclusions": 0,
    }

    # --- Simulated state ---
    # vehicle_id -> source -> SimSourceState
    sim_current: dict[int, dict[str, SimSourceState]] = defaultdict(dict)
    # vehicle_id -> condition_type -> SimCondition
    sim_conditions: dict[int, dict[str, SimCondition]] = defaultdict(dict)

    replay_records: list[ReplayRecord] = []
    per_type_stats = defaultdict(lambda: {"count": 0, "durations": [], "distances": []})

    def find_trip(vehicle_id: int, driver_id: Optional[int], ts: datetime):
        for t in trips:
            if t["vehicle_id"] != vehicle_id:
                continue
            start = t["actual_start_time"]
            end = t["actual_end_time"]
            
            if isinstance(start, str):
                try:
                    start = datetime.fromisoformat(start.replace('Z', '+00:00'))
                except:
                    start = datetime.strptime(start.split('.')[0], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
            if start and getattr(start, 'tzinfo', None) is None:
                start = start.replace(tzinfo=timezone.utc)
            t["actual_start_time"] = start
                
            if isinstance(end, str):
                try:
                    end = datetime.fromisoformat(end.replace('Z', '+00:00'))
                except:
                    end = datetime.strptime(end.split('.')[0], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
            if end and getattr(end, 'tzinfo', None) is None:
                end = end.replace(tzinfo=timezone.utc)
            t["actual_end_time"] = end
                    
            if start and ts >= start and (end is None or ts <= end):
                return t
        return None

    # --- Process events ---
    for idx, event in enumerate(events):
        v_id = event["vehicle_id"]
        evt = event
        
        now = event["timestamp"]
        if isinstance(now, str):
            try:
                now = datetime.fromisoformat(now.replace('Z', '+00:00'))
            except Exception:
                now = datetime.strptime(now.split('.')[0], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)
        
        vehicle_id = evt["vehicle_id"]
        source = evt["source"]
        
        stats["vehicles_replayed"].add(vehicle_id)
        stats["events_replayed"] += 1
        
        if source == "PHONE_GPS":
            stats["phone_events"] += 1
        else:
            stats["hardware_events"] += 1

        # Update simulated current location
        sim_current[vehicle_id][source] = SimSourceState(
            vehicle_id=vehicle_id,
            source=source,
            latitude=evt["latitude"],
            longitude=evt["longitude"],
            speed=evt["speed"],
            heading=evt["heading"],
            accuracy=evt["accuracy"],
            last_timestamp=now,
            last_received_at=evt["created_at"] if evt["created_at"] else now,
        )

        # Get both sources
        phone_state = sim_current[vehicle_id].get("PHONE_GPS")
        hw_state = sim_current[vehicle_id].get("HARDWARE_GPS")

        # Freshness check
        phone_fresh = get_freshness(phone_state, now, "PHONE_GPS")
        hw_fresh = get_freshness(hw_state, now, "HARDWARE_GPS")

        # Skip evaluation if phone (primary) is not available
        if phone_state is None:
            continue

        # Find trip context
        driver_id = evt.get("driver_id")
        company_id = evt.get("company_id")
        trip = find_trip(vehicle_id, driver_id, now)

        # Evaluate active triggers
        active_triggers = set()
        dist = None
        ts_delta = None
        dq_exclusion = None

        if hw_state is not None:
            compat = timestamps_compatible(phone_state, hw_state)
            ts_delta = abs((phone_state.last_timestamp - hw_state.last_timestamp).total_seconds())
            
            if not compat:
                stats["timestamp_skew_exclusions"] += 1
                dq_exclusion = f"timestamp_skew={ts_delta:.0f}s"
            elif phone_fresh == "STALE":
                stats["stale_source_exclusions"] += 1
                dq_exclusion = "phone_gps_stale"
            else:
                stats["comparable_samples"] += 1
                dist = haversine_m(
                    phone_state.latitude, phone_state.longitude,
                    hw_state.latitude, hw_state.longitude
                )
                prox = get_proximity(dist)
                mov = get_movement(phone_state, hw_state)

                if trip and prox == "AWAY_FROM_VEHICLE":
                    active_triggers.add("POTENTIAL_DRIVER_VEHICLE_SEPARATION")
                if mov == "VEHICLE_MOVING_DRIVER_STATIONARY":
                    active_triggers.add("VEHICLE_MOVING_DRIVER_STATIONARY")
                if (phone_fresh == "FRESH" and hw_fresh == "FRESH" and
                        dist > intelligence_config.SIGNIFICANT_SOURCE_DIVERGENCE_METERS):
                    active_triggers.add("GPS_SOURCE_DIVERGENCE")
        else:
            # Only PHONE_GPS available — no dual-source comparison possible
            dq_exclusion = "hardware_gps_unavailable"

        # --- Process conditions ---
        for ctype in ["POTENTIAL_DRIVER_VEHICLE_SEPARATION",
                       "VEHICLE_MOVING_DRIVER_STATIONARY",
                       "GPS_SOURCE_DIVERGENCE"]:
            is_triggered = ctype in active_triggers
            condition = sim_conditions[vehicle_id].get(ctype)

            if is_triggered:
                if condition is None or condition.status == "RESOLVED":
                    # New condition
                    condition = SimCondition(
                        condition_type=ctype,
                        vehicle_id=vehicle_id,
                        driver_id=driver_id,
                        trip_id=trip["id"] if trip else None,
                        company_id=company_id,
                        first_seen_at=now,
                        last_evaluated_at=now,
                        status="ACTIVE",
                        distance_at_open=dist,
                        distance_peak=dist,
                    )
                    sim_conditions[vehicle_id][ctype] = condition
                    stats["conditions_created"] += 1
                    logger.debug(f"  [CONDITION OPEN] {ctype} vehicle={vehicle_id} dist={dist:.0f}m" if dist else f"  [CONDITION OPEN] {ctype} vehicle={vehicle_id}")
                else:
                    # Update condition
                    condition.last_evaluated_at = now
                    if dist and (condition.distance_peak is None or dist > condition.distance_peak):
                        condition.distance_peak = dist

                    # Duration threshold check
                    duration = (now - condition.first_seen_at).total_seconds()
                    if duration >= intelligence_config.MINIMUM_ANOMALY_DURATION_SECONDS and condition.alert_opened_at is None:
                        condition.alert_opened_at = now
                        stats["alerts_would_open"] += 1
                        per_type_stats[ctype]["count"] += 1
                        logger.info(f"  [ALERT OPEN] {ctype} vehicle={vehicle_id} duration={duration:.0f}s dist={dist}")
                    else:
                        stats["duplicate_evals_prevented"] += 1

            else:
                if condition and condition.status == "ACTIVE":
                    condition.status = "RESOLVED"
                    condition.resolved_at = now
                    stats["conditions_resolved"] += 1
                    
                    duration_sec = (condition.resolved_at - condition.first_seen_at).total_seconds()
                    logger.debug(f"  [CONDITION RESOLVED] {ctype} vehicle={vehicle_id} duration={duration_sec:.0f}s dist_peak={condition.distance_peak}")

                    if condition.alert_opened_at is not None:
                        condition.alert_resolved_at = now
                        stats["alerts_would_resolve"] += 1

                        duration_sec = (condition.resolved_at - condition.first_seen_at).total_seconds()
                        per_type_stats[condition.condition_type]["durations"].append(duration_sec)
                        if condition.distance_peak:
                            per_type_stats[condition.condition_type]["distances"].append(condition.distance_peak)

                        replay_records.append(ReplayRecord(
                            vehicle_id=vehicle_id,
                            driver_id=driver_id,
                            condition_type=ctype,
                            first_seen=condition.first_seen_at.isoformat(),
                            alert_open_time=condition.alert_opened_at.isoformat() if condition.alert_opened_at else None,
                            alert_resolved_time=condition.alert_resolved_at.isoformat() if condition.alert_resolved_at else None,
                            duration_seconds=duration_sec,
                            distance=condition.distance_peak,
                            driver_speed_ms=phone_state.speed if phone_state else None,
                            vehicle_speed_ms=hw_state.speed if hw_state else None,
                            driver_accuracy=phone_state.accuracy if phone_state else None,
                            vehicle_accuracy=hw_state.accuracy if hw_state else None,
                            timestamp_delta_sec=ts_delta,
                            trigger_rule=ctype,
                            phone_freshness=phone_fresh,
                            hardware_freshness=hw_fresh,
                            data_quality_exclusion=dq_exclusion,
                        ))

                    logger.debug(f"  [CONDITION RESOLVED] {ctype} vehicle={vehicle_id}")

        if dq_exclusion:
            stats["data_quality_exclusions"] += 1

    # --- Collect still-active conditions as open alerts ---
    for vehicle_id, conditions in sim_conditions.items():
        for ctype, condition in conditions.items():
            if condition.status == "ACTIVE" and condition.alert_opened_at is not None:
                # Alert opened but never resolved — still active at end of replay window
                last_ts = condition.last_evaluated_at
                duration_sec = (last_ts - condition.first_seen_at).total_seconds()
                per_type_stats[condition.condition_type]["durations"].append(duration_sec)
                if condition.distance_peak:
                    per_type_stats[condition.condition_type]["distances"].append(condition.distance_peak)

                replay_records.append(ReplayRecord(
                    vehicle_id=vehicle_id,
                    driver_id=condition.driver_id,
                    condition_type=condition.condition_type,
                    first_seen=condition.first_seen_at.isoformat(),
                    alert_open_time=condition.alert_opened_at.isoformat(),
                    alert_resolved_time=None,
                    duration_seconds=duration_sec,
                    distance=condition.distance_peak,
                    driver_speed_ms=None,
                    vehicle_speed_ms=None,
                    driver_accuracy=None,
                    vehicle_accuracy=None,
                    timestamp_delta_sec=None,
                    trigger_rule=ctype,
                    phone_freshness="UNKNOWN",
                    hardware_freshness="UNKNOWN",
                    data_quality_exclusion=None,
                ))

    # --- Build summary ---
    def pct(series, q):
        if not series:
            return None
        s = sorted(series)
        idx = min(int(len(s) * q), len(s) - 1)
        return s[idx]

    per_type_summary = {}
    for ctype, data in per_type_stats.items():
        durations = data["durations"]
        distances = data["distances"]
        per_type_summary[ctype] = {
            "count": data["count"],
            "median_duration_sec": pct(durations, 0.5),
            "P95_duration_sec": pct(durations, 0.95),
            "median_distance_m": pct(distances, 0.5),
            "P95_distance_m": pct(distances, 0.95),
        }

    # Hysteresis analysis: count rapid open/close cycles per vehicle
    # A "flap" = condition resolved within 2× MINIMUM_ANOMALY_DURATION_SECONDS after opening
    flap_events = []
    for rec in replay_records:
        if rec.alert_open_time and rec.alert_resolved_time and rec.duration_seconds is not None:
            if rec.duration_seconds <= 2 * intelligence_config.MINIMUM_ANOMALY_DURATION_SECONDS:
                flap_events.append(rec)

    hysteresis_summary = {
        "total_resolved_alerts": len([r for r in replay_records if r.alert_resolved_time]),
        "potential_flap_events": len(flap_events),
        "flap_threshold_used_sec": 2 * intelligence_config.MINIMUM_ANOMALY_DURATION_SECONDS,
        "vehicles_with_flap": len({r.vehicle_id for r in flap_events}),
        "median_flap_duration_sec": pct([r.duration_seconds for r in flap_events], 0.5),
        "P95_flap_duration_sec": pct([r.duration_seconds for r in flap_events], 0.95),
    }

    summary = {
        "replay_config": {
            "thresholds_used": {
                "PHONE_GPS_EVENT_STALE_AFTER_SECONDS": intelligence_config.PHONE_GPS_EVENT_STALE_AFTER_SECONDS,
                "HARDWARE_GPS_EVENT_STALE_AFTER_SECONDS": intelligence_config.HARDWARE_GPS_EVENT_STALE_AFTER_SECONDS,
                "MAX_LOCATION_COMPARISON_TIMESTAMP_DELTA_SECONDS": intelligence_config.MAX_LOCATION_COMPARISON_TIMESTAMP_DELTA_SECONDS,
                "DRIVER_VEHICLE_PROXIMITY_METERS": intelligence_config.DRIVER_VEHICLE_PROXIMITY_METERS,
                "DRIVER_VEHICLE_POSSIBLE_PROXIMITY_METERS": intelligence_config.DRIVER_VEHICLE_POSSIBLE_PROXIMITY_METERS,
                "SIGNIFICANT_SOURCE_DIVERGENCE_METERS": intelligence_config.SIGNIFICANT_SOURCE_DIVERGENCE_METERS,
                "VEHICLE_MOVING_SPEED_THRESHOLD_KMH": intelligence_config.VEHICLE_MOVING_SPEED_THRESHOLD_KMH,
                "DRIVER_STATIONARY_SPEED_THRESHOLD_KMH": intelligence_config.DRIVER_STATIONARY_SPEED_THRESHOLD_KMH,
                "MINIMUM_ANOMALY_DURATION_SECONDS": intelligence_config.MINIMUM_ANOMALY_DURATION_SECONDS,
            },
            "start_time": start_time.isoformat() if start_time else None,
            "end_time": end_time.isoformat() if end_time else None,
            "vehicle_ids_filter": vehicle_ids,
            "company_ids_filter": company_ids,
        },
        "totals": {
            "vehicles_replayed": len(stats["vehicles_replayed"]),
            "events_replayed": stats["events_replayed"],
            "phone_gps_events": stats["phone_events"],
            "hardware_gps_events": stats["hardware_events"],
            "comparable_source_samples": stats["comparable_samples"],
            "conditions_created": stats["conditions_created"],
            "conditions_resolved": stats["conditions_resolved"],
            "alerts_that_would_open": stats["alerts_would_open"],
            "alerts_that_would_resolve": stats["alerts_would_resolve"],
            "duplicate_evals_prevented": stats["duplicate_evals_prevented"],
            "data_quality_exclusions": stats["data_quality_exclusions"],
            "timestamp_skew_exclusions": stats["timestamp_skew_exclusions"],
            "stale_source_exclusions": stats["stale_source_exclusions"],
        },
        "per_anomaly_type": per_type_summary,
        "hysteresis_analysis": hysteresis_summary,
    }

    # --- Write outputs ---
    with open(out_json, "w") as f:
        report_data = {"summary": summary, "records": [asdict(r) for r in replay_records]}
        json.dump(report_data, f, indent=2)
    logger.info(f"Replay report (JSON) saved to: {out_json}")

    with open(out_csv, "w", newline="") as f:
        if replay_records:
            writer = csv.DictWriter(f, fieldnames=asdict(replay_records[0]).keys())
            writer.writeheader()
            writer.writerows(asdict(r) for r in replay_records)
        else:
            f.write("No alert-generating conditions were detected in the replay window.\n")
    logger.info(f"Replay report (CSV) saved to: {out_csv}")

    # --- Print summary ---
    logger.info("=== REPLAY SUMMARY ===")
    for k, v in summary["totals"].items():
        logger.info(f"  {k}: {v}")
    logger.info("--- Per Anomaly Type ---")
    for ctype, data in per_type_summary.items():
        logger.info(f"  {ctype}: {data}")
    logger.info("--- Hysteresis Analysis ---")
    for k, v in hysteresis_summary.items():
        logger.info(f"  {k}: {v}")


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FleetGuard Intelligence Replay")
    parser.add_argument("--start", help="Start datetime (ISO format, UTC)", default=None)
    parser.add_argument("--end", help="End datetime (ISO format, UTC)", default=None)
    parser.add_argument("--vehicles", help="Comma-separated vehicle IDs", default=None)
    parser.add_argument("--companies", help="Comma-separated company IDs", default=None)
    parser.add_argument("--out-csv", default="phase5_replay_report.csv")
    parser.add_argument("--out-json", default="phase5_replay_report.json")
    parser.add_argument("--config", default=None, help="Path to JSON config with candidate thresholds")
    parser.add_argument("--db-url", default=None, help="Optional DB URL for testing (e.g. sqlite+aiosqlite:///test.db)")
    args = parser.parse_args()

    if args.config:
        logger.info(f"Loading candidate config from: {args.config}")
        intelligence_config.load_from_json(args.config)

    start_dt = datetime.fromisoformat(args.start).replace(tzinfo=timezone.utc) if args.start else None
    end_dt = datetime.fromisoformat(args.end).replace(tzinfo=timezone.utc) if args.end else None
    vids = [int(x) for x in args.vehicles.split(",")] if args.vehicles else None
    cids = [int(x) for x in args.companies.split(",")] if args.companies else None

    asyncio.run(run_replay(
        start_time=start_dt,
        end_time=end_dt,
        vehicle_ids=vids,
        company_ids=cids,
        out_csv=args.out_csv,
        out_json=args.out_json,
        db_url=args.db_url,
    ))
