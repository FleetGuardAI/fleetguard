"""
FleetGuard — Tyre Domain REST API Tests
Tests REST endpoints under /api/v1/tyres:
- Tyre registration into stock
- Listing tyres (verifying tyres in storage are visible to tenant)
- Inventory summary aggregation
- Tyre installation onto vehicle
- Wheel position collision rejection (409 Conflict)
- Tyre removal and odometer tracking
- Tyre rotation
- Tyre retreading
- Tyre repair
- Tyre retirement
- Multi-tenant isolation enforcement
"""

import pytest
from datetime import datetime, timezone
from models.user import User, UserRole
from models.company import Company
from models.vehicle_domain import Vehicle, VehicleStatus
from models.tyre_domain import Tyre, TyreStatus
from services.auth_service import get_current_user
from main import app


@pytest.fixture
async def setup_api_data(db_session):
    c1 = Company(id=301, company_name="Speedway Express", owner_name="Owner Speedway", mobile_number="9111111111")
    c2 = Company(id=302, company_name="Metro Haulage", owner_name="Owner Metro", mobile_number="9222222222")
    db_session.add_all([c1, c2])
    await db_session.flush()

    u1 = User(
        id=401, email="admin@speedway.com", company_id=301,
        full_name="Admin Speedway", mobile_number="9111111112",
        password_hash="mock_hash", role=UserRole.COMPANY_ADMIN, is_active=True
    )
    u2 = User(
        id=402, email="admin@metro.com", company_id=302,
        full_name="Admin Metro", mobile_number="9222222223",
        password_hash="mock_hash", role=UserRole.COMPANY_ADMIN, is_active=True
    )
    db_session.add_all([u1, u2])
    await db_session.flush()




    v1 = Vehicle(
        id=501, company_id=301, registration_number="DL-01-AA-1111",
        status=VehicleStatus.ACTIVE, current_odometer=30000.0
    )
    v2 = Vehicle(
        id=502, company_id=302, registration_number="DL-02-BB-2222",
        status=VehicleStatus.ACTIVE, current_odometer=15000.0
    )
    db_session.add_all([v1, v2])
    await db_session.flush()

    return {"c1": c1, "c2": c2, "u1": u1, "u2": u2, "v1": v1, "v2": v2}


def test_tyre_api_full_lifecycle(client, setup_api_data):
    u1 = setup_api_data["u1"]
    app.dependency_overrides[get_current_user] = lambda: u1

    try:
        # 1. Register tyre into stock
        reg_payload = {
            "serial_number": "SN-API-101",
            "manufacturer": "Michelin",
            "brand": "X Multi Z",
            "size": "295/80R22.5",
            "initial_tread_mm": 15.0,
            "purchase_cost": 21000.0,
            "record_purchase_expense": True
        }
        res = client.post("/api/v1/tyres", json=reg_payload)
        assert res.status_code == 201
        data = res.json()
        assert data["serial_number"] == "SN-API-101"
        assert data["current_status"] == "IN_STORAGE"
        assert data["company_id"] == 301
        assert data["current_tread_depth_mm"] == 15.0

        # 2. List tyres - tyre in storage MUST BE VISIBLE!
        res = client.get("/api/v1/tyres")
        assert res.status_code == 200
        tyres = res.json()
        assert len(tyres) == 1
        assert tyres[0]["serial_number"] == "SN-API-101"
        assert tyres[0]["current_status"] == "IN_STORAGE"

        # 3. Inventory summary check
        res = client.get("/api/v1/tyres/inventory/summary")
        assert res.status_code == 200
        summary = res.json()
        assert summary["total_tyres"] == 1
        assert summary["in_storage"] == 1
        assert summary["installed"] == 0

        # 4. Install tyre onto vehicle #501 at FRONT_LEFT
        install_payload = {
            "vehicle_id": 501,
            "position": "FRONT_LEFT",
            "odometer_km": 30000.0
        }
        res = client.post("/api/v1/tyres/SN-API-101/install", json=install_payload)
        assert res.status_code == 200
        data = res.json()
        assert data["current_status"] == "INSTALLED"
        assert data["current_vehicle_id"] == 501
        assert data["current_position"] == "FRONT_LEFT"
        assert data["current_installation_odometer"] == 30000.0

        # 5. Inventory summary: in_storage=0, installed=1
        res = client.get("/api/v1/tyres/inventory/summary")
        summary = res.json()
        assert summary["in_storage"] == 0
        assert summary["installed"] == 1

        # 6. Register a second tyre and attempt collision at FRONT_LEFT -> Expect 409
        client.post("/api/v1/tyres", json={"serial_number": "SN-API-102", "size": "295/80R22.5"})
        res = client.post("/api/v1/tyres/SN-API-102/install", json=install_payload)
        assert res.status_code == 409
        assert "already occupied" in res.json()["detail"]

        # 7. Rotate tyre to FRONT_RIGHT (vacant)
        res = client.post("/api/v1/tyres/SN-API-101/rotate", json={"new_position": "FRONT_RIGHT"})
        assert res.status_code == 200
        assert res.json()["current_position"] == "FRONT_RIGHT"

        # 8. Attempt rollback removal -> Expect 400
        res = client.post("/api/v1/tyres/SN-API-101/remove", json={"odometer_km": 28000.0})
        assert res.status_code == 400
        assert "rollback rejected" in res.json()["detail"]

        # 9. Valid removal at 35000 km (run 5000 km) and send for retread
        res = client.post("/api/v1/tyres/SN-API-101/remove", json={"odometer_km": 35000.0, "target_status": "RETREADING"})
        assert res.status_code == 200
        data = res.json()
        assert data["current_status"] == "RETREADING"
        assert data["total_lifetime_km"] == 5000.0
        assert data["current_retread_km"] == 5000.0
        assert data["current_vehicle_id"] is None

        # 10. Complete retreading
        retread_payload = {
            "action": "COMPLETED",
            "vendor": "Bandag Retreading",
            "cost": 4200.0,
            "tread_depth_mm": 13.5
        }
        res = client.post("/api/v1/tyres/SN-API-101/retread", json=retread_payload)
        assert res.status_code == 200
        data = res.json()
        assert data["current_status"] == "IN_STORAGE"
        assert data["retread_count"] == 1
        assert data["current_retread_km"] == 0.0
        assert data["total_lifetime_km"] == 5000.0
        assert data["current_tread_depth_mm"] == 13.5

        # 11. Record a repair
        repair_payload = {
            "repair_type": "PUNCTURE",
            "cost": 350.0,
            "workshop": "Express Tyre Care"
        }
        res = client.post("/api/v1/tyres/SN-API-101/repair", json=repair_payload)
        assert res.status_code == 200

        # 12. Scrap/Retire tyre
        res = client.post("/api/v1/tyres/SN-API-101/retire", json={"reason": "Sidewall impact cut"})
        assert res.status_code == 200
        assert res.json()["current_status"] == "RETIRED"

    finally:
        app.dependency_overrides.pop(get_current_user, None)


def test_tyre_api_multi_tenancy(client, setup_api_data):
    """
    Company 302 user cannot see or modify Company 301 tyres.
    """
    u1 = setup_api_data["u1"]
    u2 = setup_api_data["u2"]

    # Register tyre under Company 301
    app.dependency_overrides[get_current_user] = lambda: u1
    client.post("/api/v1/tyres", json={"serial_number": "SN-SEC-999"})

    # Switch to Company 302 user
    app.dependency_overrides[get_current_user] = lambda: u2

    try:
        # Listing tyres for Company 302 must return 0 tyres
        res = client.get("/api/v1/tyres")
        assert res.status_code == 200
        assert len(res.json()) == 0

        # Attempting to fetch Company 301 tyre by serial/install must return 404
        res = client.post("/api/v1/tyres/SN-SEC-999/install", json={"vehicle_id": 502, "position": "FRONT_LEFT"})
        assert res.status_code == 404
    finally:
        app.dependency_overrides.pop(get_current_user, None)
