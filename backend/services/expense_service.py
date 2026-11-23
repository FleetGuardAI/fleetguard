"""
FleetGuard — Expense Service
Domain service orchestrating business rules for Expense Management.
"""

from typing import Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from infrastructure.uow import AbstractUnitOfWork

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
        payload = event.payload or {}

        # 1. Direct Expense Domain Events
        if event.event_type == EventType.EXPENSE_ADDED:
            business_id = event.entity_id or f"EXP-{event.id}"
            await self._record_expense(business_id, payload, str(event.id), company_id=event.company_id)

        elif event.event_type == EventType.EXPENSE_APPROVED:
            business_id = event.entity_id
            await self._update_expense_status(business_id, ExpenseStatus.APPROVED, payload, str(event.id))

        elif event.event_type == EventType.EXPENSE_REJECTED:
            business_id = event.entity_id
            await self._update_expense_status(business_id, ExpenseStatus.REJECTED, payload, str(event.id))

        # 2. Linked Operational Events (Cross-domain financial ledger projections)
        elif event.event_type == EventType.FUEL_FILLED:
            await self._record_fuel_expense(event, payload)

        elif event.event_type == EventType.MAINTENANCE_COMPLETED:
            await self._record_maintenance_expense(event, payload)

    async def _record_expense(
        self,
        business_id: str,
        payload: dict,
        origin_id: str,
        company_id: Optional[int] = None,
    ) -> None:
        expense = await self.uow.repositories.expense.get_expense_by_business_id(business_id)
        if not expense:
            expense = Expense(
                business_id=business_id,
                origin_type="verified_event",
                origin_id=origin_id,
                company_id=company_id or payload.get("company_id"),
            )
            
        # Parse fields
        raw_cat = payload.get("category", ExpenseCategory.MISCELLANEOUS.value)
        try:
            expense.category = ExpenseCategory(raw_cat)
        except ValueError:
            expense.category = ExpenseCategory.MISCELLANEOUS
            
        expense.amount = float(payload.get("amount", 0.0))
        expense.currency = payload.get("currency", "INR")
        
        if "expense_date" in payload and payload["expense_date"]:
            try:
                expense.expense_date = datetime.fromisoformat(str(payload["expense_date"]))
            except (ValueError, TypeError):
                expense.expense_date = datetime.now(timezone.utc)
        else:
            expense.expense_date = datetime.now(timezone.utc)
            
        expense.description = payload.get("description")
        expense.receipt_reference = payload.get("receipt_reference") or payload.get("receipt_url")
        
        expense.vehicle_id = payload.get("vehicle_id")
        expense.driver_id = payload.get("driver_id")
        expense.trip_id = payload.get("trip_id")
        expense.maintenance_id = payload.get("maintenance_id")

        await self.uow.repositories.expense.upsert_expense(expense)

    async def _record_fuel_expense(self, event: OperationalEvent, payload: dict) -> None:
        """
        Record or update an idempotent linked expense for a FUEL_FILLED event.
        """
        amount = float(payload.get("cost_inr") or payload.get("amount") or payload.get("total_cost") or 0.0)
        business_id = f"EXP-FUEL-{event.id}"

        expense = await self.uow.repositories.expense.get_expense_by_business_id(business_id)
        if not expense:
            expense = Expense(
                business_id=business_id,
                category=ExpenseCategory.FUEL,
                amount=amount,
                currency=payload.get("currency", "INR"),
                status=ExpenseStatus.RECORDED,
                expense_date=event.occurred_at or datetime.now(timezone.utc),
                description=event.notes or f"Fuel fill {payload.get('liters', 0)}L",
                receipt_reference=payload.get("receipt_url") or payload.get("receipt_reference"),
                vehicle_id=int(event.entity_id) if str(event.entity_id).isdigit() else payload.get("vehicle_id"),
                driver_id=payload.get("driver_id"),
                trip_id=payload.get("trip_id"),
                company_id=event.company_id,
                origin_type="verified_event",
                origin_id=str(event.id),
            )
        else:
            expense.amount = amount
            if payload.get("receipt_url") or payload.get("receipt_reference"):
                expense.receipt_reference = payload.get("receipt_url") or payload.get("receipt_reference")

        await self.uow.repositories.expense.upsert_expense(expense)

    async def _record_maintenance_expense(self, event: OperationalEvent, payload: dict) -> None:
        """
        Record or update an idempotent linked expense for a MAINTENANCE_COMPLETED event.
        """
        cost = float(payload.get("cost") or payload.get("total_cost") or payload.get("amount") or 0.0)
        business_id = f"EXP-MNT-{event.id}"

        expense = await self.uow.repositories.expense.get_expense_by_business_id(business_id)
        if not expense:
            expense = Expense(
                business_id=business_id,
                category=ExpenseCategory.MAINTENANCE,
                amount=cost,
                currency=payload.get("currency", "INR"),
                status=ExpenseStatus.RECORDED,
                expense_date=event.occurred_at or datetime.now(timezone.utc),
                description=event.notes or f"Maintenance completed: {payload.get('service_type', 'Service')}",
                receipt_reference=payload.get("receipt_reference") or payload.get("receipt_url"),
                maintenance_id=int(event.entity_id) if str(event.entity_id).isdigit() else payload.get("maintenance_id"),
                vehicle_id=payload.get("vehicle_id"),
                company_id=event.company_id,
                origin_type="verified_event",
                origin_id=str(event.id),
            )
        else:
            expense.amount = cost

        await self.uow.repositories.expense.upsert_expense(expense)

    async def _update_expense_status(
        self, business_id: str, status: ExpenseStatus, payload: dict, origin_id: str
    ) -> None:
        expense = await self.uow.repositories.expense.get_expense_by_business_id(business_id)
        if not expense:
            return

        expense.status = status
        expense.origin_type = "verified_event"
        expense.origin_id = origin_id
        if "reviewed_by" in payload:
            expense.reviewed_by = payload["reviewed_by"]
            expense.reviewed_at = datetime.now(timezone.utc)
        if "rejection_reason" in payload:
            expense.rejection_reason = payload["rejection_reason"]

        await self.uow.repositories.expense.upsert_expense(expense)
