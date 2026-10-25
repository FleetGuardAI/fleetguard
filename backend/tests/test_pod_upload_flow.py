import io
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from main import app
from database import get_db
from models.driver_domain import VerificationStatus
from models.trip_domain import Trip, TripStatus
from routers.driver_mobile import get_current_driver, get_onboarding_driver
from routers.owner_dashboard import get_current_user
from tests.trip.test_dispatch_operations_integrity import setup_dispatch_env

@pytest.mark.asyncio
async def test_pod_document_upload_and_submission(db_session, setup_dispatch_env):
    env = setup_dispatch_env
    drv_a = env["drv_a"]
    comp_a = env["comp_a"]
    user_admin_a = env["admin_a"]

    drv_a.verification_status = VerificationStatus.APPROVED
    await db_session.flush()

    trip = Trip(
        trip_id=f"TRP-POD-{env['suffix']}",
        company_id=comp_a.id,
        driver_id=drv_a.id,
        status=TripStatus.IN_PROGRESS,
        actual_start_time=datetime.now(timezone.utc) - timedelta(hours=1)
    )
    db_session.add(trip)
    await db_session.flush()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_onboarding_driver] = lambda: drv_a
    app.dependency_overrides[get_current_driver] = lambda: drv_a
    app.dependency_overrides[get_current_user] = lambda: user_admin_a

    with TestClient(app) as client:
        # 1. Upload Signature (document_type="signature")
        sig_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"
        sig_file = io.BytesIO(sig_bytes)
        upload_sig_resp = client.post(
            "/api/v1/driver-app/upload-document",
            data={"document_type": "signature"},
            files={"file": ("signature.png", sig_file, "image/png")}
        )
        assert upload_sig_resp.status_code == 200, f"Sig upload failed: {upload_sig_resp.text}"
        sig_data = upload_sig_resp.json()
        assert "url" in sig_data
        signature_url = sig_data["url"]
        # Driver verification status must remain APPROVED
        assert sig_data["verification_status"] == VerificationStatus.APPROVED.value

        # 2. Upload POD Photo (document_type="pod_photo")
        photo_bytes = b"\xff\xd8\xff\xe0\x00\x10JFIF"
        photo_file = io.BytesIO(photo_bytes)
        upload_photo_resp = client.post(
            "/api/v1/driver-app/upload-document",
            data={"document_type": "pod_photo"},
            files={"file": ("pod_photo.jpg", photo_file, "image/jpeg")}
        )
        assert upload_photo_resp.status_code == 200, f"Photo upload failed: {upload_photo_resp.text}"
        photo_data = upload_photo_resp.json()
        photo_url = photo_data["url"]

        # 3. Submit POD
        pod_resp = client.post(
            f"/api/v1/driver-app/pod/{trip.id}",
            json={
                "signature_url": signature_url,
                "photos": [photo_url],
                "remarks": "Package safely delivered to warehouse dock 3",
                "receiver_name": "Ramesh Kumar"
            }
        )
        assert pod_resp.status_code == 201, f"POD submission failed: {pod_resp.text}"
        pod_data = pod_resp.json()
        assert pod_data["signature_url"] == signature_url
        assert pod_data["receiver_name"] == "Ramesh Kumar"
        assert pod_data["photos"] == [photo_url]

        # 4. Verify Driver GET POD
        driver_get_pod = client.get(f"/api/v1/driver-app/pod/{trip.id}")
        assert driver_get_pod.status_code == 200
        assert driver_get_pod.json()["receiver_name"] == "Ramesh Kumar"

        # 5. Verify Owner GET POD
        owner_get_pod = client.get(f"/api/v1/owner/dashboard/trips/{trip.id}/pod")
        assert owner_get_pod.status_code == 200
        assert owner_get_pod.json()["receiver_name"] == "Ramesh Kumar"

    app.dependency_overrides.clear()
