"""
FleetGuard — Fuel Service
Domain service orchestrating business rules for Fuel Management.
"""

from typing import Optional, Sequence
from fastapi import HTTPException
from infrastructure.uow import AbstractUnitOfWork

from models.operational_event import OperationalEvent, EventType, EntityType
from schemas.fuel_domain import FuelFill
from services.fuel_state_service import FuelStateService


class FuelService:
    """
    Coordinates Fuel Domain business rules.
    Acts as the entry point from the Processing Engine to the Fuel Domain.
    Delegates state management to the FuelStateService.
    """

    def __init__(self, uow: AbstractUnitOfWork):
        self.uow = uow
        self.fuel_state_service = FuelStateService(uow)

    async def apply_verified_event(self, event: OperationalEvent) -> None:
        """
        Single entry point for the Fuel Domain from the Processing Engine.
        Reads a verified OperationalEvent, maps it to internal domain concepts,
        and delegates to specialized internal services.
        """
        if event.entity_type != EntityType.VEHICLE:
            return  # The fuel domain only cares about Vehicle entities

        vehicle_id = int(event.entity_id)

        # Ensure vehicle exists
        vehicle = await self.uow.repositories.vehicle.get_vehicle_by_id(vehicle_id)
        if not vehicle:
            raise HTTPException(404, f"Vehicle {vehicle_id} not found")

        # Route by event type
        if event.event_type == EventType.FUEL_FILLED:
            payload = event.payload or {}
            
            fill_cmd = FuelFill(
                vehicle_id=vehicle_id,
                amount_liters=float(payload.get("liters", 0.0)),
                timestamp=event.occurred_at,
                description=event.notes or "Fuel fill from verified event"
            )
            await self.fuel_state_service.apply_verified_fuel_fill(fill_cmd, origin_event_id=str(event.id))
            
        elif event.event_type == EventType.FUEL_ALERT_TRIGGERED:
            # Future expansion
            pass
