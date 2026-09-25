"""
FleetGuard Phase 6B — Reproducible Calibration Pipeline

Automates the calibration feedback loop by generating a candidate_config.json,
running the replay_intelligence.py engine, and parsing the results to help 
determine optimal production thresholds.

Usage:
    python scripts/calibrate_intelligence.py --vehicle-id 101 --start YYYY-MM-DD
"""

import argparse
import json
import subprocess
import os
import sys

def generate_candidate_config(config_path, overrides):
    with open(config_path, 'w') as f:
        json.dump(overrides, f, indent=4)
    print(f"Generated candidate config: {config_path}")

def run_replay(config_path, vehicle_id, start_time=None, db_url=None):
    cmd = [
        sys.executable,
        "scripts/replay_intelligence.py",
        "--config", config_path,
        "--out-json", "calibration_replay_report.json"
    ]
    if vehicle_id:
        cmd.extend(["--vehicles", str(vehicle_id)])
    if start_time:
        cmd.extend(["--start", start_time])
    if db_url:
        cmd.extend(["--db-url", db_url])
        
    print(f"Running replay engine with {config_path}...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("Replay failed!")
        print(result.stderr)
        sys.exit(1)
        
    with open("calibration_replay_report.json", 'r') as f:
        report = json.load(f)
    return report

def summarize_report(report, config_name):
    summary = report.get("summary", {})
    totals = summary.get("totals", {})
    print(f"\n=== {config_name} Summary ===")
    print(f"Alerts that would open:    {totals.get('alerts_that_would_open', 0)}")
    print(f"Conditions created:        {totals.get('conditions_created', 0)}")
    print(f"Data Quality Exclusions:   {totals.get('data_quality_exclusions', 0)}")
    
    per_type = summary.get("per_anomaly_type", {})
    for ctype, data in per_type.items():
        if data.get("count", 0) > 0:
            print(f"  - {ctype}: {data['count']} alerts (Median dist: {data.get('median_distance_m')}m)")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--vehicle-id", type=int, help="Vehicle to calibrate against")
    parser.add_argument("--start", type=str, help="Start time (ISO UTC)")
    parser.add_argument("--db-url", type=str, help="Optional Database URL")
    args = parser.parse_args()
    
    # 1. Baseline Run (Empty overrides = Production Config)
    generate_candidate_config("candidate_baseline.json", {})
    baseline_report = run_replay("candidate_baseline.json", args.vehicle_id, args.start, args.db_url)
    summarize_report(baseline_report, "BASELINE (Production Config)")
    
    # 2. Strict Calibration Run (Tighter thresholds)
    strict_overrides = {
        "DRIVER_VEHICLE_PROXIMITY_METERS": 30.0,
        "DRIVER_VEHICLE_POSSIBLE_PROXIMITY_METERS": 100.0,
        "MINIMUM_ANOMALY_DURATION_SECONDS": 180,
    }
    generate_candidate_config("candidate_strict.json", strict_overrides)
    strict_report = run_replay("candidate_strict.json", args.vehicle_id, args.start, args.db_url)
    summarize_report(strict_report, "STRICT CONFIG")
    
    # 3. Lenient Calibration Run (Looser thresholds)
    lenient_overrides = {
        "DRIVER_VEHICLE_PROXIMITY_METERS": 100.0,
        "DRIVER_VEHICLE_POSSIBLE_PROXIMITY_METERS": 300.0,
        "MINIMUM_ANOMALY_DURATION_SECONDS": 600,
        "MAX_LOCATION_COMPARISON_TIMESTAMP_DELTA_SECONDS": 300
    }
    generate_candidate_config("candidate_lenient.json", lenient_overrides)
    lenient_report = run_replay("candidate_lenient.json", args.vehicle_id, args.start, args.db_url)
    summarize_report(lenient_report, "LENIENT CONFIG")
    
    print("\nCalibration pipeline complete. Compare the results against ground-truth logs to select the best configuration.")

if __name__ == "__main__":
    main()
