"""
FleetGuard — Phase B, Batch 6 Security Verification Suite
Tests:
1. FG-SEC-050: Strict financial and cost validation (reject negative / zero amounts in Wallets, Expenses, Maintenance)
2. FG-SEC-028: Horizontal IDOR document isolation for drivers (drivers cannot access other drivers' or company-wide documents)
3. FG-SEC-029: Bounded file uploads & memory exhaustion protection (reject oversized payloads before buffering to prevent OOM DoS)
4. FG-SEC-047: Redaction of plaintext GPS coordinates in Emergency SOS application logs
"""

import io
import uuid
import pytest
import pytest_asyncio
import logging
from datetime import datetime, timezone
from pydantic import ValidationError
from starlette.datastructures import UploadFile
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from main import app
from models.user import User, UserRole
from models.company import Company, CompanyStatus
from models.driver_domain import Driver, DriverStatus, DutyStatus
from models.document import Document, DocumentStorageStatus, DocumentVerificationStatus
from schemas.expense_domain import ExpenseCreateRequest, ExpenseUpdateRequest
from routers.driver_wallet import AdvanceRequest
from routers.driver_expenses import ExpenseCreateRequest as DriverExpenseCreateRequest
from schemas.maintenance_domain import (
    MaintenanceCreateRequest,
    MaintenanceUpdateRequest,
    MaintenancePartCreate,
    MaintenancePartUpdate,
    MaintenanceLabourCreate,
    MaintenanceLabourUpdate
)
from services.file_upload_service import read_bounded_file, MAX_OCR_FILE_SIZE_BYTES
from routers.documents import get_document
from repositories.document_repository import DocumentRepository
from services.document_service import DocumentService
from routers.driver_emergency import trigger_sos, SosRequest


# ==============================================================================
# FG-SEC-050: Financial & Cost Negative / Zero Amount Rejection Tests
# ==============================================================================

def test_driver_wallet_advance_negative_amount_rejected():
    """Verify AdvanceRequest rejects negative amount."""
    with pytest.raises(ValidationError) as exc:
        AdvanceRequest(amount=-500.0, reason="Need cash")
    assert "greater than 0" in str(exc.value)


def test_driver_wallet_advance_zero_amount_rejected():
    """Verify AdvanceRequest rejects zero amount."""
    with pytest.raises(ValidationError) as exc:
        AdvanceRequest(amount=0.0, reason="Zero cash")
    assert "greater than 0" in str(exc.value)


def test_driver_expense_negative_amount_rejected():
    """Verify DriverExpenseCreateRequest rejects negative amount."""
    with pytest.raises(ValidationError) as exc:
        DriverExpenseCreateRequest(category="FUEL", amount=-150.0)
    assert "greater than 0" in str(exc.value)


def test_driver_expense_zero_amount_rejected():
    """Verify DriverExpenseCreateRequest rejects zero amount."""
    with pytest.raises(ValidationError) as exc:
        DriverExpenseCreateRequest(category="TOLL", amount=0.0)
    assert "greater than 0" in str(exc.value)


def test_expense_domain_create_negative_amount_rejected():
    """Verify ExpenseCreateRequest rejects negative amount."""
    with pytest.raises(ValidationError) as exc:
        ExpenseCreateRequest(amount=-1000.0, category="REPAIR")
    assert "greater than 0" in str(exc.value)


def test_expense_domain_create_zero_amount_rejected():
    """Verify ExpenseCreateRequest rejects zero amount."""
    with pytest.raises(ValidationError) as exc:
        ExpenseCreateRequest(amount=0.0, category="REPAIR")
    assert "greater than 0" in str(exc.value)


def test_expense_domain_update_negative_amount_rejected():
    """Verify ExpenseUpdateRequest rejects negative amount."""
    with pytest.raises(ValidationError) as exc:
        ExpenseUpdateRequest(amount=-50.0)
    assert "greater than 0" in str(exc.value)


def test_maintenance_create_negative_cost_rejected():
    """Verify MaintenanceCreateRequest rejects negative costs."""
    with pytest.raises(ValidationError) as exc:
        MaintenanceCreateRequest(cost=-250.0)
    assert "greater than or equal to 0" in str(exc.value)


def test_maintenance_create_negative_other_cost_rejected():
    """Verify MaintenanceCreateRequest rejects negative other_cost."""
    with pytest.raises(ValidationError) as exc:
        MaintenanceCreateRequest(other_cost=-10.0)
    assert "greater than or equal to 0" in str(exc.value)


def test_maintenance_part_negative_unit_cost_rejected():
    """Verify MaintenancePartCreate rejects negative unit_cost."""
    with pytest.raises(ValidationError) as exc:
        MaintenancePartCreate(name="Filter", unit_cost=-99.0)
    assert "greater than or equal to 0" in str(exc.value)


def test_maintenance_part_zero_quantity_rejected():
    """Verify MaintenancePartCreate rejects quantity < 1."""
    with pytest.raises(ValidationError) as exc:
        MaintenancePartCreate(name="Filter", quantity=0, unit_cost=50.0)
    assert "greater than or equal to 1" in str(exc.value)


def test_maintenance_labour_negative_hours_rejected():
    """Verify MaintenanceLabourCreate rejects negative hours."""
    with pytest.raises(ValidationError) as exc:
        MaintenanceLabourCreate(description="Diagnostics", hours=-2.5)
    assert "greater than or equal to 0" in str(exc.value)


def test_maintenance_labour_negative_rate_rejected():
    """Verify MaintenanceLabourCreate rejects negative hourly_rate."""
    with pytest.raises(ValidationError) as exc:
        MaintenanceLabourCreate(description="Diagnostics", hours=2.0, hourly_rate=-500.0)
    assert "greater than or equal to 0" in str(exc.value)


# ==============================================================================
# FG-SEC-029: Bounded File Uploads & OOM DoS Prevention Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_read_bounded_file_accepts_valid_payload():
    """Verify valid size files read successfully without error."""
    payload = b"Hello, FleetGuard Secure File!"
    file_obj = io.BytesIO(payload)
    upload = UploadFile(file=file_obj, filename="test.txt")
    
    content = await read_bounded_file(upload, max_bytes=1024)
    assert content == payload


@pytest.mark.asyncio
async def test_read_bounded_file_rejects_oversized_payload():
    """Verify payload exceeding max_bytes raises HTTP 413 without full buffering."""
    # Create 2MB payload with max_bytes limit of 1MB
    oversized = b"X" * (1024 * 1024 + 100)
    file_obj = io.BytesIO(oversized)
    upload = UploadFile(file=file_obj, filename="huge.bin")

    with pytest.raises(HTTPException) as exc:
        await read_bounded_file(upload, max_bytes=1024 * 1024)

    assert exc.value.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
    assert "File exceeds maximum allowed size" in exc.value.detail


# ==============================================================================
# FG-SEC-028: Driver Horizontal IDOR Document Isolation Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_driver_cannot_view_other_driver_documents(db_session: AsyncSession):
    """Verify that a driver cannot access a document belonging to another driver."""
    company = Company(
        company_name="Driver Doc Isolation Co",
        owner_name="Test Owner",
        mobile_number="+919811111111",
        email="doc_iso@example.com",
        status=CompanyStatus.ACTIVE
    )
    db_session.add(company)
    await db_session.flush()

    driver1_user = User(
        company_id=company.id,
        full_name="Driver One",
        mobile_number="+919811111112",
        email="driver1@example.com",
        password_hash="mock_hash_for_test",
        role=UserRole.DRIVER,
        is_active=True
    )
    driver2_user = User(
        company_id=company.id,
        full_name="Driver Two",
        mobile_number="+919811111113",
        email="driver2@example.com",
        password_hash="mock_hash_for_test",
        role=UserRole.DRIVER,
        is_active=True
    )
    db_session.add_all([driver1_user, driver2_user])
    await db_session.flush()

    # Create Document owned by Driver 2
    doc_id = uuid.uuid4()
    doc = Document(
        id=doc_id,
        original_filename="driver2_license.pdf",
        mime_type="application/pdf",
        storage_path=f"company_{company.id}/driver2_license.pdf",
        status=DocumentStorageStatus.STORED,
        uploaded_by=str(driver2_user.id),
        company_id=company.id,
        target_id=str(driver2_user.id),
        target_type="driver",
        verification_status=DocumentVerificationStatus.APPROVED
    )
    db_session.add(doc)
    await db_session.commit()

    service = DocumentService(db_session)

    # Driver 1 attempts to access Driver 2's document -> MUST raise 403 Forbidden
    with pytest.raises(HTTPException) as exc:
        await get_document(
            document_id=doc_id,
            service=service,
            db=db_session,
            current_user=driver1_user
        )
    assert exc.value.status_code == status.HTTP_403_FORBIDDEN
    assert "Drivers can only access their own documents" in exc.value.detail


@pytest.mark.asyncio
async def test_driver_can_view_own_document(db_session: AsyncSession):
    """Verify that a driver can successfully access their own document."""
    company = Company(
        company_name="Driver Own Doc Co",
        owner_name="Owner Two",
        mobile_number="+919811111114",
        email="driver_own_doc@example.com",
        status=CompanyStatus.ACTIVE
    )
    db_session.add(company)
    await db_session.flush()

    driver_user = User(
        company_id=company.id,
        full_name="Authorized Driver",
        mobile_number="+919811111115",
        email="authdriver@example.com",
        password_hash="mock_hash_for_test",
        role=UserRole.DRIVER,
        is_active=True
    )
    db_session.add(driver_user)
    await db_session.flush()

    doc_id = uuid.uuid4()
    doc = Document(
        id=doc_id,
        original_filename="my_license.pdf",
        mime_type="application/pdf",
        storage_path=f"company_{company.id}/my_license.pdf",
        status=DocumentStorageStatus.STORED,
        uploaded_by=str(driver_user.id),
        company_id=company.id,
        target_id=str(driver_user.id),
        target_type="driver",
        verification_status=DocumentVerificationStatus.APPROVED
    )
    db_session.add(doc)
    await db_session.commit()

    service = DocumentService(db_session)
    result = await get_document(
        document_id=doc_id,
        service=service,
        db=db_session,
        current_user=driver_user
    )
    assert result.id == doc_id
    assert result.original_filename == "my_license.pdf"


@pytest.mark.asyncio
async def test_driver_list_documents_scopes_to_driver_only(db_session: AsyncSession):
    """Verify repository list_documents correctly filters out other drivers' documents."""
    company_id = 997
    driver_user_id = str(uuid.uuid4())
    other_user_id = str(uuid.uuid4())

    repo = DocumentRepository(db_session)

    # Document 1: uploaded by this driver
    doc1 = Document(
        id=uuid.uuid4(),
        original_filename="driver_doc1.pdf",
        mime_type="application/pdf",
        storage_path="path1",
        status=DocumentStorageStatus.STORED,
        uploaded_by=driver_user_id,
        company_id=company_id,
    )
    # Document 2: uploaded by someone else
    doc2 = Document(
        id=uuid.uuid4(),
        original_filename="other_doc2.pdf",
        mime_type="application/pdf",
        storage_path="path2",
        status=DocumentStorageStatus.STORED,
        uploaded_by=other_user_id,
        company_id=company_id,
    )
    db_session.add_all([doc1, doc2])
    await db_session.commit()

    # Query with driver scoping
    driver_docs = await repo.list_documents(
        company_id=company_id,
        driver_user_id=driver_user_id,
        driver_target_ids=[driver_user_id]
    )
    assert len(driver_docs) == 1
    assert driver_docs[0].id == doc1.id


# ==============================================================================
# FG-SEC-047: Emergency Alert GPS Redaction Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_emergency_alert_logs_redact_gps_coordinates(db_session: AsyncSession, caplog):
    """Verify that triggering an SOS alert does not print raw lat/long coordinates in application logs."""
    company = Company(
        company_name="SOS Privacy Fleet",
        owner_name="Owner SOS",
        mobile_number="+919800000001",
        email="sos_privacy@fleetguard.com",
        status=CompanyStatus.ACTIVE
    )
    db_session.add(company)
    await db_session.flush()

    driver = Driver(
        company_id=company.id,
        name="Secret Driver",
        phone_number="+919800000002",
        license_number="DL1234567890",
        status=DriverStatus.ACTIVE,
        duty_status=DutyStatus.ON_DUTY
    )
    db_session.add(driver)
    await db_session.commit()
    await db_session.refresh(driver)

    lat = 28.613939
    lng = 77.209021

    payload = SosRequest(
        latitude=lat,
        longitude=lng,
        message="Medical emergency"
    )

    with caplog.at_level(logging.CRITICAL, logger="fleetguard.emergency"):
        resp = await trigger_sos(
            payload=payload,
            driver=driver,
            db=db_session
        )
        assert resp.id is not None
        assert resp.latitude == lat
        assert resp.longitude == lng

    # Verify log output: MUST contain REDACTED and MUST NOT contain raw lat/lng
    log_records = [r.message for r in caplog.records if "fleetguard.emergency" in r.name]
    assert len(log_records) > 0
    sos_log = log_records[0]

    assert "Coordinates: REDACTED" in sos_log
    assert str(lat) not in sos_log
    assert str(lng) not in sos_log
