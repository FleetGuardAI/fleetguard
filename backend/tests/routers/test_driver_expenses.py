import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from main import app
from models.user import User

def override_get_current_user():
    return User(
        id=1,
        company_id=1,
        email="owner@fleetguard.com",
        full_name="Fleet Owner",
        role="OWNER"
    )

async def override_get_read_uow():
    class DummyUOW:
        pass
    yield DummyUOW()

@pytest.fixture(scope="module")
def client():
    from services.auth_service import get_current_user
    from database import get_read_uow
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_read_uow] = override_get_read_uow
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture
def auth_headers(client):
    return {"Authorization": "Bearer mock-token"}

class MockDriver:
    def __init__(self, company_id):
        self.company_id = company_id

class MockVehicle:
    def __init__(self, company_id):
        self.company_id = company_id

class MockTrip:
    def __init__(self, company_id):
        self.company_id = company_id

@pytest.fixture
def mock_db_get():
    with patch("sqlalchemy.ext.asyncio.AsyncSession.get", new_callable=AsyncMock) as mock_get:
        yield mock_get

@pytest.fixture
def mock_db_add():
    with patch("sqlalchemy.ext.asyncio.AsyncSession.add") as mock_add:
        yield mock_add

@pytest.fixture
def mock_db_commit():
    with patch("sqlalchemy.ext.asyncio.AsyncSession.commit", new_callable=AsyncMock) as mock_commit:
        yield mock_commit
        
@pytest.fixture
def mock_db_refresh():
    async def mock_refresh(obj):
        obj.id = 1
        obj.created_at = datetime.now(timezone.utc)
    
    with patch("sqlalchemy.ext.asyncio.AsyncSession.refresh", new_callable=AsyncMock, side_effect=mock_refresh) as m_refresh:
        yield m_refresh

def test_create_expense_same_company(client: TestClient, auth_headers, mock_db_get, mock_db_add, mock_db_commit, mock_db_refresh):
    # Driver, Vehicle, and Trip belong to company 1
    mock_db_get.side_effect = lambda model, id: MockDriver(1) if model.__name__ == 'Driver' else (MockVehicle(1) if model.__name__ == 'Vehicle' else MockTrip(1))
    
    payload = {
        "category": "FUEL",
        "amount": 2500.0,
        "driver_id": 101,
        "vehicle_id": 201,
        "trip_id": 301,
        "fuel_quantity_liters": 25.0
    }
    
    with patch("services.operational_event_service.OperationalEventService.create_event", new_callable=AsyncMock):
        response = client.post("/api/v1/driver-app/expenses", json=payload, headers=auth_headers)
        
    assert response.status_code == 201
    data = response.json()
    assert data["amount"] == 2500.0

def test_create_expense_cross_company_driver(client: TestClient, auth_headers, mock_db_get):
    # Driver belongs to company 2
    mock_db_get.return_value = MockDriver(2)
    
    payload = {
        "category": "FOOD",
        "amount": 500.0,
        "driver_id": 102
    }
    
    response = client.post("/api/v1/driver-app/expenses", json=payload, headers=auth_headers)
    assert response.status_code == 403
    assert "Unauthorized driver" in response.text

def test_create_expense_cross_company_vehicle(client: TestClient, auth_headers, mock_db_get):
    # Driver belongs to company 1, Vehicle belongs to company 2
    mock_db_get.side_effect = lambda model, id: MockDriver(1) if model.__name__ == 'Driver' else MockVehicle(2)
    
    payload = {
        "category": "REPAIR",
        "amount": 5000.0,
        "driver_id": 101,
        "vehicle_id": 202
    }
    
    response = client.post("/api/v1/driver-app/expenses", json=payload, headers=auth_headers)
    assert response.status_code == 403
    assert "Unauthorized vehicle" in response.text

def test_create_expense_cross_company_trip(client: TestClient, auth_headers, mock_db_get):
    # Driver belongs to company 1, Trip belongs to company 2
    mock_db_get.side_effect = lambda model, id: MockDriver(1) if model.__name__ == 'Driver' else MockTrip(2)
    
    payload = {
        "category": "TOLL",
        "amount": 150.0,
        "driver_id": 101,
        "trip_id": 302
    }
    
    response = client.post("/api/v1/driver-app/expenses", json=payload, headers=auth_headers)
    assert response.status_code == 403
    assert "Unauthorized trip" in response.text

def test_list_expenses_cross_company_driver(client: TestClient, auth_headers, mock_db_get):
    # Driver belongs to company 2
    mock_db_get.return_value = MockDriver(2)
    
    response = client.get("/api/v1/driver-app/expenses?driver_id=102", headers=auth_headers)
    assert response.status_code == 403
    assert "Unauthorized driver" in response.text

def test_list_expenses_same_company_driver(client: TestClient, auth_headers, mock_db_get):
    # Driver belongs to company 1
    mock_db_get.return_value = MockDriver(1)
    
    with patch("sqlalchemy.ext.asyncio.AsyncSession.execute", new_callable=AsyncMock) as mock_execute:
        class MockResult:
            def scalars(self):
                class MockScalars:
                    def all(self):
                        return []
                return MockScalars()
        mock_execute.return_value = MockResult()
        
        response = client.get("/api/v1/driver-app/expenses?driver_id=101", headers=auth_headers)
        assert response.status_code == 200
