import asyncio
from fastapi.testclient import TestClient
from main import app
from database import get_db, async_session_factory
import json
from datetime import datetime
import uuid

client = TestClient(app)

def run_e2e_test():
    print("Starting E2E Data Flow Test...")
    
    try:
        # 1. OWNER LOGS IN
        login_resp = client.post("/api/v1/auth/login", json={"email": "admin@example.com", "password": "password"})
        if login_resp.status_code != 200:
            print(f"1. Failed to login. Using fallback admin token creation or check seed. {login_resp.text}")
            return
            
        owner_token = login_resp.json()["access_token"]
        owner_headers = {"Authorization": f"Bearer {owner_token}"}
        print("1. Owner logged in.")

        # 2. CREATE FLEET INVITATION
        invite_resp = client.post(
            "/api/v1/fleet/invite",
            json={"phone_number": "+919999999999", "role": "DRIVER"},
            headers=owner_headers
        )
        if invite_resp.status_code not in (200, 201):
            print("2. Failed to create invite", invite_resp.text)
            return
        invite_code = invite_resp.json().get("invite_token")
        print(f"2. Owner created driver invitation: {invite_code}")

        # 3. DRIVER VERIFIES QR
        verify_invite = client.post("/api/v1/driver-app/verify-invite", json={"invite_token": invite_code})
        print("3. Driver verified invite QR:", verify_invite.json())

        # 4. DRIVER SENDS OTP AND VERIFIES
        client.post("/api/v1/driver-app/send-otp", json={"phone_number": "+919999999999"})
        otp_resp = client.post("/api/v1/driver-app/verify-otp", json={
            "phone_number": "+919999999999",
            "otp_code": "123456",
            "invite_token": invite_code
        })
        if otp_resp.status_code not in (200, 201):
            print("4. Failed to verify OTP:", otp_resp.text)
            return
        driver_token = otp_resp.json()["access_token"]
        driver_headers = {"Authorization": f"Bearer {driver_token}"}
        
        # DRIVER REGISTERS PROFILE
        register_resp = client.post("/api/v1/driver-app/register", json={
            "name": "Test Driver",
            "phone_number": "+919999999999",
            "fcm_token": "mock-token"
        }, headers=driver_headers)
        if register_resp.status_code not in (200, 201):
            print("4. Failed to register driver profile:", register_resp.text)
            return
            
        driver_id = register_resp.json()["id"]
        print(f"4. Driver registered successfully. ID: {driver_id}")

        # 5. OWNER SEES DRIVER
        drivers_resp = client.get("/api/v1/drivers", headers=owner_headers)
        if drivers_resp.status_code == 200:
            driver_found = any(d["id"] == driver_id for d in drivers_resp.json())
            print(f"5. Owner sees driver in fleet: {driver_found}")
        else:
            print("5. Failed to fetch drivers:", drivers_resp.text)

        # 6. OWNER CREATES TRUCK
        truck_reg = f"TEST-{str(uuid.uuid4())[:8].upper()}"
        truck_resp = client.post("/api/v1/vehicles", json={
            "registration_number": truck_reg,
            "make": "Tata",
            "model": "Prima",
            "year": 2024,
            "capacity_tonnes": 40.0,
            "status": "ACTIVE"
        }, headers=owner_headers)
        if truck_resp.status_code not in (200, 201):
            print("6. Failed to create truck", truck_resp.text)
            return
        truck_id = truck_resp.json()["id"]
        print(f"6. Owner created truck {truck_reg} with ID: {truck_id}")

        # 7. OWNER ASSIGNS DRIVER (Updating Vehicle)
        assign_resp = client.patch(f"/api/v1/vehicles/{truck_id}", json={"driver_id": driver_id}, headers=owner_headers)
        print("7. Owner assigned driver to truck.", assign_resp.status_code)

        # 8. DRIVER SEES TRUCK
        driver_profile = client.get("/api/v1/driver-app/profile", headers=driver_headers)
        print("8. Driver profile assigned_vehicle:", driver_profile.json().get("assigned_vehicle"))

        # 9. OWNER CREATES TRIP
        print("9. Owner creating trip...")
        trip_event = client.post("/api/v1/trips", json={
            "origin_location": "Delhi",
            "destination_location": "Mumbai",
            "vehicle_id": truck_id,
            "driver_id": driver_id
        }, headers=owner_headers)
        if trip_event.status_code not in (200, 201):
            print("9. Failed to create trip:", trip_event.text)
            return
        
        trip_resp_json = trip_event.json()
        trip_db_id = trip_resp_json["id"]
        trip_business_id = trip_resp_json["trip_id"]
        print(f"9. Owner created trip: {trip_business_id}")

        # 10. DRIVER SEES TRIP
        driver_trips = client.get("/api/v1/driver-app/trips/active", headers=driver_headers)
        print("10. Driver active trips:", driver_trips.status_code, driver_trips.text)

        # 11. DRIVER STARTS TRIP
        trip_start = client.post(f"/api/v1/driver-app/trips/{trip_db_id}/start", headers=driver_headers)
        print("11. Driver starts trip:", trip_start.status_code)

        # 12. OWNER SEES UPDATED TRIP STATUS
        owner_trips = client.get("/api/v1/owner/dashboard/trips", headers=owner_headers)
        print("12. Owner trips endpoint response:", owner_trips.status_code, [t["status"] for t in owner_trips.json()])

        # 13. DRIVER SENDS GPS
        gps_resp = client.post("/api/v1/driver-app/location/batch", json={
            "driver_id": driver_id,
            "locations": [{
                "latitude": 28.7041,
                "longitude": 77.1025,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "source": "PHONE_GPS"
            }]
        }, headers=driver_headers)
        print("13. Driver sent GPS:", gps_resp.status_code)

        # 14. OWNER SEES GPS
        owner_gps = client.get("/api/v1/tracking/fleet/live", headers=owner_headers)
        print("14. Owner fleet live tracking:", owner_gps.status_code, owner_gps.text)

        # 15. DRIVER CREATES EXPENSE
        expense_resp = client.post("/api/v1/driver-app/expenses", json={
            "category": "FUEL",
            "amount": 1000.0,
            "vehicle_id": truck_id,
            "trip_id": trip_db_id,
            "driver_id": driver_id,
            "description": "Test Fuel"
        }, headers=driver_headers)
        print("15. Driver created expense:", expense_resp.status_code)

        # 16. OWNER APPROVES EXPENSE
        expense_db_id = expense_resp.json()["id"]
        approve_resp = client.patch(f"/api/v1/owner/dashboard/expenses/{expense_db_id}/approve", headers=owner_headers)
        print("16. Owner approved expense:", approve_resp.status_code)

        # Wait for dashboard KPIs to reflect
        kpis = client.get("/api/v1/owner/dashboard/kpis", headers=owner_headers)
        print("16. Owner Dashboard KPIs after approval:", kpis.status_code, kpis.text)

        print("E2E Test Summary printed.")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error during E2E: {e}")

if __name__ == "__main__":
    run_e2e_test()
