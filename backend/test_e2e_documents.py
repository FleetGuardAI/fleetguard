import asyncio
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from fastapi.testclient import TestClient
from database import async_session_factory
from models.user import User, UserRole
from domain.driver.models.driver import Driver
from main import app
from auth.security import create_access_token

async def test_flow():
    async with async_session_factory() as session:
        from sqlalchemy import select
        # 1. Get a Driver
        result = await session.execute(select(Driver).limit(1))
        driver = result.scalar_one_or_none()
        if not driver:
            print("No driver found")
            return
            
        result = await session.execute(select(User).where(User.mobile_number == driver.phone_number))
        driver_user = result.scalar_one_or_none()
        
        # 2. Get an Admin
        result = await session.execute(select(User).where(User.role == UserRole.SUPER_ADMIN).limit(1))
        admin_user = result.scalar_one_or_none()

    driver_token = create_access_token(data={"sub": driver_user.mobile_number, "role": driver_user.role.value})
    admin_token = create_access_token(data={"sub": admin_user.mobile_number, "role": admin_user.role.value})

    with TestClient(app) as client:
        print("=== 1. Driver uploads document ===")
        # We need a file to upload
        with open("test_upload.txt", "w") as f:
            f.write("test content")
            
        with open("test_upload.txt", "rb") as f:
            resp = client.post(
                "/api/v1/driver-app/upload-document",
                headers={"Authorization": f"Bearer {driver_token}"},
                data={"document_type": "license_front"},
                files={"file": ("test.txt", f, "text/plain")}
            )
        print("Upload Response:", resp.status_code)
        
        print("\n=== 2. Driver GET documents (Expect PENDING) ===")
        resp = client.get("/api/v1/driver-app/documents", headers={"Authorization": f"Bearer {driver_token}"})
        docs = resp.json()
        target_doc = next((d for d in docs if d["category"] == "license_front"), None)
        print(f"Driver sees: {target_doc['category']} -> {target_doc['verification_status']}")
        doc_id = target_doc["id"]
        
        print("\n=== 3. Admin rejects document ===")
        resp = client.post(
            f"/api/v1/documents/{doc_id}/verify",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"status": "REJECTED", "rejection_reason": "Image is blurry"}
        )
        print("Admin Reject Response:", resp.status_code)
        
        print("\n=== 4. Driver GET documents (Expect REJECTED with reason) ===")
        resp = client.get("/api/v1/driver-app/documents", headers={"Authorization": f"Bearer {driver_token}"})
        docs = resp.json()
        target_doc = next((d for d in docs if d["category"] == "license_front"), None)
        print(f"Driver sees: {target_doc['category']} -> {target_doc['verification_status']} (Reason: {target_doc['rejection_reason']})")
        
        print("\n=== 5. Driver uploads replacement document ===")
        with open("test_upload.txt", "rb") as f:
            resp = client.post(
                "/api/v1/driver-app/upload-document",
                headers={"Authorization": f"Bearer {driver_token}"},
                data={"document_type": "license_front"},
                files={"file": ("test2.txt", f, "text/plain")}
            )
            
        print("\n=== 6. Admin GET driver documents ===")
        resp = client.get(f"/api/v1/documents/driver/{driver.id}", headers={"Authorization": f"Bearer {admin_token}"})
        admin_docs = resp.json()
        target_doc = next((d for d in admin_docs if d["category"] == "license_front"), None)
        print(f"Admin sees latest is: {target_doc['verification_status']}")
        new_doc_id = target_doc["id"]
        
        print("\n=== 7. Admin approves document ===")
        resp = client.post(
            f"/api/v1/documents/{new_doc_id}/verify",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"status": "APPROVED"}
        )
        print("Admin Approve Response:", resp.status_code)
        
        print("\n=== 8. Driver GET documents (Expect APPROVED) ===")
        resp = client.get("/api/v1/driver-app/documents", headers={"Authorization": f"Bearer {driver_token}"})
        docs = resp.json()
        target_doc = next((d for d in docs if d["category"] == "license_front"), None)
        print(f"Driver sees: {target_doc['category']} -> {target_doc['verification_status']}")
        
if __name__ == "__main__":
    asyncio.run(test_flow())
