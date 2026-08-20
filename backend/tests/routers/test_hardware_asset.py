import pytest
from fastapi.testclient import TestClient
from main import app

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture(scope="module")
def access_token(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "password", "remember_me": True}
    )
    if response.status_code != 200:
        pytest.skip("Login failed, skipping test")
    return response.json()["access_token"]

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
