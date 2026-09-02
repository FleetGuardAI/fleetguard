import uuid
import random
import pytest
from fastapi.testclient import TestClient
from main import app

def register_company(client, name_suffix):
    id_suffix = str(uuid.uuid4())[:8]
    mob = f"99{random.randint(10000000, 99999999)}"
    res = client.post("/api/v1/auth/register", json={
        "company_name": f"Company {name_suffix} {id_suffix}",
        "owner_name": f"Owner {name_suffix} {id_suffix}",
        "mobile_number": mob,
        "email": f"owner_{name_suffix}_{id_suffix}@test.com",
        "password": "password123",
        "confirm_password": "password123"
    })
    assert res.status_code in [200, 201], f"Register failed: {res.text}"
    token = res.json()["token"]["access_token"]
    return token

def test_storage_security_isolation(client: TestClient):
    # Register two companies
    token_a = register_company(client, "A")
    token_b = register_company(client, "B")

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 1. Company A creates an operational event
    from datetime import datetime, timezone
    res_event_create = client.post(
        "/api/v1/events",
        headers=headers_a,
        json={
            "event_type": "TRIP_STARTED",
            "entity_type": "TRIP",
            "entity_id": "1",
            "capture_method": "API_INTEGRATION",
            "occurred_at": datetime.now(timezone.utc).isoformat(),
            "payload": {"distance": 0, "storage_path": "mocked/storage/path.jpg"}
        }
    )
    assert res_event_create.status_code == 201, f"Failed to create event: {res_event_create.text}"
    event_a_id = res_event_create.json()["id"]

    # 2. Upload Evidence for the event
    file_content = b"fake image content"
    files = {"file": ("test.jpg", file_content, "image/jpeg")}
    
    # We create evidence manually and assume the file was uploaded by document ingestion.
    res_ev_create = client.post(
        f"/api/v1/events/{event_a_id}/evidence",
        headers=headers_a,
        json={
            "evidence_type": "RECEIPT_DOCUMENT",
            "source": "test",
            "summary": "test evidence",
            "details": "mocked/storage/path.jpg"
        }
    )
    assert res_ev_create.status_code == 201, f"Failed to create evidence: {res_ev_create.text}"
    evidence_a_id = res_ev_create.json()["id"]

    # 3. Company A accesses its own evidence URL
    res_url_a = client.get(f"/api/v1/events/{event_a_id}/evidence/{evidence_a_id}/url", headers=headers_a)
    assert res_url_a.status_code == 200, f"Failed to get URL: {res_url_a.text}"
    assert "signed_url" in res_url_a.json()
    assert "mock-supabase.com" in res_url_a.json()["signed_url"]

    # 4. Company B tries to access Company A's evidence URL (Cross-Company IDOR check)
    res_url_b = client.get(f"/api/v1/events/{event_a_id}/evidence/{evidence_a_id}/url", headers=headers_b)
    assert res_url_b.status_code in [403, 404], f"IDOR Vulnerability! Code: {res_url_b.status_code}"

    # 5. Unauthenticated access denied
    res_url_unauth = client.get(f"/api/v1/events/{event_a_id}/evidence/{evidence_a_id}/url")
    assert res_url_unauth.status_code == 401

    # 6. Upload validation: File size limit (Simulate a large file upload manually using service or endpoint)
    # We can test invalid MIME type first
    files_invalid = {"file": ("test.txt", b"text content", "text/plain")}
    res_invalid_type = client.post("/api/v1/documents", headers=headers_a, files=files_invalid)
    assert res_invalid_type.status_code == 400
    assert "Unsupported file type" in res_invalid_type.text
    
    print("Storage Security Tests Passed!")

