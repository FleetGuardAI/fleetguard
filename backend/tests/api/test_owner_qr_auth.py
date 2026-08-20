import pytest
from fastapi.testclient import TestClient
from main import app

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture(scope="module")
def admin_token(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "password", "remember_me": True}
    )
    assert response.status_code == 200, "Failed to login for test setup. Ensure seed data exists."
    return response.json()["access_token"]

def test_owner_qr_flow(client: TestClient, admin_token: str):
    # 1. Generate QR Token
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = client.post("/api/v1/auth/owner-qr/generate", headers=headers)
    
    assert response.status_code == 200, response.text
    data = response.json()
    pairing_token = data["pairing_token"]
    assert pairing_token is not None
    assert "expires_in_seconds" in data
    
    # 2. Verify QR Token
    verify_response = client.post("/api/v1/auth/owner-qr/verify", json={"pairing_token": pairing_token})
    assert verify_response.status_code == 200, verify_response.text
    verify_data = verify_response.json()
    assert "access_token" in verify_data
    
    # 3. Try to reuse QR Token (should fail because single-use)
    reuse_response = client.post("/api/v1/auth/owner-qr/verify", json={"pairing_token": pairing_token})
    assert reuse_response.status_code == 400
    assert "Invalid or expired" in reuse_response.text
