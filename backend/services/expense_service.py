"""
FleetGuard — Expense Service
Domain service orchestrating business rules for Expense Management.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from infrastructure.uow import AbstractUnitOfWork
from datetime import datetime

from models.operational_event import OperationalEvent, EventType, EntityType
from models.expense_domain import Expense, ExpenseCategory, ExpenseStatus
from repositories.expense_repository import ExpenseRepository


class ExpenseService:
    """
    Coordinates Expense Domain business rules.
    Receives Canonical Events and updates the Expense ledger.
    """

    def __init__(self, uow: AbstractUnitOfWork):
        self.uow = uow

    async def apply_verified_event(self, event: OperationalEvent) -> None:
        """
        Single entry point for state mutation in the Expense Domain.
        Reads a verified OperationalEvent and applies business rules.
        """
        if event.entity_type != EntityType.EXPENSE:
            return

        payload = event.payload or {}
        business_id = event.entity_id

        if event.event_type == EventType.EXPENSE_RECORDED:
            await self._record_expense(business_id, payload, str(event.id))
        elif event.event_type == EventType.EXPENSE_UPDATED:
            await self._update_expense(business_id, payload, str(event.id))
        elif event.event_type == EventType.EXPENSE_CANCELLED:
            await self._cancel_expense(business_id, payload, str(event.id))

    async def _record_expense(self, business_id: str, payload: dict, origin_id: str) -> None:
        expense = await self.uow.repositories.expense.get_expense_by_business_id(business_id)
        if not expense:
            expense = Expense(
                business_id=business_id,
                origin_type="verified_event",
                origin_id=origin_id
            )
            
        # Parse fields
        try:
            expense.category = ExpenseCategory(payload.get("category", ExpenseCategory.MISCELLANEOUS))
        except ValueError:
            expense.category = ExpenseCategory.MISCELLANEOUS
            
        expense.amount = float(payload.get("amount", 0.0))
        expense.currency = payload.get("currency", "INR")
        
        if "expense_date" in payload:
            try:
                expense.expense_date = datetime.fromisoformat(payload["expense_date"])
            except (ValueError, TypeError):
                expense.expense_date = datetime.utcnow()
        else:
            expense.expense_date = datetime.utcnow()
            
        expense.description = payload.get("description")
        expense.receipt_reference = payload.get("receipt_reference")
        
        expense.vehicle_id = payload.get("vehicle_id")
        expense.driver_id = payload.get("driver_id")
        expense.trip_id = payload.get("trip_id")
        expense.maintenance_id = payload.get("maintenance_id")

        await self.uow.repositories.expense.upsert_expense(expense)

    async def _update_expense(self, business_id: str, payload: dict, origin_id: str) -> None:
        expense = await self.uow.repositories.expense.get_expense_by_business_id(business_id)
        if not expense:
            return

        expense.origin_type = "verified_event"
        expense.origin_id = origin_id

        if "amount" in payload:
            expense.amount = float(payload["amount"])
        if "category" in payload:
            try:
                expense.category = ExpenseCategory(payload["category"])
            except ValueError:
                pass
        if "description" in payload:
            expense.description = payload["description"]
        if "receipt_reference" in payload:
            expense.receipt_reference = payload["receipt_reference"]

        await self.uow.repositories.expense.upsert_expense(expense)

    async def _cancel_expense(self, business_id: str, payload: dict, origin_id: str) -> None:
        expense = await self.uow.repositories.expense.get_expense_by_business_id(business_id)
        if not expense:
            return

        expense.status = ExpenseStatus.CANCELLED
        expense.origin_type = "verified_event"
        expense.origin_id = origin_id

        await self.uow.repositories.expense.upsert_expense(expense)
