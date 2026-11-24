"""
FleetGuard — Expense Domain API Router
Provides REST APIs for the Expense Business Domain.
Includes proper approval/rejection workflow with authorization.
"""

import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from database import get_db
from models.expense_domain import ExpenseCategory, ExpenseStatus, Expense
from schemas.expense_domain import (
    ExpenseResponse, 
    ExpenseApproveRequest, 
    ExpenseRejectRequest,
    ExpenseCreateRequest,
    ExpenseUpdateRequest
)
from repositories.expense_repository import ExpenseRepository
from services.auth_service import get_current_user, requires_role
from models.user import User, UserRole

logger = logging.getLogger("fleetguard.expense_domain")

router = APIRouter(prefix="/v1", tags=["Expense Domain"])

# Roles allowed to approve/reject expenses
REVIEWER_ROLES = {UserRole.COMPANY_ADMIN, UserRole.SUPER_ADMIN, UserRole.FLEET_MANAGER, UserRole.ADMIN}


@router.get("/expenses/search", response_model=List[ExpenseResponse])
async def search_expenses(
    category: Optional[str] = Query(None, description="Filter by ExpenseCategory"),
    status: Optional[str] = Query(None, description="Filter by ExpenseStatus"),
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[ExpenseResponse]:
    """Search for expenses."""
    repo = ExpenseRepository(db)
    results = await repo.search_expenses(category=category, status=status, limit=limit, offset=offset, company_id=current_user.company_id)
    return [ExpenseResponse.model_validate(r) for r in results]


@router.get("/expenses", response_model=List[ExpenseResponse])
async def list_expenses(
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[ExpenseResponse]:
    """List all expenses."""
    repo = ExpenseRepository(db)
    results = await repo.search_expenses(limit=limit, offset=offset, company_id=current_user.company_id)
    return [ExpenseResponse.model_validate(r) for r in results]


@router.get("/expenses/{expense_id}", response_model=ExpenseResponse)
async def get_expense(
    expense_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ExpenseResponse:
    """Get a specific expense by internal ID."""
    repo = ExpenseRepository(db)
    expense = await repo.get_expense_by_id(expense_id, company_id=current_user.company_id)
    if not expense:
        raise HTTPException(404, f"Expense {expense_id} not found")
    return ExpenseResponse.model_validate(expense)


@router.get("/vehicles/{vehicle_id}/expenses", response_model=List[ExpenseResponse])
async def get_vehicle_expenses(
    vehicle_id: int,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[ExpenseResponse]:
    """Get all expenses linked to a specific vehicle."""
    repo = ExpenseRepository(db)
    results = await repo.get_expenses_by_vehicle(vehicle_id, limit, offset, company_id=current_user.company_id)
    return [ExpenseResponse.model_validate(r) for r in results]


@router.get("/drivers/{driver_id}/expenses", response_model=List[ExpenseResponse])
async def get_driver_expenses(
    driver_id: int,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[ExpenseResponse]:
    """Get all expenses linked to a specific driver."""
    repo = ExpenseRepository(db)
    results = await repo.get_expenses_by_driver(driver_id, limit, offset, company_id=current_user.company_id)
    return [ExpenseResponse.model_validate(r) for r in results]


@router.get("/trips/{trip_id}/expenses", response_model=List[ExpenseResponse])
async def get_trip_expenses(
    trip_id: int,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[ExpenseResponse]:
    """Get all expenses linked to a specific trip."""
    repo = ExpenseRepository(db)
    results = await repo.get_expenses_by_trip(trip_id, limit, offset, company_id=current_user.company_id)
    return [ExpenseResponse.model_validate(r) for r in results]


@router.get("/maintenance/{maintenance_id}/expenses", response_model=List[ExpenseResponse])
async def get_maintenance_expenses(
    maintenance_id: int,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[ExpenseResponse]:
    """Get all expenses linked to a specific maintenance record."""
    repo = ExpenseRepository(db)
    results = await repo.get_expenses_by_maintenance(maintenance_id, limit, offset, company_id=current_user.company_id)
    return [ExpenseResponse.model_validate(r) for r in results]


@router.post("/expenses", response_model=ExpenseResponse, status_code=201)
async def create_expense(
    payload: ExpenseCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ExpenseResponse:
    from models.vehicle_domain import Vehicle
    from models.driver_domain import Driver
    from models.trip_domain import Trip
    import uuid

    # FG-SEC-050: Strict validation against negative or zero expense amount
    if payload.amount <= 0:
        raise HTTPException(400, "Expense amount must be strictly greater than zero.")

    if payload.vehicle_id:
        vehicle = await db.get(Vehicle, payload.vehicle_id)
        if not vehicle or vehicle.company_id != current_user.company_id:
            raise HTTPException(400, "Invalid vehicle_id or unauthorized")
            
    if payload.driver_id:
        driver = await db.get(Driver, payload.driver_id)
        if not driver or driver.company_id != current_user.company_id:
            raise HTTPException(400, "Invalid driver_id or unauthorized")
            
    trip = None
    if payload.trip_id:
        trip = await db.get(Trip, payload.trip_id)
        if not trip or trip.company_id != current_user.company_id:
            raise HTTPException(400, "Invalid trip_id or unauthorized")

    resolved_vehicle_id = payload.vehicle_id or (trip.vehicle_id if trip else None)
    
    expense_date = payload.expense_date or datetime.now(timezone.utc)

    expense = Expense(
        business_id=f"EXP-{str(uuid.uuid4())[:8].upper()}",
        company_id=current_user.company_id,
        category=payload.category or "MISCELLANEOUS",
        amount=payload.amount,
        status="PENDING",
        expense_date=expense_date,
        description=payload.description or "",
        vehicle_id=resolved_vehicle_id,
        driver_id=payload.driver_id,
        trip_id=payload.trip_id,
        origin_type="rest_api",
        origin_id="manual"
    )
    db.add(expense)
    await db.commit()
    await db.refresh(expense)
    return ExpenseResponse.model_validate(expense)


@router.patch("/expenses/{expense_id}", response_model=ExpenseResponse)
async def update_expense(
    expense_id: int,
    payload: ExpenseUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ExpenseResponse:
    """Update non-status expense fields. For approval/rejection, use the dedicated endpoints."""
    expense = await db.get(Expense, expense_id)
    if not expense or expense.company_id != current_user.company_id:
        raise HTTPException(404, f"Expense {expense_id} not found")

    # Financial Immutability
    if expense.status in [ExpenseStatus.APPROVED, ExpenseStatus.REJECTED]:
        raise HTTPException(
            400,
            f"Cannot modify an expense with status '{expense.status.value}'. Only PENDING or RECORDED expenses can be edited."
        )

    if payload.description is not None:
        expense.description = payload.description
    if payload.amount is not None:
        # FG-SEC-050: Strict validation against negative or zero updated amount
        if payload.amount <= 0:
            raise HTTPException(400, "Expense amount must be strictly greater than zero.")
        expense.amount = payload.amount
    if payload.category is not None:
        try:
            expense.category = ExpenseCategory(payload.category)
        except ValueError:
            pass

    await db.commit()
    await db.refresh(expense)
    return ExpenseResponse.model_validate(expense)


@router.post("/expenses/{expense_id}/approve", response_model=ExpenseResponse)
async def approve_expense(
    expense_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(requires_role(UserRole.COMPANY_ADMIN, UserRole.FLEET_MANAGER, UserRole.ADMIN))
) -> ExpenseResponse:
    """
    Approve a pending expense claim.
    Only COMPANY_ADMIN, SUPER_ADMIN, FLEET_MANAGER, or ADMIN roles can approve.
    """
    # Authorization check
    if current_user.role not in REVIEWER_ROLES:
        raise HTTPException(403, "You do not have permission to approve expenses")

    expense = await db.get(Expense, expense_id)
    if not expense or expense.company_id != current_user.company_id:
        raise HTTPException(404, f"Expense {expense_id} not found")

    # State validation — only PENDING expenses can be approved
    if expense.status != ExpenseStatus.PENDING:
        raise HTTPException(
            400,
            f"Cannot approve expense with status '{expense.status.value}'. Only PENDING expenses can be approved."
        )

    expense.status = ExpenseStatus.APPROVED
    expense.reviewed_by = str(current_user.id)
    expense.reviewed_at = datetime.now(timezone.utc)
    expense.rejection_reason = None  # Clear any previous rejection reason

    await db.commit()
    await db.refresh(expense)

    logger.info(f"Expense {expense_id} approved by user {current_user.id}")
    return ExpenseResponse.model_validate(expense)


@router.post("/expenses/{expense_id}/reject", response_model=ExpenseResponse)
async def reject_expense(
    expense_id: int,
    payload: ExpenseRejectRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(requires_role(UserRole.COMPANY_ADMIN, UserRole.FLEET_MANAGER, UserRole.ADMIN))
) -> ExpenseResponse:
    """
    Reject a pending expense claim.
    Only COMPANY_ADMIN, SUPER_ADMIN, FLEET_MANAGER, or ADMIN roles can reject.
    A rejection reason is required.
    """
    # Authorization check
    if current_user.role not in REVIEWER_ROLES:
        raise HTTPException(403, "You do not have permission to reject expenses")

    expense = await db.get(Expense, expense_id)
    if not expense or expense.company_id != current_user.company_id:
        raise HTTPException(404, f"Expense {expense_id} not found")

    # State validation — only PENDING expenses can be rejected
    if expense.status != ExpenseStatus.PENDING:
        raise HTTPException(
            400,
            f"Cannot reject expense with status '{expense.status.value}'. Only PENDING expenses can be rejected."
        )

    expense.status = ExpenseStatus.REJECTED
    expense.reviewed_by = str(current_user.id)
    expense.reviewed_at = datetime.now(timezone.utc)
    expense.rejection_reason = payload.rejection_reason

    await db.commit()
    await db.refresh(expense)

    logger.info(f"Expense {expense_id} rejected by user {current_user.id}: {payload.rejection_reason}")
    return ExpenseResponse.model_validate(expense)
