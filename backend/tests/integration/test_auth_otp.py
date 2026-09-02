import os
os.environ["OTP_MOCK_MODE"] = "True"

import pytest
from fastapi.testclient import TestClient
from main import app
from config import settings

settings.OTP_MOCK_MODE = True

def test_otp_request_and_verify_success(client: TestClient):
    """Test successful OTP request and verification for an existing user."""
    # First, register the admin user so they exist in the DB
    res = client.post("/api/v1/auth/register", json={
        "company_name": "Test Co",
        "owner_name": "Admin",
        "mobile_number": "9988776655",
        "email": "admin@fleetguard.com",
        "password": "password123",
        "confirm_password": "password123"
    })
    assert res.status_code in [200, 201]

    # Now request OTP
    response = client.post(
        "/api/v1/auth/request-otp",
        json={"identifier": "admin@fleetguard.com"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "verification code has been sent" in data["message"]
    req_id = data.get("req_id")
    assert req_id is not None

    # In mock mode, the code is always 123456
    verify_response = client.post(
        "/api/v1/auth/verify-otp",
        json={"identifier": "admin@fleetguard.com", "req_id": req_id, "code": "123456"},
    )
    assert verify_response.status_code == 200
    verify_data = verify_response.json()
    assert "access_token" in verify_data
    assert verify_data["token_type"] == "bearer"


def test_otp_verify_invalid_code(client: TestClient):
    """Test OTP verification with invalid code."""
    res = client.post("/api/v1/auth/register", json={
        "company_name": "Test Co 2",
        "owner_name": "Admin 2",
        "mobile_number": "9988776656",
        "email": "admin@fleetguard.com",
        "password": "password123",
        "confirm_password": "password123"
    })
    
    verify_response = client.post(
        "/api/v1/auth/verify-otp",
        json={"identifier": "admin@fleetguard.com", "req_id": "mock_req_123", "code": "999999"},
    )
    assert verify_response.status_code == 401
    assert verify_response.json()["detail"] == "Invalid or expired OTP."


def test_otp_request_nonexistent_user(client: TestClient):
    """Test OTP request for a nonexistent user prevents enumeration."""
    # Should still return 200 success message to avoid user enumeration
    response = client.post(
        "/api/v1/auth/request-otp",
        json={"identifier": "nonexistent@fleetguard.com"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "verification code has been sent" in data["message"]
    # For non-existent users, req_id should be null
    assert data.get("req_id") is None

    # Verification should fail
    verify_response = client.post(
        "/api/v1/auth/verify-otp",
        json={"identifier": "nonexistent@fleetguard.com", "req_id": "null_req", "code": "123456"},
    )
    assert verify_response.status_code == 401
    assert verify_response.json()["detail"] == "Invalid credentials."
