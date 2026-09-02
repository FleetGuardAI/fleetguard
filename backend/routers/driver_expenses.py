"""
FleetGuard — Driver Expense Router with AI OCR & Fraud Detection

Allows drivers to submit fuel, toll, parking, repair, and food expenses with receipt photos.
Simulates AI OCR extraction & fraud detection for production-ready API interface.
"""

import uuid
import logging
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, status
from pydantic import BaseModel
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db, get_uow
from models.expense_domain import Expense, ExpenseCategory, ExpenseStatus
from models.operational_event import EventType, CaptureMethod, EntityType
from models.driver_domain import Driver
from services.auth_service import get_current_user
from models.user import User
from models.vehicle_domain import Vehicle
from models.trip_domain import Trip
from models.user import User
from schemas.operational_event import OperationalEventCreate
from services.operational_event_service import OperationalEventService
from services.file_upload_service import storage_service
from models.driver_domain import Driver
from services.auth_service import get_current_user
from models.user import User
from routers.driver_mobile import get_current_driver

logger = logging.getLogger("fleetguard.driver_expenses")

router = APIRouter(prefix="/api/v1/driver-app", tags=["Driver Expenses"])


# --- Schemas ---

class ExpenseCreateRequest(BaseModel):
    category: str  # FUEL, TOLL, PARKING, MAINTENANCE, ALLOWANCE, MISCELLANEOUS
    amount: float
    description: Optional[str] = None
    receipt_url: Optional[str] = None
    vehicle_id: Optional[int] = None
    trip_id: Optional[int] = None
    driver_id: int
    
    # Fuel specific fields (Milestone 1C)
    fuel_quantity_liters: Optional[float] = None
    odometer_reading: Optional[float] = None
    is_full_tank: Optional[bool] = None


class ExpenseResponse(BaseModel):
    id: int
    business_id: str
    category: str
    amount: float
    currency: str = "INR"
    status: str
    expense_date: datetime
    description: Optional[str] = None
    receipt_reference: Optional[str] = None
    vehicle_id: Optional[int] = None
    driver_id: Optional[int] = None
    trip_id: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class OcrExtractResponse(BaseModel):
    vendor: str
    gst_number: Optional[str] = None
    date: str
    amount: float
    category: str
    fraud_risk_score: float  # 0.0 to 1.0
    is_suspicious: bool
    fraud_flags: List[str] = []


@router.post("/expenses/ocr", response_model=OcrExtractResponse)
async def process_receipt_ocr(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    uow = Depends(get_uow),
):
    """
    Process receipt image via AI OCR framework.
    Extracts Vendor, Date, Amount.
    """
    if not current_user.company_id:
        raise HTTPException(status_code=403, detail="User is not associated with a company")

    # Save temp file for OCR
    import os
    import tempfile
    
    file_ext = os.path.splitext(file.filename or "")[1] or ".jpg"
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    await file.seek(0)

    try:
        url = await storage_service.upload_file(file, folder="receipts")
        
        provider_type = settings.OCR_PROVIDER.lower()
        if provider_type == "openai":
            if not settings.OPENAI_API_KEY and not settings.GEMINI_API_KEY:
                raise HTTPException(status_code=503, detail="OpenAI API key not configured for OCR")
            provider = GoogleDocumentAIProvider()
        else:
            provider = MockOCRProvider()

        ocr_result = await provider.extract_text(tmp_path, file.content_type or "image/jpeg")
        
        if provider_type == "openai":
            try:
                parsed_data = json.loads(ocr_result.text)
                return OcrExtractResponse(
                    vendor=parsed_data.get("vendor", "Unknown Vendor"),
                    gst_number=parsed_data.get("gst_number"),
                    date=parsed_data.get("date", datetime.now().strftime("%Y-%m-%d")),
                    amount=float(parsed_data.get("amount", 0.0)),
                    category=parsed_data.get("category", "MISCELLANEOUS"),
                    fraud_risk_score=float(parsed_data.get("fraud_risk_score", 0.0)),
                    is_suspicious=bool(parsed_data.get("is_suspicious", False)),
                    fraud_flags=parsed_data.get("fraud_flags", [])
                )
            except json.JSONDecodeError:
                logger.error(f"Failed to parse OCR JSON: {ocr_result.text}")
                raise HTTPException(status_code=500, detail="Failed to parse OCR response")
        else:
            return OcrExtractResponse(
                vendor="HP Fuel Station #482",
                gst_number="27AAACH1234H1Z5",
                date=datetime.now().strftime("%Y-%m-%d"),
                amount=2500.0,
                category="FUEL",
                fraud_risk_score=0.08,
                is_suspicious=False,
                fraud_flags=[],
            )
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
    content = await file.read()
    await file.seek(0)
    
    url = await storage_service.upload_file(file, folder="receipts")
    
    from infrastructure.ocr.provider import get_ocr_provider
    provider = get_ocr_provider()
    
    try:
        ocr_result = await provider.extract_text(
            file_data=content, 
            mime_type=file.content_type or "image/jpeg", 
            document_type="receipt"
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"OCR failed: {e}")
        raise HTTPException(status_code=500, detail="OCR processing failed")
        
    fields = ocr_result.extracted_fields
    
    # Parse extracted fields robustly
    vendor = fields.get("MerchantName", "Unknown Vendor")
    date = fields.get("TransactionDate", datetime.now().strftime("%Y-%m-%d"))
    
    # Attempt to normalize amount. 
    # Handle typically parsed values.
    amount_raw = fields.get("Total")
    amount = 0.0
    if amount_raw is not None:
        try:
            if isinstance(amount_raw, str):
                # Clean up typical currency strings like "₹ 2,500.00"
                clean_amount = amount_raw.replace("₹", "").replace("Rs.", "").replace("INR", "").replace(",", "").strip()
                amount = float(clean_amount)
            else:
                amount = float(amount_raw)
        except ValueError:
            amount = 0.0
            
    gst_number = fields.get("MerchantTaxId")

    # Store OCR evidence using the existing Evidence framework
    try:
        from models.operational_event import OperationalEvent, EventType, EntityType, CaptureMethod
        from models.evidence import Evidence, EvidenceType, EvidenceStatus
        import json
        
        # Create a document upload event
        event = OperationalEvent(
            event_type=EventType.DOCUMENT_UPLOADED,
            entity_type=EntityType.DOCUMENT,
            entity_id=url,
            occurred_at=datetime.now(timezone.utc),
            capture_method=CaptureMethod.SYSTEM_GENERATED,
            created_by="system",
            payload={"url": url, "filename": file.filename}
        )
        db.add(event)
        await db.flush() # To get event.id
        
        # Create the OCR evidence record
        evidence = Evidence(
            event_id=event.id,
            evidence_type=EvidenceType.OCR_EXTRACTION,
            source=ocr_result.provider_name,
            status=EvidenceStatus.COMPLETED,
            summary=f"Extracted {amount} from {vendor}",
            details=ocr_result.text[:500] if ocr_result.text else None,
            raw_data={
                "extracted_fields": ocr_result.extracted_fields,
                "confidence": ocr_result.confidence,
                "processing_time_ms": ocr_result.processing_time_ms,
                "provider_request_id": ocr_result.provider_request_id,
                "metadata": ocr_result.metadata
            }
        )
        db.add(evidence)
        await db.commit()
    except Exception as e:
        logger.error(f"Failed to save OCR evidence: {e}")
        await db.rollback()

    return OcrExtractResponse(
        vendor=vendor,
        gst_number=gst_number,
        date=date,
        amount=amount,
        category="MISCELLANEOUS", # Default category
        fraud_risk_score=0.0,     # Not implemented
        is_suspicious=False,      # Not implemented
        fraud_flags=[],           # Not implemented
    )


@router.post("/expenses", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
async def create_expense(
    payload: ExpenseCreateRequest,
    driver: Driver = Depends(get_current_driver),
    db: AsyncSession = Depends(get_db),
    uow = Depends(get_uow),
    current_user: User = Depends(get_current_user)
):
    """Submit a driver expense."""
    if not current_user.company_id:
        raise HTTPException(status_code=403, detail="User is not associated with a company")

    # Validate driver ownership
    driver = await db.get(Driver, payload.driver_id)
    if not driver or driver.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Unauthorized driver")

    # Validate vehicle ownership if present
    if payload.vehicle_id:
        vehicle = await db.get(Vehicle, payload.vehicle_id)
        if not vehicle or vehicle.company_id != current_user.company_id:
            raise HTTPException(status_code=403, detail="Unauthorized vehicle")

    # Validate trip ownership if present
    if payload.trip_id:
        trip = await db.get(Trip, payload.trip_id)
        if not trip or trip.company_id != current_user.company_id:
            raise HTTPException(status_code=403, detail="Unauthorized trip")

    try:
        cat_enum = ExpenseCategory(payload.category.upper())
    except ValueError:
        cat_enum = ExpenseCategory.MISCELLANEOUS

    # If it's a fuel expense, validate and dispatch operational event
    if cat_enum == ExpenseCategory.FUEL and payload.fuel_quantity_liters is not None:
        if payload.fuel_quantity_liters <= 0:
            raise HTTPException(status_code=400, detail="Fuel quantity must be greater than 0")
        if not payload.vehicle_id:
            raise HTTPException(status_code=400, detail="vehicle_id is required for fuel expenses")
            
        event_service = OperationalEventService(uow)
        
        event_payload = {
            "liters": payload.fuel_quantity_liters,
            "odometer_km": payload.odometer_reading,
            "is_full_tank": bool(payload.is_full_tank),
            "cost_inr": payload.amount,
            "receipt_url": payload.receipt_url
        }
        
        event_create = OperationalEventCreate(
            event_type=EventType.FUEL_FILLED,
            entity_type=EntityType.VEHICLE,
            entity_id=str(payload.vehicle_id),
            occurred_at=datetime.now(timezone.utc),
            capture_method=CaptureMethod.MANUAL_ENTRY,
            created_by=f"driver_{payload.driver_id}",
            payload=event_payload
        )
        
        await event_service.create_event(event_create)
        await uow.commit()

    business_id = f"exp_{uuid.uuid4().hex[:12]}"

    expense = Expense(
        business_id=business_id,
        category=cat_enum,
        amount=payload.amount,
        currency="INR",
        status=ExpenseStatus.PENDING,
        expense_date=datetime.now(timezone.utc),
        description=payload.description,
        receipt_reference=payload.receipt_url,
        vehicle_id=payload.vehicle_id,
        driver_id=driver.id,
        company_id=driver.company_id,
        trip_id=payload.trip_id,
        origin_type="driver_app",
        origin_id=f"driver_{driver.id}",
    )

    db.add(expense)
    await db.commit()
    await db.refresh(expense)

    logger.info(f"Expense {expense.id} created by driver {driver.id}")

    return ExpenseResponse(
        id=expense.id,
        business_id=expense.business_id,
        category=expense.category.value,
        amount=expense.amount,
        currency=expense.currency,
        status=expense.status.value,
        expense_date=expense.expense_date,
        description=expense.description,
        receipt_reference=storage_service.create_signed_url(expense.receipt_reference) if expense.receipt_reference else None,
        vehicle_id=expense.vehicle_id,
        driver_id=expense.driver_id,
        trip_id=expense.trip_id,
        created_at=expense.created_at,
    )


@router.get("/expenses", response_model=List[ExpenseResponse])
async def list_driver_expenses(
    driver_id: Optional[int] = Query(None), # Kept for backwards compatibility but ignored
    limit: int = Query(50, ge=1, le=200),
    driver: Driver = Depends(get_current_driver),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List expenses for a specific driver."""
    result = await db.execute(
        select(Expense)
        .where(Expense.driver_id == driver.id)
        .order_by(desc(Expense.created_at))
        .limit(limit)
    )
    expenses = result.scalars().all() or []

    return [
        ExpenseResponse(
            id=exp.id,
            business_id=exp.business_id,
            category=exp.category.value,
            amount=exp.amount,
            currency=exp.currency,
            status=exp.status.value,
            expense_date=exp.expense_date,
            description=exp.description,
            receipt_reference=storage_service.create_signed_url(exp.receipt_reference) if exp.receipt_reference else None,
            vehicle_id=exp.vehicle_id,
            driver_id=exp.driver_id,
            trip_id=exp.trip_id,
            created_at=exp.created_at,
        )
        for exp in expenses
    ]
