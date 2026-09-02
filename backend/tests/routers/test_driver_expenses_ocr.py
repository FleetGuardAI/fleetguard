import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import io
import json

from main import app
from models.user import User
from config import settings

def override_get_current_user():
    return User(
        id=1,
        company_id=1,
        email="owner@fleetguard.com",
        full_name="Fleet Owner",
        role="OWNER"
    )

@pytest.fixture(scope="module")
def client():
    from services.auth_service import get_current_user
    app.dependency_overrides[get_current_user] = override_get_current_user
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture
def auth_headers(client):
    return {"Authorization": "Bearer mock-token"}

def test_ocr_mock_provider(client: TestClient, auth_headers):
    # Ensure OCR_PROVIDER is set to mock
    settings.OCR_PROVIDER = "mock"
    
    # Create a dummy image file
    file_content = b"fake image content"
    files = {"file": ("receipt.jpg", io.BytesIO(file_content), "image/jpeg")}
    
    with patch("services.file_upload_service.StorageService.upload_file", new_callable=AsyncMock) as mock_upload:
        mock_upload.return_value = "http://fake-url/receipt.jpg"
        
        response = client.post("/api/v1/driver-app/expenses/ocr", files=files, headers=auth_headers)
        
    assert response.status_code == 200
    data = response.json()
    assert data["vendor"] == "HP Fuel Station #482"
    assert data["amount"] == 2500.0

def test_ocr_openai_missing_key(client: TestClient, auth_headers):
    # Set provider to openai but clear keys
    settings.OCR_PROVIDER = "openai"
    original_openai = settings.OPENAI_API_KEY
    original_gemini = settings.GEMINI_API_KEY
    settings.OPENAI_API_KEY = None
    settings.GEMINI_API_KEY = None
    
    file_content = b"fake image content"
    files = {"file": ("receipt.jpg", io.BytesIO(file_content), "image/jpeg")}
    
    with patch("services.file_upload_service.StorageService.upload_file", new_callable=AsyncMock) as mock_upload:
        mock_upload.return_value = "http://fake-url/receipt.jpg"
        
        response = client.post("/api/v1/driver-app/expenses/ocr", files=files, headers=auth_headers)
        
    assert response.status_code == 503
    assert "OpenAI API key not configured" in response.text
    
    # Restore
    settings.OPENAI_API_KEY = original_openai
    settings.GEMINI_API_KEY = original_gemini

def test_ocr_openai_success(client: TestClient, auth_headers):
    settings.OCR_PROVIDER = "openai"
    
    # Temporarily set key so it doesn't fail the key check
    original_openai = settings.OPENAI_API_KEY
    settings.OPENAI_API_KEY = "test-key"
    
    file_content = b"fake image content"
    files = {"file": ("receipt.jpg", io.BytesIO(file_content), "image/jpeg")}
    
    mock_ocr_result = type('OCRResult', (), {'text': json.dumps({
        "vendor": "Test Vendor",
        "amount": 100.0,
        "date": "2023-10-01",
        "category": "FOOD"
    })})
    
    with patch("services.file_upload_service.StorageService.upload_file", new_callable=AsyncMock) as mock_upload, \
         patch("infrastructure.ocr.openai_provider.OpenAIOCRProvider.extract_text", new_callable=AsyncMock) as mock_extract:
         
        mock_upload.return_value = "http://fake-url/receipt.jpg"
        mock_extract.return_value = mock_ocr_result
        
        response = client.post("/api/v1/driver-app/expenses/ocr", files=files, headers=auth_headers)
        
    assert response.status_code == 200
    data = response.json()
    assert data["vendor"] == "Test Vendor"
    assert data["amount"] == 100.0
    assert data["category"] == "FOOD"
    
    # Restore
    settings.OPENAI_API_KEY = original_openai
