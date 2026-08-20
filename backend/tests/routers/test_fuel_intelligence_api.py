import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from main import app
from infrastructure.intelligence.fuel_domain.financial.summary_schemas import FleetFinancialIntelligenceSummary
from infrastructure.intelligence.fuel_domain.financial.truck_schemas import TruckIntelligenceDetailResponse

from models.user import User

def override_get_current_user():
    user = User(
        id=1,
        company_id=1,
        email="owner@fleetguard.com",
        full_name="Fleet Owner",
        role="OWNER"
    )
    return user

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

def test_fleet_summary_valid(client: TestClient, auth_headers):
    now = datetime.now(timezone.utc)
    start = (now - timedelta(days=30)).isoformat()
    end = now.isoformat()
    
    mock_summary = FleetFinancialIntelligenceSummary(
        period_start=now - timedelta(days=30),
        period_end=now,
        fleet_id="1",
        total_trucks=10,
        trucks_with_sufficient_intelligence=8,
        trucks_with_insufficient_data=2,
        affected_trucks=2,
        trucks_without_anomaly=6,
        total_estimated_exposure=5000.0,
        total_excess_fuel_liters=55.0,
        average_exposure_per_affected_truck=2500.0,
        top_exposures=[],
        contributing_factor_summary=[]
    )
    
    with patch("infrastructure.intelligence.fuel_domain.financial.summary_service.FleetFinancialIntelligenceService.get_fleet_summary", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_summary
        
        response = client.get("/api/v1/intelligence/fuel/summary", params={"period_start": start, "period_end": end, "top_n": 5}, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total_trucks"] == 10
        assert data["total_estimated_exposure"] == 5000.0
        
        mock_get.assert_called_once()

def test_fleet_summary_invalid_period(client: TestClient, auth_headers):
    now = datetime.now(timezone.utc)
    start = now.isoformat()
    end = (now - timedelta(days=1)).isoformat()
    
    response = client.get("/api/v1/intelligence/fuel/summary", params={"period_start": start, "period_end": end}, headers=auth_headers)
    assert response.status_code == 400

def test_truck_detail_valid(client: TestClient, auth_headers):
    now = datetime.now(timezone.utc)
    start = (now - timedelta(days=30)).isoformat()
    end = now.isoformat()
    truck_id = "TEST-1"
    
    from infrastructure.intelligence.fuel_domain.financial.summary_schemas import TruckFinancialIntelligence
    from models.fuel_anomaly import AnomalySeverity
    from models.fuel_root_cause import RootCauseType, EvidenceStrength
    
    mock_detail = TruckIntelligenceDetailResponse(
        summary=TruckFinancialIntelligence(
            truck_id=truck_id,
            estimated_exposure=900.0,
            excess_fuel_liters=10.0,
            anomaly_count=1,
            worst_deviation_percent=-10.0,
            severity=AnomalySeverity.WARNING,
            top_contributing_factor=RootCauseType.UNKNOWN,
            top_contributing_strength=EvidenceStrength.NO_EVIDENCE,
            period_start=now - timedelta(days=30),
            period_end=now
        ),
        anomalies=[],
        financial_impacts=[],
        contributing_factors=[]
    )
    
    with patch("infrastructure.intelligence.fuel_domain.financial.truck_service.TruckFinancialIntelligenceService.get_truck_detail", new_callable=AsyncMock) as mock_truck_get, \
         patch("infrastructure.intelligence.fuel_domain.financial.summary_service.FleetFinancialIntelligenceService.get_fleet_summary", new_callable=AsyncMock) as mock_fleet_get:
        
        mock_truck_get.return_value = mock_detail
        
        response = client.get(f"/api/v1/intelligence/fuel/trucks/{truck_id}", params={"period_start": start, "period_end": end}, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert data["summary"]["truck_id"] == truck_id
        assert data["summary"]["estimated_exposure"] == 900.0
        
        mock_truck_get.assert_called_once()
        mock_fleet_get.assert_not_called()

def test_truck_detail_foreign_truck(client: TestClient, auth_headers):
    now = datetime.now(timezone.utc)
    start = (now - timedelta(days=30)).isoformat()
    end = now.isoformat()
    truck_id = "FOREIGN-1"
    
    with patch("infrastructure.intelligence.fuel_domain.financial.truck_service.TruckFinancialIntelligenceService.get_truck_detail", new_callable=AsyncMock) as mock_truck_get:
        mock_truck_get.return_value = None
        
        response = client.get(f"/api/v1/intelligence/fuel/trucks/{truck_id}", params={"period_start": start, "period_end": end}, headers=auth_headers)
        assert response.status_code == 404
