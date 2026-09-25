import pytest
from httpx import AsyncClient
from main import app
from database import async_session_factory
from models.user import User, UserRole
from models.driver_domain import Driver, DriverStatus, VerificationStatus
from models.document import Document, DocumentVerificationStatus
from utils.security import create_access_token

@pytest.mark.asyncio
async def test_driver_activation_document_security():
    # Test 0 through 5 documents
    async with async_session_factory() as session:
        # Create an admin user
        import random
        admin_mobile = f"9999{random.randint(100000, 999999)}"
        admin = User(company_id=1, full_name="Admin", mobile_number=admin_mobile, role=UserRole.COMPANY_ADMIN, is_active=True, password_hash="hash")
        session.add(admin)
        await session.commit()
        await session.refresh(admin)
        admin_token = create_access_token(data={"sub": admin.mobile_number, "role": admin.role.value})
        
        # Test 0-5 loop
        for count in range(6):
            driver_mobile = f"8880{random.randint(100000, 999999)}"
            driver = Driver(company_id=1, name=f"Driver {count}", phone_number=driver_mobile, status=DriverStatus.INACTIVE, origin_type="test")
            session.add(driver)
            await session.commit()
            await session.refresh(driver)
            
            # Add documents
            required_cats = ["license_front", "license_back", "aadhaar_front", "aadhaar_back", "selfie"]
            for i in range(count):
                doc = Document(
                    company_id=1,
                    target_id=str(driver.id),
                    target_type="DRIVER",
                    category=required_cats[i],
                    file_url="test.jpg",
                    verification_status=DocumentVerificationStatus.APPROVED,
                    uploaded_by=admin.id
                )
                session.add(doc)
            await session.commit()
            
            # Make API Call
            from httpx import ASGITransport
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                resp = await ac.post(
                    f"/api/v1/drivers/{driver.id}/approve",
                    headers={"Authorization": f"Bearer {admin_token}"},
                    json={"action": "APPROVED"}
                )
            
            if count < 5:
                # Should fail because not all 5 are present and approved
                assert resp.status_code == 400
                assert "Cannot approve" in resp.json()["detail"]
            else:
                # Should succeed because all 5 are present and approved
                assert resp.status_code == 200
                assert resp.json()["verification_status"] == "APPROVED"
                assert resp.json()["status"] == "ACTIVE"
