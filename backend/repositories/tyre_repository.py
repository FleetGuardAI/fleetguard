"""
FleetGuard — Tyre Repository
Handles database operations for the Tyre Domain.
"""

from typing import Optional, Sequence, Dict, Any
from datetime import datetime, timezone
from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.tyre_domain import Tyre, TyreLifecycleRecord, TyreStatus, LifecycleEventCategory
from models.expense_domain import Expense, ExpenseCategory, ExpenseStatus


class TyreRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_tyre_by_id(self, tyre_id: int) -> Optional[Tyre]:
        return await self.db.get(Tyre, tyre_id)

    async def get_tyre_by_id_and_company(self, tyre_id: int, company_id: int) -> Optional[Tyre]:
        stmt = select(Tyre).where(Tyre.id == tyre_id, Tyre.company_id == company_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_tyre_by_serial_number(self, serial_number: str) -> Optional[Tyre]:
        stmt = select(Tyre).where(Tyre.serial_number == serial_number)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_tyre_by_serial_number_for_update(self, serial_number: str) -> Optional[Tyre]:
        """
        Fetches tyre with row-level locking (FOR UPDATE) to prevent concurrency races.
        In SQLite test environments, with_for_update is safely ignored.
        """
        stmt = select(Tyre).where(Tyre.serial_number == serial_number).with_for_update()
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_tyre_at_position(self, vehicle_id: int, position: str) -> Optional[Tyre]:
        """
        Checks if a tyre is already mounted at this specific wheel position on this vehicle.
        """
        stmt = select(Tyre).where(
            Tyre.current_vehicle_id == vehicle_id,
            Tyre.current_position == position,
            Tyre.current_status == TyreStatus.INSTALLED
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_tyres_by_vehicle(self, vehicle_id: int, limit: int = 50, offset: int = 0) -> Sequence[Tyre]:
        stmt = select(Tyre).where(Tyre.current_vehicle_id == vehicle_id).order_by(Tyre.id.desc()).offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def search_tyres(
        self, 
        status: Optional[TyreStatus] = None, 
        limit: int = 50, 
        offset: int = 0
    ) -> Sequence[Tyre]:
        query = select(Tyre)
        if status is not None:
            query = query.where(Tyre.current_status == status)
        query = query.order_by(Tyre.id.desc()).offset(offset).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def search_tyres_by_company(
        self,
        company_id: int,
        status: Optional[TyreStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Sequence[Tyre]:
        query = select(Tyre).where(Tyre.company_id == company_id)
        if status is not None:
            query = query.where(Tyre.current_status == status)
        query = query.order_by(Tyre.id.desc()).offset(offset).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def count_by_status_for_company(self, company_id: int) -> Dict[str, int]:
        stmt = (
            select(Tyre.current_status, func.count(Tyre.id))
            .where(Tyre.company_id == company_id)
            .group_by(Tyre.current_status)
        )
        result = await self.db.execute(stmt)
        counts = {s.value: 0 for s in TyreStatus}
        for status_val, count in result.all():
            status_str = status_val.value if isinstance(status_val, TyreStatus) else str(status_val)
            counts[status_str] = count
        return counts

    async def upsert_tyre(self, tyre: Tyre) -> Tyre:
        self.db.add(tyre)
        await self.db.flush()
        await self.db.refresh(tyre)
        return tyre
        
    async def add_lifecycle_record(self, record: TyreLifecycleRecord) -> TyreLifecycleRecord:
        self.db.add(record)
        await self.db.flush()
        await self.db.refresh(record)
        return record

    async def get_lifecycle_record_by_origin(
        self, 
        tyre_id: int, 
        origin_id: str, 
        event_category: Optional[LifecycleEventCategory] = None
    ) -> Optional[TyreLifecycleRecord]:
        query = select(TyreLifecycleRecord).where(
            TyreLifecycleRecord.tyre_id == tyre_id,
            TyreLifecycleRecord.origin_id == origin_id
        )
        if event_category is not None:
            query = query.where(TyreLifecycleRecord.event_category == event_category)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_inventory_valuation_by_company(self, company_id: int) -> Dict[str, Any]:
        """
        Aggregates inventory valuation metrics partitioned by lifecycle state for a tenant.
        Does not fabricate costs for unknown-cost tyres; counts them transparently.
        Also computes retread and repair expenditures separately from the Expense ledger.
        """
        # 1. State-level Tyre Aggregation
        stmt = (
            select(
                Tyre.current_status,
                func.count(Tyre.id).label("total_count"),
                func.count(Tyre.purchase_cost).label("known_cost_count"),
                func.coalesce(func.sum(Tyre.purchase_cost), 0.0).label("total_acquisition_value")
            )
            .where(Tyre.company_id == company_id)
            .group_by(Tyre.current_status)
        )
        result = await self.db.execute(stmt)
        
        # Initialize default partitions for all states
        by_state = {}
        for s in TyreStatus:
            by_state[s.value] = {
                "state": s,
                "total_count": 0,
                "known_cost_count": 0,
                "unknown_cost_count": 0,
                "total_acquisition_value": 0.0,
                "coverage_pct": 100.0
            }

        total_owned_tyres = 0
        total_owned_val = 0.0
        total_known_count = 0
        total_unknown_count = 0

        active_tyres = 0
        active_val = 0.0
        active_known_count = 0
        active_unknown_count = 0

        for row in result.all():
            st = row.current_status
            st_key = st.value if isinstance(st, TyreStatus) else str(st)
            tot = int(row.total_count)
            known = int(row.known_cost_count)
            unknown = tot - known
            val = float(round(row.total_acquisition_value, 2))
            cov = float(round((known / tot * 100.0), 2)) if tot > 0 else 100.0

            by_state[st_key] = {
                "state": st if isinstance(st, TyreStatus) else TyreStatus(st_key),
                "total_count": tot,
                "known_cost_count": known,
                "unknown_cost_count": unknown,
                "total_acquisition_value": val,
                "coverage_pct": cov
            }

            total_owned_tyres += tot
            total_owned_val += val
            total_known_count += known
            total_unknown_count += unknown

            if st_key != TyreStatus.RETIRED.value:
                active_tyres += tot
                active_val += val
                active_known_count += known
                active_unknown_count += unknown

        total_coverage_pct = (
            float(round((total_known_count / total_owned_tyres * 100.0), 2))
            if total_owned_tyres > 0 else 100.0
        )
        active_coverage_pct = (
            float(round((active_known_count / active_tyres * 100.0), 2))
            if active_tyres > 0 else 100.0
        )

        # 2. Separately query recognized Retread & Repair expenses for this company
        stmt_expenses = (
            select(
                func.coalesce(
                    func.sum(
                        case((Expense.business_id.like("EXP-TYRE-RETREAD-%"), Expense.amount), else_=0.0)
                    ), 0.0
                ).label("retread_total"),
                func.coalesce(
                    func.sum(
                        case((Expense.business_id.like("EXP-TYRE-REPAIR-%"), Expense.amount), else_=0.0)
                    ), 0.0
                ).label("repair_total")
            )
            .where(
                Expense.company_id == company_id,
                Expense.category == ExpenseCategory.TYRE,
                Expense.status != ExpenseStatus.REJECTED,
                Expense.status != ExpenseStatus.CANCELLED
            )
        )
        exp_res = await self.db.execute(stmt_expenses)
        exp_row = exp_res.first()
        retread_exp = float(round(exp_row.retread_total, 2)) if exp_row else 0.0
        repair_exp = float(round(exp_row.repair_total, 2)) if exp_row else 0.0

        return {
            "as_of": datetime.now(timezone.utc),
            "currency": "INR",
            "valuation_method": "KNOWN_ACQUISITION_COST",
            "total_active_tyres": active_tyres,
            "total_active_acquisition_value": round(active_val, 2),
            "active_known_cost_count": active_known_count,
            "active_unknown_cost_count": active_unknown_count,
            "active_coverage_pct": active_coverage_pct,
            "total_owned_tyres": total_owned_tyres,
            "total_owned_acquisition_value": round(total_owned_val, 2),
            "total_known_cost_count": total_known_count,
            "total_unknown_cost_count": total_unknown_count,
            "total_coverage_pct": total_coverage_pct,
            "by_lifecycle_state": by_state,
            "total_retread_expenditure": retread_exp,
            "total_repair_expenditure": repair_exp
        }



