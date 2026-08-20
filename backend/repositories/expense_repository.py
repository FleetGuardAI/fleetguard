"""
FleetGuard — Expense Repository
Data access layer for the Expense Domain.
"""

from typing import Optional, Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.expense_domain import Expense, ExpenseStatus


class ExpenseRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_expense_by_id(self, expense_id: int, company_id: Optional[int] = None) -> Optional[Expense]:
        stmt = select(Expense).where(Expense.id == expense_id)
        if company_id is not None:
            stmt = stmt.where(Expense.company_id == company_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_expense_by_business_id(self, business_id: str) -> Optional[Expense]:
        stmt = select(Expense).where(Expense.business_id == business_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_expenses_by_vehicle(self, vehicle_id: int, limit: int = 100, offset: int = 0, company_id: Optional[int] = None) -> Sequence[Expense]:
        stmt = select(Expense).where(Expense.vehicle_id == vehicle_id)
        if company_id is not None:
            stmt = stmt.where(Expense.company_id == company_id)
        stmt = stmt.order_by(Expense.created_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_expenses_by_driver(self, driver_id: int, limit: int = 100, offset: int = 0, company_id: Optional[int] = None) -> Sequence[Expense]:
        stmt = select(Expense).where(Expense.driver_id == driver_id)
        if company_id is not None:
            stmt = stmt.where(Expense.company_id == company_id)
        stmt = stmt.order_by(Expense.created_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_expenses_by_trip(self, trip_id: int, limit: int = 100, offset: int = 0, company_id: Optional[int] = None) -> Sequence[Expense]:
        stmt = select(Expense).where(Expense.trip_id == trip_id)
        if company_id is not None:
            stmt = stmt.where(Expense.company_id == company_id)
        stmt = stmt.order_by(Expense.created_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_expenses_by_maintenance(self, maintenance_id: int, limit: int = 100, offset: int = 0, company_id: Optional[int] = None) -> Sequence[Expense]:
        stmt = select(Expense).where(Expense.maintenance_id == maintenance_id)
        if company_id is not None:
            stmt = stmt.where(Expense.company_id == company_id)
        stmt = stmt.order_by(Expense.created_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def search_expenses(
        self,
        category: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        company_id: Optional[int] = None
    ) -> Sequence[Expense]:
        stmt = select(Expense)
        if category:
            stmt = stmt.where(Expense.category == category)
        if status:
            stmt = stmt.where(Expense.status == status)
        if company_id is not None:
            stmt = stmt.where(Expense.company_id == company_id)
            
        stmt = stmt.order_by(Expense.created_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def upsert_expense(self, expense: Expense) -> Expense:
        """Create or update an expense."""
        if not expense.id:
            self.db.add(expense)
        await self.db.flush()
        await self.db.refresh(expense)
        return expense
