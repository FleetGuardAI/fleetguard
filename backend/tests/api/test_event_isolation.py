import uuid
import random
import pytest
from fastapi.testclient import TestClient
from main import app

def test_user_cannot_read_other_company_event_and_evidence():
    with TestClient(app) as client:
        # Setup: Register two companies
        id_a = str(uuid.uuid4())[:8]
        id_b = str(uuid.uuid4())[:8]
        
        comp_a = client.post("/api/v1/auth/register", json={
            "company_name": f"Company A {id_a}",
            "owner_name": f"Owner A {id_a}",
            "mobile_number": f"99{random.randint(10000000, 99999999)}",
            "email": f"ownera_{id_a}@iso.com",
            "password": "password123",
            "confirm_password": "password123"
        })
        
        comp_b = client.post("/api/v1/auth/register", json={
            "company_name": f"Company B {id_b}",
            "owner_name": f"Owner B {id_b}",
            "mobile_number": f"99{random.randint(10000000, 99999999)}",
            "email": f"ownerb_{id_b}@iso.com",
            "password": "password123",
            "confirm_password": "password123"
        })
        
        assert comp_a.status_code in [200, 201]
        assert comp_b.status_code in [200, 201]
        
        token_a = comp_a.json()["token"]["access_token"]
        token_b = comp_b.json()["token"]["access_token"]
        
        headers_a = {"Authorization": f"Bearer {token_a}"}
        headers_b = {"Authorization": f"Bearer {token_b}"}
        
        # TEST 1: Read Event
        event_payload = {
            "event_type": "FUEL_FILLED",
            "entity_type": "VEHICLE",
            "entity_id": f"MH{random.randint(10,99)}AB{random.randint(1000,9999)}",
            "occurred_at": "2026-08-30T10:00:00Z",
            "capture_method": "MANUAL_ENTRY",
            "payload": {"liters": 45}
        }
        
        res_evt_a = client.post("/api/v1/events", headers=headers_a, json=event_payload)
        assert res_evt_a.status_code in [200, 201], f"Failed to create event: {res_evt_a.text}"
        event_a_id = res_evt_a.json()["id"]
        
        # Company B tries to read Company A's event
        res_get_evt_b = client.get(f"/api/v1/events/{event_a_id}", headers=headers_b)
        assert res_get_evt_b.status_code == 404, "Isolation failed: Company B could read Company A's event"

        # TEST 2: Evidence URL
        event_payload_2 = {
            "event_type": "FUEL_FILLED",
            "entity_type": "VEHICLE",
            "entity_id": f"MH{random.randint(10,99)}AB{random.randint(1000,9999)}",
            "occurred_at": "2026-08-30T10:00:00Z",
            "capture_method": "MANUAL_ENTRY",
            "payload": {"storage_path": "uploads/company_a/receipt.jpg"}
        }
        
        res_evt_a_2 = client.post("/api/v1/events", headers=headers_a, json=event_payload_2)
        event_a_id_2 = res_evt_a_2.json()["id"]
        
        evidence_payload = {
            "evidence_type": "RECEIPT_DOCUMENT",
            "source": "WHATSAPP",
            "status": "COMPLETED",
            "summary": "Receipt for fuel",
            "raw_data": {"path": "uploads/company_a/receipt.jpg"}
        }
        
        res_evd_a = client.post(f"/api/v1/events/{event_a_id_2}/evidence", headers=headers_a, json=evidence_payload)
        assert res_evd_a.status_code in [200, 201], f"Failed to create evidence: {res_evd_a.text}"
        evidence_a_id = res_evd_a.json()["id"]
        
        res_url_b = client.get(f"/api/v1/events/{event_a_id_2}/evidence/{evidence_a_id}/url", headers=headers_b)
        assert res_url_b.status_code == 404, "Isolation failed: Company B could get signed URL for Company A's evidence"
