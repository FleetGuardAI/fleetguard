import uuid
import random
import pytest
from fastapi.testclient import TestClient
from main import app


def test_cross_app_sync_and_isolation():
    with TestClient(app) as client:
        # --- Setup: Register two companies ---
        id_a = str(uuid.uuid4())[:8]
        id_b = str(uuid.uuid4())[:8]

        mob_a = f"99{random.randint(10000000, 99999999)}"
        mob_b = f"99{random.randint(10000000, 99999999)}"

        comp_a = client.post("/api/v1/auth/register", json={
            "company_name": f"Company A Sync {id_a}",
            "owner_name": f"Owner A {id_a}",
            "mobile_number": mob_a,
            "email": f"ownera_{id_a}@sync.com",
            "password": "password123",
            "confirm_password": "password123"
        })

        comp_b = client.post("/api/v1/auth/register", json={
            "company_name": f"Company B Sync {id_b}",
            "owner_name": f"Owner B {id_b}",
            "mobile_number": mob_b,
            "email": f"ownerb_{id_b}@sync.com",
            "password": "password123",
            "confirm_password": "password123"
        })

        # Assert successful creation
        assert comp_a.status_code in [200, 201], f"A failed: {comp_a.text}"
        assert comp_b.status_code in [200, 201], f"B failed: {comp_b.text}"

        token_a = comp_a.json()["token"]["access_token"]
        token_b = comp_b.json()["token"]["access_token"]

        id_a = str(uuid.uuid4())[:8]
        id_b = str(uuid.uuid4())[:8]

        headers_a = {"Authorization": f"Bearer {token_a}"}
        headers_b = {"Authorization": f"Bearer {token_b}"}

        # 1. Company A adds a vehicle
        res_veh_a = client.post("/api/v1/vehicles", headers=headers_a, json={
            "license_plate": f"A-TRUCK-{id_a}",
            "make": "Volvo",
            "model": "FH16",
            "year": 2024,
            "type": "TRUCK",
            "fuel_type": "DIESEL",
            "status": "ACTIVE"
        })
        assert res_veh_a.status_code in [200, 201], f"Veh err: {res_veh_a.text}"
        veh_a_id = res_veh_a.json()["id"]

        # 2. Company A adds a driver
        res_drv_a = client.post("/api/v1/drivers", headers=headers_a, json={
            "name": f"Driver A {id_a}",
            "phone_number": f"88{random.randint(10000000, 99999999)}",
            "license_number": f"DL-A-{id_a}",
            "status": "ACTIVE"
        })
        assert res_drv_a.status_code in [200, 201], f"Drv err: {res_drv_a.text}"
        drv_a_id = res_drv_a.json()["id"]

        # 3. Create a trip for Driver A
        res_trip_a = client.post("/api/v1/trips", headers=headers_a, json={
            "driver_id": drv_a_id,
            "vehicle_id": veh_a_id,
            "origin": "City A",
            "destination": "City B",
            "origin_location": "12.0,77.0",
            "destination_location": "13.0,78.0",
            "distance_km": 100,
            "estimated_duration_mins": 120,
            "status": "SCHEDULED"
        })
        assert res_trip_a.status_code in [200, 201], f"Trip err: {res_trip_a.text}"
        trip_a_id = res_trip_a.json()["id"]

        # --- TEST 1: DRIVER -> OWNER ---
        update_trip_a = client.patch(f"/api/v1/trips/{trip_a_id}", headers=headers_a, json={
            "status": "IN_PROGRESS"
        })
        assert update_trip_a.status_code == 200

        # Query Dashboard API (Owner/Dashboard view)
        res_dash_a = client.get("/api/v1/owner/dashboard/kpis", headers=headers_a)
        assert res_dash_a.status_code == 200
        # The active_trips should be 1
        assert res_dash_a.json()["active_trips"] == 1

        # Query Trip list
        res_trips_a = client.get("/api/v1/trips", headers=headers_a)
        assert res_trips_a.status_code == 200
        assert any(t["id"] == trip_a_id and t["status"] == "IN_PROGRESS" for t in res_trips_a.json())

        print("TEST 1 & 2 & 3 (Cross-App Sync) Passed!")

        # --- TEST COMPANY ISOLATION ---
        # Company B tries to read Company A's vehicle
        res_get_veh_b = client.get(f"/api/v1/vehicles/{veh_a_id}", headers=headers_b)
        assert res_get_veh_b.status_code in [404, 403], f"Isolation Failed! Code: {res_get_veh_b.status_code}"

        # Company B tries to read Company A's trip
        res_get_trip_b = client.get(f"/api/v1/trips/{trip_a_id}", headers=headers_b)
        assert res_get_trip_b.status_code in [404, 403]

        # Company B tries to delete Company A's vehicle
        res_del_veh_b = client.delete(f"/api/v1/vehicles/{veh_a_id}", headers=headers_b)
        assert res_del_veh_b.status_code in [404, 403]

        # Company A gets Dashboard KPIs
        res_dash_b = client.get("/api/v1/owner/dashboard/kpis", headers=headers_b)
        assert res_dash_b.status_code == 200
        assert res_dash_b.json()["active_trips"] == 0  # Company B has 0 trips

        print("TEST Company Isolation Passed!")
