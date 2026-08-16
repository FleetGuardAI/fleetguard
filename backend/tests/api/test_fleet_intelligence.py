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
    assert response.status_code == 200, "Failed to login for test setup. Ensure seed data exists."
    return response.json()["access_token"]


def test_get_fleet_health_endpoint(client: TestClient, access_token: str):
    """
    Verify that the fleet intelligence API can be called successfully
    by an authenticated user, returning a valid schema representing
    the fleet's current health status.
    """
    response = client.get(
        "/api/v1/intelligence/fleet-health",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "fleet_health_status" in data
    assert "domain_statistics" in data
    assert "fleet_findings" in data
    assert "fleet_insights" in data
    
    # Check default/fallback behavior (assumes isolated DB or populated DB works either way)
    assert isinstance(data["vehicle_count"], int)
    assert isinstance(data["fleet_summary"], str)


def test_get_fleet_health_unauthorized(client: TestClient):
    """
    Verify that unauthorized access is blocked.
    """
    response = client.get("/api/v1/intelligence/fleet-health")
    assert response.status_code == 401
