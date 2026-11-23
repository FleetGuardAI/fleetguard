import pytest
from httpx import ASGITransport, AsyncClient
from main import app
from models.user import User, UserRole
from services.auth_service import get_current_user

@pytest.fixture
def auth_user():
    return User(
        id=1,
        company_id=1,
        email="admin@fleetguard.com",
        full_name="Fleet Admin",
        role=UserRole.COMPANY_ADMIN,
        is_active=True
    )

@pytest.fixture
async def client(auth_user):
    app.dependency_overrides[get_current_user] = lambda: auth_user
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.pop(get_current_user, None)

@pytest.fixture
def auth_headers():
    return {"Authorization": "Bearer mock-token"}

@pytest.mark.asyncio
async def test_create_trip_with_receiver_info(client: AsyncClient, auth_headers):
    payload = {
        "origin_location": "Origin A",
        "destination_location": "Destination B",
        "receiver_name": "John Doe",
        "receiver_phone": "1234567890",
        "receiver_address": "123 Main St",
        "receiver_city": "Metropolis",
        "receiver_pincode": "12345"
    }
    response = await client.post("/api/v1/trips", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["receiver_name"] == "John Doe"
    assert data["receiver_city"] == "Metropolis"

@pytest.mark.asyncio
async def test_create_trip_missing_receiver_fields(client: AsyncClient, auth_headers):
    # Only providing receiver_name without phone should trigger validation error
    payload = {
        "origin_location": "Origin A",
        "destination_location": "Destination B",
        "receiver_name": "John Doe"
    }
    response = await client.post("/api/v1/trips", json=payload, headers=auth_headers)
    assert response.status_code == 400
    assert "Receiver Phone Number is required" in response.json()["detail"]

@pytest.mark.asyncio
async def test_create_trip_without_receiver_info(client: AsyncClient, auth_headers):
    # Backward compatibility: no receiver fields should succeed
    payload = {
        "origin_location": "Origin A",
        "destination_location": "Destination B"
    }
    response = await client.post("/api/v1/trips", json=payload, headers=auth_headers)
    assert response.status_code == 201
