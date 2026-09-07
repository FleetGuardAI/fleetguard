import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.document import Document, DocumentVerificationStatus, DocumentStorageStatus
from models.driver_domain import Driver, VerificationStatus
from models.user import User, UserRole
import uuid

@pytest.fixture
async def admin_user_token(client: AsyncClient, db_session: AsyncSession):
    # Mock or create admin user and return a valid auth token/headers
    # Assuming there's a utility for this, or we just mock the dependency
    pass

@pytest.mark.asyncio
async def test_document_verification_replacement_flow(
    client,
    db_session: AsyncSession,
):
    """
    Test the scenario requested by the user:
    Initial: license_front -> REJECTED
    Replacement: license_front -> PENDING
    Approval: license_front old -> REJECTED, latest -> APPROVED
    Overall driver status must evaluate only the latest document.
    """
    # 1. Setup Company, User, and Driver
    from models.company import Company
    company = Company(company_name="Test Co", owner_name="Owner", mobile_number="1234567890")
    db_session.add(company)
    await db_session.flush()

    user = User(
        mobile_number="9999999999", 
        role=UserRole.DRIVER, 
        company_id=company.id, 
        is_active=True,
        full_name="Test Driver",
        password_hash="fake"
    )
    admin_user = User(
        mobile_number="8888888888",
        role=UserRole.COMPANY_ADMIN,
        company_id=company.id,
        is_active=True,
        full_name="Admin",
        password_hash="fake"
    )
    db_session.add_all([user, admin_user])
    await db_session.flush()

    driver = Driver(
        user_id=user.id, 
        company_id=company.id, 
        name="Test Driver", 
        phone_number="9999999999",
        verification_status=VerificationStatus.PENDING_DOCUMENTS,
        origin_type="test"
    )
    db_session.add(driver)
    await db_session.flush()

    # 2. Add an initial REJECTED document
    doc1 = Document(
        original_filename="lic1.jpg",
        mime_type="image/jpeg",
        storage_path="path/to/lic1",
        status=DocumentStorageStatus.AVAILABLE,
        verification_status=DocumentVerificationStatus.REJECTED,
        rejection_reason="Blurry",
        category="license_front",
        target_id=str(driver.id),
        target_type="DRIVER",
        company_id=company.id
    )
    
    # 3. Add the rest of the required documents as APPROVED
    docs = [doc1]
    for cat in ["license_back", "aadhaar_front", "aadhaar_back", "selfie"]:
        docs.append(
            Document(
                original_filename=f"{cat}.jpg",
                mime_type="image/jpeg",
                storage_path=f"path/to/{cat}",
                status=DocumentStorageStatus.AVAILABLE,
                verification_status=DocumentVerificationStatus.APPROVED,
                category=cat,
                target_id=str(driver.id),
                target_type="DRIVER",
                company_id=company.id
            )
        )
    db_session.add_all(docs)
    await db_session.commit()

    import asyncio
    await asyncio.sleep(1)

    # At this point, driver has 1 REJECTED, 4 APPROVED.
    # To test the API, let's mock authentication
    from main import app
    from routers.auth import get_current_user
    
    app.dependency_overrides[get_current_user] = lambda: admin_user

    # 4. Driver uploads a replacement document (we create it directly as PENDING)
    doc2 = Document(
        original_filename="lic2.jpg",
        mime_type="image/jpeg",
        storage_path="path/to/lic2",
        status=DocumentStorageStatus.AVAILABLE,
        verification_status=DocumentVerificationStatus.PENDING,
        category="license_front",
        target_id=str(driver.id),
        target_type="DRIVER",
        company_id=company.id
    )
    db_session.add(doc2)
    await db_session.commit()

    # 5. Admin Approves the NEW document
    response = client.post(
        f"/api/v1/documents/{doc2.id}/verify",
        json={"status": "APPROVED"}
    )
    assert response.status_code == 200

    # 6. Verify conditions
    await db_session.refresh(doc1)
    await db_session.refresh(doc2)
    await db_session.refresh(driver)

    # old document remains REJECTED
    assert doc1.verification_status == DocumentVerificationStatus.REJECTED
    
    # latest document is APPROVED
    assert doc2.verification_status == DocumentVerificationStatus.APPROVED

    # overall verification considers latest document only and should be APPROVED
    assert driver.verification_status == VerificationStatus.APPROVED
    
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_rejection_reason_required(client, db_session: AsyncSession):
    # Setup Admin
    from models.company import Company
    company = Company(company_name="Test Co", owner_name="Owner", mobile_number="1234567890")
    db_session.add(company)
    await db_session.flush()

    admin_user = User(
        mobile_number="8888888888",
        role=UserRole.COMPANY_ADMIN,
        company_id=company.id,
        is_active=True,
        full_name="Admin",
        password_hash="fake"
    )
    db_session.add(admin_user)
    await db_session.flush()

    doc = Document(
        original_filename="test.jpg",
        mime_type="image/jpeg",
        storage_path="path/to/test",
        status=DocumentStorageStatus.AVAILABLE,
        verification_status=DocumentVerificationStatus.PENDING,
        category="selfie",
        target_id="1",
        target_type="DRIVER",
        company_id=company.id
    )
    db_session.add(doc)
    await db_session.commit()

    from main import app
    from routers.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: admin_user

    # Reject without reason -> 400
    res = client.post(f"/api/v1/documents/{doc.id}/verify", json={"status": "REJECTED"})
    assert res.status_code == 400
    assert "Rejection reason is required" in res.json()["detail"]

    # Reject with reason -> 200
    res = client.post(f"/api/v1/documents/{doc.id}/verify", json={"status": "REJECTED", "rejection_reason": "Too dark"})
    assert res.status_code == 200
    await db_session.refresh(doc)
    assert doc.verification_status == DocumentVerificationStatus.REJECTED
    assert doc.rejection_reason == "Too dark"
    
    # Approve clears reason -> 200
    res = client.post(f"/api/v1/documents/{doc.id}/verify", json={"status": "APPROVED"})
    assert res.status_code == 200
    await db_session.refresh(doc)
    assert doc.verification_status == DocumentVerificationStatus.APPROVED
    assert doc.rejection_reason is None

    app.dependency_overrides.clear()
