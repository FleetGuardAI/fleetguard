"""
FleetGuard — Expense Domain API Router
Provides Read-Only REST APIs for the Expense Business Domain.
(Write operations are processed asynchronously via Operational Events).
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from database import get_db
from models.expense_domain import ExpenseCategory, ExpenseStatus
from repositories.expense_repository import ExpenseRepository
from schemas.expense_domain import ExpenseResponse

router = APIRouter(prefix="/v1", tags=["Expense Domain"])


@router.get("/expenses/search", response_model=List[ExpenseResponse])
async def search_expenses(
    category: Optional[str] = Query(None, description="Filter by ExpenseCategory"),
    status: Optional[str] = Query(None, description="Filter by ExpenseStatus"),
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
) -> List[ExpenseResponse]:
    """Search for expenses."""
    repo = ExpenseRepository(db)
    results = await repo.search_expenses(category=category, status=status, limit=limit, offset=offset)
    return [ExpenseResponse.model_validate(r) for r in results]


@router.get("/expenses", response_model=List[ExpenseResponse])
async def list_expenses(
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
) -> List[ExpenseResponse]:
    """List all expenses."""
    repo = ExpenseRepository(db)
    results = await repo.search_expenses(limit=limit, offset=offset)
    return [ExpenseResponse.model_validate(r) for r in results]


@router.get("/expenses/{expense_id}", response_model=ExpenseResponse)
async def get_expense(
    expense_id: int,
    db: AsyncSession = Depends(get_db)
) -> ExpenseResponse:
    """Get a specific expense by internal ID."""
    repo = ExpenseRepository(db)
    expense = await repo.get_expense_by_id(expense_id)
    if not expense:
        raise HTTPException(404, f"Expense {expense_id} not found")
    return ExpenseResponse.model_validate(expense)


@router.get("/vehicles/{vehicle_id}/expenses", response_model=List[ExpenseResponse])
async def get_vehicle_expenses(
    vehicle_id: int,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
) -> List[ExpenseResponse]:
    """Get all expenses linked to a specific vehicle."""
    repo = ExpenseRepository(db)
    results = await repo.get_expenses_by_vehicle(vehicle_id, limit, offset)
    return [ExpenseResponse.model_validate(r) for r in results]


@router.get("/drivers/{driver_id}/expenses", response_model=List[ExpenseResponse])
async def get_driver_expenses(
    driver_id: int,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
) -> List[ExpenseResponse]:
    """Get all expenses linked to a specific driver."""
    repo = ExpenseRepository(db)
    results = await repo.get_expenses_by_driver(driver_id, limit, offset)
    return [ExpenseResponse.model_validate(r) for r in results]


@router.get("/trips/{trip_id}/expenses", response_model=List[ExpenseResponse])
async def get_trip_expenses(
    trip_id: int,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
) -> List[ExpenseResponse]:
    """Get all expenses linked to a specific trip."""
    repo = ExpenseRepository(db)
    results = await repo.get_expenses_by_trip(trip_id, limit, offset)
    return [ExpenseResponse.model_validate(r) for r in results]


@router.get("/maintenance/{maintenance_id}/expenses", response_model=List[ExpenseResponse])
async def get_maintenance_expenses(
    maintenance_id: int,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
) -> List[ExpenseResponse]:
    """Get all expenses linked to a specific maintenance record."""
    repo = ExpenseRepository(db)
    results = await repo.get_expenses_by_maintenance(maintenance_id, limit, offset)
    return [ExpenseResponse.model_validate(r) for r in results]
