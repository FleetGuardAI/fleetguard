"""
FleetGuard Phase 6B — Ground Truth Logger

Interactive CLI tool for field testers to log exact timestamps of physical events 
during the real-world dual-GPS pilot.

Usage:
    python scripts/record_ground_truth.py --vehicle-id 101 --driver-id 42
"""

import argparse
import csv
import json
import os
from datetime import datetime, timezone
import termios
import sys
import tty

EVENTS = {
    "1": "STATIONARY_START",
    "2": "STATIONARY_END",
    "3": "DRIVER_EXIT_CAB",
    "4": "DRIVER_ENTER_CAB",
    "5": "WALK_25M",
    "6": "WALK_50M",
    "7": "WALK_75M",
    "8": "WALK_100M",
    "9": "WALK_200M_PLUS",
    "d": "DRIVING_NORMAL_START",
    "p": "PARKED_START",
    "o": "GPS_OUTAGE_SIMULATED",
    "r": "GPS_OUTAGE_RESTORED",
    "c": "CUSTOM_NOTE",
    "q": "QUIT"
}

def getch():
    """Read a single character without needing Enter (Unix-specific).
    For cross-platform, fallback to input() if termios fails."""
    try:
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch
    except Exception:
        # Fallback for Windows
        return input("Choice: ").strip()[:1]

def main():
    parser = argparse.ArgumentParser(description="Phase 6B Field Test - Ground Truth Logger")
    parser.add_argument("--vehicle-id", type=int, required=True, help="Test Vehicle ID")
    parser.add_argument("--driver-id", type=int, required=True, help="Test Driver ID")
    parser.add_argument("--out", type=str, default="phase6b_ground_truth.csv", help="Output file")
    args = parser.parse_args()

    out_file = args.out
    is_new_file = not os.path.exists(out_file)

    print(f"=== FleetGuard Ground Truth Logger ===")
    print(f"Vehicle: {args.vehicle_id} | Driver: {args.driver_id}")
    print(f"Logging to: {out_file}\n")
    
    print("Available Events:")
    for key, name in EVENTS.items():
        print(f"  [{key}] : {name}")
    print("--------------------------------------")
    print("Press a key to log an event at the current UTC time.\n")

    with open(out_file, mode='a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["timestamp", "vehicle_id", "driver_id", "event_type", "notes"])
        if is_new_file:
            writer.writeheader()

        while True:
            # Note: For reliable usage in Windows PS, getch fallback uses input()
            print("Select Event -> ", end="", flush=True)
            choice = getch().lower()
            if choice == '\r' or choice == '\n':
                continue
                
            if choice not in EVENTS:
                if choice != '\x03': # Ctrl+C
                    print(f"\n[!] Unknown choice: {choice}")
                continue

            event_type = EVENTS[choice]
            now = datetime.now(timezone.utc)
            
            if choice == "q" or choice == '\x03':
                print(f"\nExiting... Logs saved to {out_file}")
                break
                
            notes = ""
            if choice == "c":
                print(f"\nCustom Note: ", end="", flush=True)
                notes = input().strip()
                
            record = {
                "timestamp": now.isoformat(),
                "vehicle_id": args.vehicle_id,
                "driver_id": args.driver_id,
                "event_type": event_type,
                "notes": notes
            }
            writer.writerow(record)
            f.flush()
            
            print(f"\n[✔] {now.strftime('%H:%M:%S UTC')} | Logged: {event_type} {notes}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting...")
