import pytest
from fastapi.testclient import TestClient
from main import app

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

import uuid

@pytest.fixture(scope="module")
def admin_token(client):
    # Self-register a test user rather than depending on seed data
    uid = str(uuid.uuid4())[:8]
    reg = client.post("/api/v1/auth/register", json={
        "company_name": f"TestCo QR {uid}",
        "owner_name": f"Owner QR {uid}",
        "mobile_number": f"66{uid}00",
        "email": f"qr_{uid}@test.com",
        "password": "password123",
        "confirm_password": "password123"
    })
    if reg.status_code in [200, 201]:
        return reg.json()["token"]["access_token"]
    pytest.skip(f"Could not register test user: {reg.text}")

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
