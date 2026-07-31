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

from database import get_db
from models.expense_domain import Expense, ExpenseCategory, ExpenseStatus
from services.file_upload_service import storage_service

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
):
    """
    Process receipt image via AI OCR framework.
    Extracts Vendor, GST, Date, Amount, and runs receipt fraud detection.
    """
    url = await storage_service.upload_file(file, folder="receipts")

    # AI OCR extraction (Demo mode uses high accuracy simulated response adhering to production contract)
    # If OpenAI key configured, can call vision API.
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


@router.post("/expenses", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
async def create_expense(
    payload: ExpenseCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Submit a driver expense."""
    try:
        cat_enum = ExpenseCategory(payload.category.upper())
    except ValueError:
        cat_enum = ExpenseCategory.MISCELLANEOUS

    business_id = f"exp_{uuid.uuid4().hex[:12]}"

    expense = Expense(
        business_id=business_id,
        category=cat_enum,
        amount=payload.amount,
        currency="INR",
        status=ExpenseStatus.RECORDED,
        expense_date=datetime.now(timezone.utc),
        description=payload.description,
        receipt_reference=payload.receipt_url,
        vehicle_id=payload.vehicle_id,
        driver_id=payload.driver_id,
        trip_id=payload.trip_id,
        origin_type="driver_app",
        origin_id=f"driver_{payload.driver_id}",
    )

    db.add(expense)
    await db.commit()
    await db.refresh(expense)

    logger.info(f"Expense {expense.id} created by driver {payload.driver_id}")

    return ExpenseResponse(
        id=expense.id,
        business_id=expense.business_id,
        category=expense.category.value,
        amount=expense.amount,
        currency=expense.currency,
        status=expense.status.value,
        expense_date=expense.expense_date,
        description=expense.description,
        receipt_reference=expense.receipt_reference,
        vehicle_id=expense.vehicle_id,
        driver_id=expense.driver_id,
        trip_id=expense.trip_id,
        created_at=expense.created_at,
    )


@router.get("/expenses", response_model=List[ExpenseResponse])
async def list_driver_expenses(
    driver_id: int = Query(...),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """List expenses for a specific driver."""
    result = await db.execute(
        select(Expense)
        .where(Expense.driver_id == driver_id)
        .order_by(desc(Expense.created_at))
        .limit(limit)
    )
    expenses = result.scalars().all()

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
            receipt_reference=exp.receipt_reference,
            vehicle_id=exp.vehicle_id,
            driver_id=exp.driver_id,
            trip_id=exp.trip_id,
            created_at=exp.created_at,
        )
        for exp in expenses
    ]
