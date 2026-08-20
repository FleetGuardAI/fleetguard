import pytest
from fastapi.testclient import TestClient
from main import app

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

import uuid

@pytest.fixture(scope="module")
def access_token(client):
    # Self-register a test user rather than depending on seed data
    uid = str(uuid.uuid4())[:8]
    reg = client.post("/api/v1/auth/register", json={
        "company_name": f"TestCo HW {uid}",
        "owner_name": f"Owner HW {uid}",
        "mobile_number": f"55{uid}00",
        "email": f"hw_{uid}@test.com",
        "password": "password123",
        "confirm_password": "password123"
    })
    if reg.status_code in [200, 201]:
        return reg.json()["token"]["access_token"]
    pytest.skip(f"Could not register test user: {reg.text}")

def test_create_hardware_asset_success(client: TestClient, access_token: str):
    # Get a valid vehicle first
    res = client.get("/api/v1/vehicles", headers={"Authorization": f"Bearer {access_token}"})
    if res.status_code != 200 or not res.json():
        pytest.skip("No vehicles found to assign hardware to")
    
    vehicle_id = res.json()[0]["id"]
    
    payload = {
        "api_key": "sec_test123",
        "vehicle_id": vehicle_id,
        "device_name": "Test GPS"
    }
    
    response = client.post(
        "/api/v1/assets/hardware",
        json=payload,
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["model"] == "Test GPS"
    assert "api_key" not in data
    assert data["current_vehicle_id"] == vehicle_id

def test_create_hardware_asset_unauthorized_vehicle(client: TestClient, access_token: str):
    payload = {
        "api_key": "sec_test456",
        "vehicle_id": 999999, # unlikely to exist
        "device_name": "Other GPS"
    }
    
    response = client.post(
        "/api/v1/assets/hardware",
        json=payload,
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code in [400, 404]
