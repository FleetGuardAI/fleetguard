"""
FleetGuard — Fuel State Service
Domain service orchestrating business rules purely for Fuel State Management.
"""

from typing import Optional, Sequence
from fastapi import HTTPException

from infrastructure.uow import AbstractUnitOfWork
from models.fuel_domain import FuelState, FuelTransaction, FuelTransactionType, FuelStateReliability, FuelSource
from schemas.fuel_domain import FuelFill


class FuelStateService:
    """
    Coordinates Fuel State business rules.
    This service is entirely decoupled from external inputs like Kafka; it is called by the
    processing pipeline after a verified event has successfully passed validation rules.
    """

    def __init__(self, uow: AbstractUnitOfWork):
        self.uow = uow

    async def apply_verified_fuel_fill(self, fill: FuelFill, origin_event_id: str) -> None:
        """
        Applies a verified fuel fill to the business state.
        This assumes upstream validation (like tank capacity limits) has already been
        handled by the Validation Engine via the ValidationContextFactory.
        """
        
        # 1. Update State
        state = await self.uow.repositories.fuel_state.get_fuel_state_by_vehicle(fill.vehicle_id)
        current_level = state.current_level if state else 0.0
        new_level = current_level + fill.amount_liters

        new_state = FuelState(
            vehicle_id=fill.vehicle_id,
            current_level=new_level,
            source=FuelSource.SENSOR, # Or provided by the fill/event in a real scenario
            reliability=FuelStateReliability.HIGH,
            last_operational_event_id=origin_event_id
        )
        await self.uow.repositories.fuel_state.upsert_fuel_state(new_state)

        # 2. Record Transaction
        tx = FuelTransaction(
            vehicle_id=fill.vehicle_id,
            transaction_type=FuelTransactionType.FILL,
            amount_liters=fill.amount_liters,
            origin_type="verified_event",
            origin_id=origin_event_id,
            timestamp=fill.timestamp,
            description=fill.description
        )
        await self.uow.repositories.fuel_state.create_transaction(tx)

    async def get_fuel_history(self, vehicle_id: int) -> Sequence[FuelTransaction]:
        """Fetch history of fuel transactions for a vehicle."""
        return await self.uow.repositories.fuel_state.get_fuel_transactions_by_vehicle(vehicle_id)

    async def get_fuel_state(self, vehicle_id: int) -> Optional[FuelState]:
        """Fetch the current fuel state for a vehicle."""
        return await self.uow.repositories.fuel_state.get_fuel_state_by_vehicle(vehicle_id)
