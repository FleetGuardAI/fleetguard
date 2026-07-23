"""
FleetGuard — Fuel Repository
Handles database operations for the Fuel Domain.
"""

from typing import Optional, Sequence
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from models.fuel_domain import FuelState, FuelTransaction


class FuelRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_transaction(self, transaction: FuelTransaction) -> FuelTransaction:
        self.db.add(transaction)
        await self.db.flush()
        await self.db.refresh(transaction)
        return transaction

    async def get_transaction_by_id(self, transaction_id: int) -> Optional[FuelTransaction]:
        return await self.db.get(FuelTransaction, transaction_id)

    async def get_fuel_transactions_by_truck(self, truck_id: int, limit: int = 100) -> Sequence[FuelTransaction]:
        stmt = (
            select(FuelTransaction)
            .where(FuelTransaction.truck_id == truck_id)
            .order_by(FuelTransaction.timestamp.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_fuel_state_by_truck(self, truck_id: int) -> Optional[FuelState]:
        stmt = select(FuelState).where(FuelState.truck_id == truck_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert_fuel_state(self, state: FuelState) -> FuelState:
        """
        Inserts or updates the fuel state for a truck.
        Since we might have race conditions, this is a basic upsert approach.
        In a high-concurrency environment, we might want to use PostgreSQL's ON CONFLICT DO UPDATE.
        For now, we query and update.
        """
        existing = await self.get_fuel_state_by_truck(state.truck_id)
        if existing:
            existing.current_level = state.current_level
            existing.origin_type = state.origin_type
            existing.origin_id = state.origin_id
            await self.db.flush()
            return existing
        else:
            self.db.add(state)
            await self.db.flush()
            await self.db.refresh(state)
            return state
