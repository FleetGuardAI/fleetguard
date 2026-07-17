"""
FleetGuard — Vehicle Service
Domain service orchestrating business rules for Vehicle Management.
"""

from typing import Optional, Sequence
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from infrastructure.uow import AbstractUnitOfWork

from models.operational_event import OperationalEvent, EventType, EntityType
from models.vehicle_domain import Vehicle, VehicleStatus
from repositories.vehicle_repository import VehicleRepository


class VehicleService:
    """
    Coordinates Vehicle Domain business rules.
    Receives Canonical Events or handles read-only queries from the API.
    """

    def __init__(self, uow: AbstractUnitOfWork):
        self.uow = uow

    async def apply_verified_event(self, event: OperationalEvent) -> None:
        """
        Single entry point for state mutation in the Vehicle Domain.
        Reads a verified OperationalEvent and applies business rules.
        """
        if event.entity_type != EntityType.VEHICLE:
            return  # The vehicle domain only cares about Vehicle entities

        payload = event.payload or {}
        
        # Determine registration number from entity_id or payload
        registration_number = payload.get("registration_number", event.entity_id)

        # Route by event type
        if event.event_type == EventType.VEHICLE_ASSIGNED:
            # VEHICLE_ASSIGNED acts as registration/creation for this epic
            await self._record_vehicle_registered(
                registration_number=registration_number,
                payload=payload,
                origin_id=str(event.id)
            )

        elif event.event_type == EventType.VEHICLE_UPDATED:
            await self._record_vehicle_updated(
                registration_number=registration_number,
                payload=payload,
                origin_id=str(event.id)
            )
            
        elif event.event_type == EventType.VEHICLE_STATUS_CHANGED:
            await self._record_vehicle_status_changed(
                registration_number=registration_number,
                payload=payload,
                origin_id=str(event.id)
            )

    async def _record_vehicle_registered(self, registration_number: str, payload: dict, origin_id: str) -> None:
        vehicle = await self.uow.repositories.vehicle.get_vehicle_by_registration(registration_number)
        if vehicle:
            # If already exists, we might just update it or skip
            pass
        else:
            vehicle = Vehicle(
                registration_number=registration_number,
                make=payload.get("make", "Unknown"),
                model=payload.get("model"),
                year=payload.get("year"),
                tank_capacity=payload.get("tank_capacity", 400.0),
                vin=payload.get("vin"),
                engine_number=payload.get("engine_number"),
                ownership_info=payload.get("ownership_info"),
                status=VehicleStatus.ACTIVE,
                origin_type="verified_event",
                origin_id=origin_id
            )
        await self.uow.repositories.vehicle.upsert_vehicle(vehicle)
        
    async def _record_vehicle_updated(self, registration_number: str, payload: dict, origin_id: str) -> None:
        vehicle = await self.uow.repositories.vehicle.get_vehicle_by_registration(registration_number)
        if not vehicle:
            return # Cannot update a vehicle that doesn't exist

        if "make" in payload:
            vehicle.make = payload["make"]
        if "model" in payload:
            vehicle.model = payload["model"]
        if "year" in payload:
            vehicle.year = payload["year"]
        if "tank_capacity" in payload:
            vehicle.tank_capacity = payload["tank_capacity"]
        if "vin" in payload:
            vehicle.vin = payload["vin"]
        if "engine_number" in payload:
            vehicle.engine_number = payload["engine_number"]
        if "ownership_info" in payload:
            vehicle.ownership_info = payload["ownership_info"]
            
        vehicle.origin_type = "verified_event"
        vehicle.origin_id = origin_id
        
        await self.uow.repositories.vehicle.upsert_vehicle(vehicle)

    async def _record_vehicle_status_changed(self, registration_number: str, payload: dict, origin_id: str) -> None:
        vehicle = await self.uow.repositories.vehicle.get_vehicle_by_registration(registration_number)
        if not vehicle:
            return
            
        new_status = payload.get("status")
        if new_status:
            try:
                vehicle.status = VehicleStatus(new_status)
                vehicle.origin_type = "verified_event"
                vehicle.origin_id = origin_id
                await self.uow.repositories.vehicle.upsert_vehicle(vehicle)
            except ValueError:
                pass # Invalid status enum

    # --- Read APIs ---

    async def get_vehicle(self, vehicle_id: int) -> Optional[Vehicle]:
        return await self.uow.repositories.vehicle.get_vehicle_by_id(vehicle_id)

    async def search_vehicles(
        self, 
        is_active: Optional[bool] = None, 
        limit: int = 50, 
        offset: int = 0
    ) -> Sequence[Vehicle]:
        return await self.uow.repositories.vehicle.search_vehicles(is_active=is_active, limit=limit, offset=offset)
