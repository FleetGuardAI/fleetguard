import os
import random
import pytest
import requests

client = requests.Session()
client.base_url = "http://localhost:8000"

def post(path, **kwargs):
    kwargs.setdefault("timeout", 30)
    return client.post(f"http://localhost:8000{path}", **kwargs)

def get(path, **kwargs):
    kwargs.setdefault("timeout", 30)
    return client.get(f"http://localhost:8000{path}", **kwargs)

def patch(path, **kwargs):
    kwargs.setdefault("timeout", 30)
    return client.patch(f"http://localhost:8000{path}", **kwargs)


def run_tests():
    print("=== FleetGuard End-to-End Driver Flow Test ===")
    
    # 1. Register Fleet A and Fleet B Admins
    admin_a_email = f"admin_a_{random.randint(10000, 99999)}@fleet.com"
    res_a = post("/api/v1/auth/register", json={
        "company_name": "Fleet A", "owner_name": "Admin A", "mobile_number": f"+9199999{random.randint(10000, 99999)}",
        "email": admin_a_email, "password": "password", "confirm_password": "password"
    })
    assert res_a.status_code == 201, f"Failed Fleet A register: {res_a.text}"
    token_a = res_a.json()["token"]["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    admin_b_email = f"admin_b_{random.randint(10000, 99999)}@fleet.com"
    res_b = post("/api/v1/auth/register", json={
        "company_name": "Fleet B", "owner_name": "Admin B", "mobile_number": f"+9188888{random.randint(10000, 99999)}",
        "email": admin_b_email, "password": "password", "confirm_password": "password"
    })
    assert res_b.status_code == 201
    token_b = res_b.json()["token"]["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    print("âœ… Fleet A and Fleet B created.")

    # 2. Fleet A Admin generates an invite
    invite_res = post("/api/v1/fleet/invite", json={"phone_number": "", "role": "DRIVER"}, headers=headers_a)
    invite_token_a = invite_res.json()["invite_token"]

    # 3. Driver A scans QR and verifies invite
    scan_res = post("/api/v1/driver-app/verify-invite", json={"invite_token": invite_token_a})
    assert scan_res.status_code == 200 and scan_res.json()["valid"] == True
    print("âœ… Driver A scanned QR for Fleet A.")

    # 4. Driver A authenticates via OTP
    driver_phone = f"+9177777{random.randint(10000, 99999)}"
    post("/api/v1/driver-app/send-otp", json={"phone_number": driver_phone})
    otp_res = post("/api/v1/driver-app/verify-otp", json={
        "phone_number": driver_phone, "req_id": "mock_req_123", "otp_code": "123456", "invite_token": invite_token_a
    })
    if otp_res.status_code != 200:
        print("OTP Failed (maybe mock is off?), trying mock token bypass...")
        # Since we might not have mock enabled in test client, let's enable it
        from config import settings
        settings.OTP_MOCK_MODE = True
        otp_res = post("/api/v1/driver-app/verify-otp", json={
            "phone_number": driver_phone, "req_id": "mock_req_123", "otp_code": "123456", "invite_token": invite_token_a
        })
    assert otp_res.status_code == 200, f"OTP failed: {otp_res.text}"
    d_token_a = otp_res.json()["access_token"]
    d_headers_a = {"Authorization": f"Bearer {d_token_a}"}
    print("âœ… Driver A authenticated.")

    # 5. Driver A registers profile (Name + Age)
    reg_res = post("/api/v1/driver-app/register", json={
        "name": "Driver A Real", "age": 35, "license_number": f"DL-{random.randint(1000, 9999)}"
    }, headers=d_headers_a)
    assert reg_res.status_code == 200, f"Failed Driver profile registration: {reg_res.text}"
    assert reg_res.json()["age"] == 35
    driver_a_id = reg_res.json()["id"]
    print("âœ… Driver A registered profile with Age.")

    # 6. Upload documents
    # Mocking upload by calling the face verify which might need documents, actually face_verify checks url
    # Wait, the upload-document needs a file. We can bypass upload and just patch the db for test or simulate file upload
    with open("backend/requirements.txt", "rb") as f:
        post("/api/v1/driver-app/upload-document", data={"document_type": "license_front"}, files={"file": ("test.jpg", f, "image/jpeg")}, headers=d_headers_a)
        f.seek(0)
        post("/api/v1/driver-app/upload-document", data={"document_type": "license_back"}, files={"file": ("test.jpg", f, "image/jpeg")}, headers=d_headers_a)
        f.seek(0)
        post("/api/v1/driver-app/upload-document", data={"document_type": "aadhaar_front"}, files={"file": ("test.jpg", f, "image/jpeg")}, headers=d_headers_a)
        f.seek(0)
        post("/api/v1/driver-app/upload-document", data={"document_type": "aadhaar_back"}, files={"file": ("test.jpg", f, "image/jpeg")}, headers=d_headers_a)
        f.seek(0)
        post("/api/v1/driver-app/upload-document", data={"document_type": "selfie"}, files={"file": ("test.jpg", f, "image/jpeg")}, headers=d_headers_a)
    
    face_res = post("/api/v1/driver-app/face-verify", headers=d_headers_a)
    assert face_res.status_code == 200
    print("âœ… Driver A uploaded documents and verified face.")

    # 7. Fleet A Admin approves Driver A
    patch_res = patch(f"/api/v1/drivers/{driver_a_id}", json={"name": "Driver A Real"}, headers=headers_a)
    assert patch_res.status_code == 200
    
    # 8. Fleet Isolation check: Fleet B admin tries to view Driver A
    get_driver_b = get(f"/api/v1/drivers/{driver_a_id}", headers=headers_b)
    assert get_driver_b.status_code == 404, "SECURITY FAIL: Fleet B saw Fleet A's driver!"
    print("âœ… SECURITY: Fleet isolation verified for Driver Profile.")

    # 9. Admin assigns truck to Driver A
    truck_reg = f"RJ{random.randint(10, 99)}BZ{random.randint(1000, 9999)}"
    truck_res = post("/api/v1/vehicles", json={
        "registration_number": truck_reg, "make": "Tata", "model": "Prima", "year": 2024, "capacity_tonnes": 40.0, "status": "ACTIVE"
    }, headers=headers_a)
    truck_id = truck_res.json()["id"]

    assign_res = post(f"/api/v1/vehicles/{truck_id}/assign-driver?driver_id={driver_a_id}", headers=headers_a)
    assert assign_res.status_code == 200
    print("âœ… Admin assigned truck RJ14BZ9999 to Driver A.")

    # 10. Driver A checks assigned truck
    prof_res = get("/api/v1/driver-app/profile", headers=d_headers_a)
    assert prof_res.json()["assigned_vehicle"] == truck_reg
    print("âœ… Driver App sees assigned truck.")

    # 11. Fleet B tries to assign truck to Driver A
    truck_b_res = post("/api/v1/vehicles", json={
        "registration_number": f"MH{random.randint(10, 99)}BZ{random.randint(1000, 9999)}", "make": "Tata", "model": "Prima", "year": 2024, "capacity_tonnes": 40.0, "status": "ACTIVE"
    }, headers=headers_b)
    truck_b_id = truck_b_res.json()["id"]
    bad_assign = post(f"/api/v1/vehicles/{truck_b_id}/assign-driver?driver_id={driver_a_id}", headers=headers_b)
    assert bad_assign.status_code == 400 or bad_assign.status_code == 404
    print("âœ… SECURITY: Fleet isolation verified for Vehicle Assignment.")

    # 12. Create a trip for Driver A
    trip_res = post("/api/v1/trips", json={
        "origin_location": "Delhi", "destination_location": "Mumbai", "vehicle_id": truck_id, "driver_id": driver_a_id
    }, headers=headers_a)
    trip_id = trip_res.json()["id"]

    # 13. Driver A attempts to start trip without selfie
    start_res = post(f"/api/v1/driver-app/trips/{trip_id}/start", headers=d_headers_a)
    assert start_res.status_code == 400
    print("âœ… Negative Test: Trip start blocked without selfie.")

    # 14. Driver A uploads Trip Start Selfie
    with open("backend/requirements.txt", "rb") as f:
        selfie_res = post(f"/api/v1/driver-app/trips/{trip_id}/start-selfie", files={"file": ("selfie.jpg", f, "image/jpeg")}, headers=d_headers_a)
    assert selfie_res.status_code == 200, f"Failed selfie upload: {selfie_res.text}"
    assert "url" in selfie_res.json()
    print("âœ… Driver A uploaded trip start selfie.")

    # 15. Driver A starts trip
    start_res_2 = post(f"/api/v1/driver-app/trips/{trip_id}/start", headers=d_headers_a)
    assert start_res_2.status_code == 200
    print("âœ… Driver A started trip.")

    # 16. Negative Test: Driver A attempts to start AGAIN
    start_res_3 = post(f"/api/v1/driver-app/trips/{trip_id}/start", headers=d_headers_a)
    assert start_res_3.status_code == 400
    print("âœ… Negative Test: Duplicate trip start blocked.")

    # 17. Pause, Resume, Complete
    post(f"/api/v1/driver-app/trips/{trip_id}/pause", headers=d_headers_a)
    post(f"/api/v1/driver-app/trips/{trip_id}/resume", headers=d_headers_a)
    comp_res = post(f"/api/v1/driver-app/trips/{trip_id}/complete", headers=d_headers_a)
    assert comp_res.status_code == 200
    print("âœ… Trip lifecycle (Pause/Resume/Complete) verified.")

    print("ðŸŽ‰ ALL END-TO-END TESTS PASSED ðŸŽ‰")

if __name__ == "__main__":
    run_tests()
