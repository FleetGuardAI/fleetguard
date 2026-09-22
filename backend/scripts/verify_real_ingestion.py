import asyncio
import json
from sqlalchemy import text
from database import engine

async def verify_real_ingestion():
    print("=== FleetGuard Integration Test: Real Driver App Ingestion Verification ===")
    
    async with engine.connect() as conn:
        # Get location counts
        res = await conn.execute(text("""
            SELECT source, COUNT(*) as count 
            FROM vehicle_locations 
            WHERE vehicle_id = 9999
            GROUP BY source
        """))
        counts = {row.source: row.count for row in res.fetchall()}
        
        print(f"\n[1] Events Received:")
        print(f"  - PHONE_GPS: {counts.get('PHONE_GPS', 0)}")
        print(f"  - HARDWARE_GPS: {counts.get('HARDWARE_GPS', 0)}")
        
        # Check latency and duplicates
        res = await conn.execute(text("""
            SELECT id, timestamp, created_at, event_fingerprint 
            FROM vehicle_locations 
            WHERE vehicle_id = 9999 AND source = 'PHONE_GPS'
            ORDER BY timestamp ASC
        """))
        phone_events = res.fetchall()
        
        if not phone_events:
            print("\nWARNING: No PHONE_GPS events found! The Driver App did not send data, or vehicle/driver association failed.")
            return

        total_latency = 0
        max_latency = 0
        fingerprints = set()
        duplicates = 0
        out_of_order = 0
        last_ts = None
        
        for ev in phone_events:
            if ev.event_fingerprint in fingerprints:
                duplicates += 1
            fingerprints.add(ev.event_fingerprint)
            
            if last_ts and ev.timestamp < last_ts:
                out_of_order += 1
            last_ts = ev.timestamp
            
            latency = (ev.created_at - ev.timestamp).total_seconds()
            total_latency += latency
            if latency > max_latency:
                max_latency = latency
                
        avg_latency = total_latency / len(phone_events)
        
        print(f"\n[2] Ingestion Quality:")
        print(f"  - Average E2E Latency: {avg_latency:.2f} seconds")
        print(f"  - Max E2E Latency: {max_latency:.2f} seconds")
        print(f"  - Duplicates Detected: {duplicates}")
        print(f"  - Out-of-Order Events: {out_of_order}")
        
        # Check intelligence engine
        res = await conn.execute(text("""
            SELECT condition_type, status, first_seen_at, last_evaluated_at 
            FROM intelligence_conditions 
            WHERE vehicle_id = 9999
        """))
        conditions = res.fetchall()
        
        print(f"\n[3] Intelligence Engine Activity:")
        if not conditions:
            print("  - No active conditions generated.")
            print("  - Note: This might be expected if the test was brief or no rules were violated.")
        else:
            for cond in conditions:
                eval_duration = (cond.last_evaluated_at - cond.first_seen_at).total_seconds()
                print(f"  - [{cond.status}] {cond.condition_type} (Evaluated over {eval_duration:.0f}s)")
        
        # Output small report payload
        report = {
            "phone_events_received": counts.get('PHONE_GPS', 0),
            "hardware_events_mocked": counts.get('HARDWARE_GPS', 0),
            "avg_latency_sec": round(avg_latency, 2),
            "duplicates": duplicates,
            "out_of_order": out_of_order,
            "conditions_processed": len(conditions)
        }
        
        with open("integration_test_report.json", "w") as f:
            json.dump(report, f, indent=2)
            
        print("\nIntegration test verification complete. Report written to integration_test_report.json")

if __name__ == "__main__":
    asyncio.run(verify_real_ingestion())
