import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_get_fleet_health_endpoint(async_client: AsyncClient, access_token: str):
    """
    Verify that the fleet intelligence API can be called successfully
    by an authenticated user, returning a valid schema representing
    the fleet's current health status.
    """
    response = await async_client.get(
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

@pytest.mark.asyncio
async def test_get_fleet_health_unauthorized(async_client: AsyncClient):
    """
    Verify that unauthorized access is blocked.
    """
    response = await async_client.get("/api/v1/intelligence/fleet-health")
    assert response.status_code == 401
