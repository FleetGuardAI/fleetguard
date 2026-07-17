"""
FleetGuard — Fuel Service
Domain service orchestrating business rules for Fuel Management.
"""

from typing import Optional, Sequence
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from infrastructure.uow import AbstractUnitOfWork

from models.operational_event import OperationalEvent, EventType, EntityType
from models.fuel_domain import FuelState, FuelTransaction, FuelTransactionType
from models.vehicle_domain import Vehicle
from repositories.fuel_repository import FuelRepository
from schemas.fuel_domain import FuelFill, FuelAdjustment


class FuelService:
    """
    Coordinates Fuel Domain business rules.
    This service is entirely decoupled from external inputs; it receives Canonical Events 
    or handles read-only queries from the API.
    """

    def __init__(self, uow: AbstractUnitOfWork):
        self.uow = uow

    async def apply_verified_event(self, event: OperationalEvent) -> None:
        """
        Single entry point for state mutation in the Fuel Domain.
        Reads a verified OperationalEvent, maps it to internal domain concepts,
        and applies the business rules.
        """
        if event.entity_type != EntityType.VEHICLE:
            return  # The fuel domain only cares about Vehicle entities

        truck_id = int(event.entity_id)

        # Ensure truck exists
        truck = await self.uow.repositories.vehicle.get_vehicle_by_id(truck_id)
        if not truck:
            raise HTTPException(404, f"Truck {truck_id} not found")

        # Route by event type
        if event.event_type == EventType.FUEL_FILLED:
            # Note: The payload schema mapping expects "liters" for amount, etc.
            # (Validations are guaranteed by the validation engine upstream).
            payload = event.payload or {}
            
            fill_cmd = FuelFill(
                truck_id=truck_id,
                amount_liters=float(payload.get("liters", 0.0)),
                timestamp=event.occurred_at,
                description=event.notes or "Fuel fill from verified event"
            )
            await self._record_fuel_fill(fill_cmd, origin_id=str(event.id))
            
        elif event.event_type == EventType.FUEL_ALERT_TRIGGERED:
            # We don't have a specific requirement to process FUEL_ALERT_TRIGGERED as an adjustment yet,
            # but if it was mapped to a manual adjustment, it would go here.
            pass
            
        # Ignore other events (TRIP_STARTED, etc.)

    async def _record_fuel_fill(self, fill: FuelFill, origin_id: str) -> None:
        """Internal business rule execution for a Fuel Fill."""
        
        # 1. Update State
        state = await self.uow.repositories.fuel.get_fuel_state_by_truck(fill.truck_id)
        current_level = state.current_level if state else 0.0
        new_level = current_level + fill.amount_liters

        new_state = FuelState(
            truck_id=fill.truck_id,
            current_level=new_level,
            origin_type="verified_event",
            origin_id=origin_id
        )
        await self.uow.repositories.fuel.upsert_fuel_state(new_state)

        # 2. Record Transaction
        tx = FuelTransaction(
            truck_id=fill.truck_id,
            transaction_type=FuelTransactionType.FILL,
            amount_liters=fill.amount_liters,
            origin_type="verified_event",
            origin_id=origin_id,
            timestamp=fill.timestamp,
            description=fill.description
        )
        await self.uow.repositories.fuel.create_transaction(tx)

    async def get_fuel_history(self, truck_id: int) -> Sequence[FuelTransaction]:
        """Fetch history of fuel transactions for a truck."""
        return await self.uow.repositories.fuel.get_fuel_transactions_by_truck(truck_id)

    async def get_fuel_state(self, truck_id: int) -> Optional[FuelState]:
        """Fetch the current fuel state for a truck."""
        return await self.uow.repositories.fuel.get_fuel_state_by_truck(truck_id)
