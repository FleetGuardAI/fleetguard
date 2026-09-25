import argparse
import asyncio
import json
import logging
from datetime import datetime, timezone
import pandas as pd
import numpy as np
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from database import engine as default_engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("audit_data_quality")

# Haversine distance
def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  # radius of Earth in meters
    phi1 = np.radians(lat1)
    phi2 = np.radians(lat2)
    delta_phi = np.radians(lat2 - lat1)
    delta_lambda = np.radians(lon2 - lon1)
    a = np.sin(delta_phi/2.0)**2 + np.cos(phi1) * np.cos(phi2) * np.sin(delta_lambda/2.0)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    return R * c

def compute_percentiles(series):
    s = series.dropna()
    if len(s) == 0:
        return {}
    return {
        "min": float(s.min()),
        "median": float(s.median()),
        "mean": float(s.mean()),
        "P75": float(s.quantile(0.75)),
        "P90": float(s.quantile(0.90)),
        "P95": float(s.quantile(0.95)),
        "P99": float(s.quantile(0.99)),
        "max": float(s.max())
    }

async def fetch_data(query):
    async with engine.connect() as conn:
        res = await conn.execute(text(query))
        return [dict(r._mapping) for r in res]

async def run_audit(out_csv: str, out_json: str, db_url: str = None):
    logger.info("=== FleetGuard Phase 5 — Production Data Quality Audit ===")
    
    global engine
    if db_url:
        engine = create_async_engine(db_url)
    else:
        engine = default_engine
        
    async with engine.connect() as conn:
        pass

    report = {}

    # 1. Dataset Inventory
    vl_count = await fetch_data("SELECT COUNT(*) as c FROM vehicle_locations")
    vcl_count = await fetch_data("SELECT COUNT(*) as c FROM vehicle_current_locations")
    v_count = await fetch_data("SELECT COUNT(*) as c FROM vehicles")
    d_count = await fetch_data("SELECT COUNT(*) as c FROM drivers")
    t_count = await fetch_data("SELECT COUNT(*) as c FROM trips")
    
    vl_rows = await fetch_data("SELECT * FROM vehicle_locations ORDER BY timestamp ASC")
    df_vl = pd.DataFrame(vl_rows)

    if df_vl.empty:
        logger.warning("No data found in vehicle_locations.")
        return

    # Convert times
    for col in ['timestamp', 'created_at']:
        df_vl[col] = pd.to_datetime(df_vl[col], utc=True)

    report['Dataset_Inventory'] = {
        "Total_VehicleLocation_rows": int(vl_count[0]['c']),
        "Total_VehicleCurrentLocation_rows": int(vcl_count[0]['c']),
        "Total_vehicles": int(v_count[0]['c']),
        "Total_drivers": int(d_count[0]['c']),
        "Total_trips": int(t_count[0]['c']),
        "Total_PHONE_GPS_events": int(len(df_vl[df_vl['source'] == 'PHONE_GPS'])),
        "Total_HARDWARE_GPS_events": int(len(df_vl[df_vl['source'] == 'HARDWARE_GPS'])),
        "Oldest_location_timestamp": str(df_vl['timestamp'].min()),
        "Newest_location_timestamp": str(df_vl['timestamp'].max()),
        "Oldest_received_timestamp": str(df_vl['created_at'].min()),
        "Newest_received_timestamp": str(df_vl['created_at'].max()),
    }

    # 2. Dual-Source Coverage
    vehicles = df_vl.groupby('vehicle_id')['source'].unique()
    v_phone = [v for v, sources in vehicles.items() if 'PHONE_GPS' in sources]
    v_hardware = [v for v, sources in vehicles.items() if 'HARDWARE_GPS' in sources]
    v_both = [v for v in v_phone if v in v_hardware]
    v_only_phone = [v for v in v_phone if v not in v_hardware]
    v_only_hardware = [v for v in v_hardware if v not in v_phone]

    report['Dual_Source_Coverage'] = {
        "Vehicles_with_PHONE_GPS": len(v_phone),
        "Vehicles_with_HARDWARE_GPS": len(v_hardware),
        "Vehicles_with_both": len(v_both),
        "Vehicles_with_only_PHONE_GPS": len(v_only_phone),
        "Vehicles_with_only_HARDWARE_GPS": len(v_only_hardware),
        "Percentage_both": float(len(v_both) / len(vehicles) * 100) if len(vehicles) > 0 else 0
    }

    # 3 & 4. Update Frequency
    df_vl = df_vl.sort_values(by=['vehicle_id', 'source', 'timestamp'])
    df_vl['prev_timestamp'] = df_vl.groupby(['vehicle_id', 'source'])['timestamp'].shift(1)
    df_vl['interval_sec'] = (df_vl['timestamp'] - df_vl['prev_timestamp']).dt.total_seconds()

    for source in ['PHONE_GPS', 'HARDWARE_GPS']:
        src_df = df_vl[(df_vl['source'] == source) & (df_vl['interval_sec'].notna())]
        intervals = src_df['interval_sec']
        
        report[f'{source}_Update_Frequency'] = compute_percentiles(intervals)
        report[f'{source}_Update_Frequency']['Gap_Distribution'] = {
            "< 10 sec": int(len(intervals[intervals < 10])),
            "10-30 sec": int(len(intervals[(intervals >= 10) & (intervals < 30)])),
            "30-60 sec": int(len(intervals[(intervals >= 30) & (intervals < 60)])),
            "1-2 min": int(len(intervals[(intervals >= 60) & (intervals < 120)])),
            "2-5 min": int(len(intervals[(intervals >= 120) & (intervals < 300)])),
            "5-10 min": int(len(intervals[(intervals >= 300) & (intervals < 600)])),
            "10-30 min": int(len(intervals[(intervals >= 600) & (intervals < 1800)])),
            "> 30 min": int(len(intervals[intervals >= 1800]))
        }

    # 5. GPS Accuracy Distribution
    for source in ['PHONE_GPS', 'HARDWARE_GPS']:
        src_df = df_vl[df_vl['source'] == source]
        acc = src_df['accuracy'].dropna()
        report[f'{source}_Accuracy_Distribution'] = compute_percentiles(acc)
        report[f'{source}_Accuracy_Distribution']['Bands'] = {
            "<= 5m": int(len(acc[acc <= 5])),
            "5-10m": int(len(acc[(acc > 5) & (acc <= 10)])),
            "10-25m": int(len(acc[(acc > 10) & (acc <= 25)])),
            "25-50m": int(len(acc[(acc > 25) & (acc <= 50)])),
            "50-100m": int(len(acc[(acc > 50) & (acc <= 100)])),
            "> 100m": int(len(acc[acc > 100])),
            "missing": int(src_df['accuracy'].isna().sum())
        }

    # 6. Timestamp Quality
    now = pd.Timestamp.now(tz='UTC')
    df_vl['ingestion_delay'] = (df_vl['created_at'] - df_vl['timestamp']).dt.total_seconds()
    
    for source in ['PHONE_GPS', 'HARDWARE_GPS']:
        src_df = df_vl[df_vl['source'] == source]
        delay = src_df['ingestion_delay'].dropna()
        report[f'{source}_Timestamp_Quality'] = {
            "future_timestamps": int(len(src_df[src_df['timestamp'] > now])),
            "zero_invalid": int(len(src_df[src_df['timestamp'] == pd.Timestamp("1970-01-01", tz='UTC')])),
            "ingestion_delay_percentiles": compute_percentiles(delay)
        }

    # 7 & 8. Timestamp Compatibility & Distance
    phone_df = df_vl[df_vl['source'] == 'PHONE_GPS'].copy()
    hw_df = df_vl[df_vl['source'] == 'HARDWARE_GPS'].copy()
    
    phone_df = phone_df.sort_values(['vehicle_id', 'timestamp'])
    hw_df = hw_df.sort_values(['vehicle_id', 'timestamp'])
    
    if not phone_df.empty and not hw_df.empty:
        # Build a clean subset for merging to avoid column name collisions
        hw_merge = hw_df[['vehicle_id', 'timestamp', 'latitude', 'longitude', 'speed', 'accuracy']].copy()
        hw_merge = hw_merge.rename(columns={
            'timestamp': 'hw_timestamp',
            'latitude': 'latitude_hw',
            'longitude': 'longitude_hw',
            'speed': 'speed_hw',
            'accuracy': 'accuracy_hw',
        })
        hw_merge = hw_merge.sort_values(['vehicle_id', 'hw_timestamp'])
        
        phone_merge = phone_df[['vehicle_id', 'timestamp', 'latitude', 'longitude', 'speed', 'accuracy']].copy()
        phone_merge = phone_merge.rename(columns={
            'latitude': 'latitude_phone',
            'longitude': 'longitude_phone',
            'speed': 'speed_phone',
            'accuracy': 'accuracy_phone',
        })
        phone_merge = phone_merge.sort_values(['vehicle_id', 'timestamp'])

        merged = pd.merge_asof(
            phone_merge, hw_merge,
            by='vehicle_id',
            left_on='timestamp',
            right_on='hw_timestamp',
            direction='nearest',
        )
        merged['ts_delta'] = (merged['timestamp'] - merged['hw_timestamp']).abs().dt.total_seconds()
        
        delta = merged['ts_delta'].dropna()
        report['Timestamp_Compatibility'] = compute_percentiles(delta)
        report['Timestamp_Compatibility']['Bands'] = {
            "<= 10 sec": int(len(delta[delta <= 10])),
            "<= 30 sec": int(len(delta[delta <= 30])),
            "<= 60 sec": int(len(delta[delta <= 60])),
            "<= 120 sec": int(len(delta[delta <= 120])),
            "> 120 sec": int(len(delta[delta > 120])),
        }
        
        # Distance Distribution for compatible samples
        compat = merged[merged['ts_delta'] <= 120].dropna(subset=['latitude_phone', 'latitude_hw']).copy()
        if not compat.empty:
            compat['dist'] = haversine(
                compat['latitude_phone'].values, compat['longitude_phone'].values,
                compat['latitude_hw'].values, compat['longitude_hw'].values
            )
            dist = compat['dist'].dropna()
            report['Distance_Distribution'] = compute_percentiles(dist)
            report['Distance_Distribution']['sample_size'] = int(len(dist))
            report['Distance_Distribution']['Bands'] = {
                "0-10m": int(len(dist[dist <= 10])),
                "10-25m": int(len(dist[(dist > 10) & (dist <= 25)])),
                "25-50m": int(len(dist[(dist > 25) & (dist <= 50)])),
                "50-100m": int(len(dist[(dist > 50) & (dist <= 100)])),
                "100-200m": int(len(dist[(dist > 100) & (dist <= 200)])),
                "200-500m": int(len(dist[(dist > 200) & (dist <= 500)])),
                "500-1000m": int(len(dist[(dist > 500) & (dist <= 1000)])),
                "1-2km": int(len(dist[(dist > 1000) & (dist <= 2000)])),
                "> 2km": int(len(dist[dist > 2000]))
            }
            
            # Segment Distance: speeds in DB are m/s, convert to km/h for threshold comparison
            compat['speed_hw_kmh'] = compat['speed_hw'] * 3.6
            compat['speed_phone_kmh'] = compat['speed_phone'] * 3.6
            
            # Both stationary: vehicle speed <= 2 km/h
            stationary = compat[(compat['speed_hw_kmh'] <= 2.0) & (compat['speed_phone_kmh'] <= 2.0)]
            # Both/either moving: vehicle speed > 10 km/h
            moving = compat[(compat['speed_hw_kmh'] > 10.0) | (compat['speed_phone_kmh'] > 10.0)]
            
            report['Segment_Distance'] = {
                "filter_criteria": "Both fresh + compat timestamp (<=120s). Stationary: vehicle+driver speed <= 2km/h. Moving: vehicle or driver speed > 10km/h.",
                "Stationary": {**compute_percentiles(stationary['dist']), "sample_size": int(len(stationary))} if not stationary.empty else {"sample_size": 0},
                "Moving": {**compute_percentiles(moving['dist']), "sample_size": int(len(moving))} if not moving.empty else {"sample_size": 0}
            }
    
    # 10. Speed Distribution
    for source in ['PHONE_GPS', 'HARDWARE_GPS']:
        src_df = df_vl[df_vl['source'] == source]
        spd = src_df['speed'].dropna() * 3.6 # Assuming m/s, convert to km/h
        report[f'{source}_Speed_Distribution'] = compute_percentiles(spd)
        report[f'{source}_Speed_Distribution']['Bands'] = {
            "0": int(len(spd[spd == 0])),
            "0-2": int(len(spd[(spd > 0) & (spd <= 2)])),
            "2-5": int(len(spd[(spd > 2) & (spd <= 5)])),
            "5-10": int(len(spd[(spd > 5) & (spd <= 10)])),
            "10-20": int(len(spd[(spd > 10) & (spd <= 20)])),
            "20-40": int(len(spd[(spd > 20) & (spd <= 40)])),
            "40-60": int(len(spd[(spd > 40) & (spd <= 60)])),
            "60-80": int(len(spd[(spd > 60) & (spd <= 80)])),
            "> 80": int(len(spd[spd > 80]))
        }
        
    # 11. Heading Quality
    for source in ['PHONE_GPS', 'HARDWARE_GPS']:
        src_df = df_vl[df_vl['source'] == source]
        valid_heading = src_df['heading'].dropna()
        invalid = valid_heading[(valid_heading < 0) | (valid_heading > 360)]
        report[f'{source}_Heading_Quality'] = {
            "with_heading": int(src_df['heading'].notna().sum()),
            "missing_heading": int(src_df['heading'].isna().sum()),
            "invalid_heading": int(len(invalid))
        }
        
    # 12. Duplicate and Out-of-Order
    for source in ['PHONE_GPS', 'HARDWARE_GPS']:
        src_df = df_vl[df_vl['source'] == source]
        report[f'{source}_Duplicates_And_Ordering'] = {
            "duplicate_fingerprints": int(src_df['event_fingerprint'].duplicated().sum()) if 'event_fingerprint' in src_df else 0,
            "out_of_order_events": int(len(src_df[src_df['timestamp'] < src_df['prev_timestamp']]))
        }
        
    # Save reports
    with open(out_json, "w") as f:
        json.dump(report, f, indent=2)
        
    logger.info(f"Data Quality Audit complete. Report saved to {out_json}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FleetGuard Production Data Quality Audit")
    parser.add_argument("--out-csv", default="phase5_data_quality_report.csv")
    parser.add_argument("--out-json", default="phase5_data_quality_report.json")
    parser.add_argument("--db-url", default=None, help="Optional DB URL for testing")
    args = parser.parse_args()

    asyncio.run(run_audit(args.out_csv, args.out_json, args.db_url))
