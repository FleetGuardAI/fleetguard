"""
FleetGuard — Driver Service
Domain service orchestrating business rules for Driver Management.
"""

from typing import Optional, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from infrastructure.uow import AbstractUnitOfWork
from datetime import date

from models.operational_event import OperationalEvent, EventType, EntityType
from models.driver_domain import Driver, DriverStatus, EmploymentStatus
from repositories.driver_repository import DriverRepository


class DriverService:
    """
    Coordinates Driver Domain business rules.
    Receives Canonical Events or handles read-only queries from the API.
    """

    def __init__(self, uow: AbstractUnitOfWork):
        self.uow = uow

    async def apply_verified_event(self, event: OperationalEvent) -> None:
        """
        Single entry point for state mutation in the Driver Domain.
        Reads a verified OperationalEvent and applies business rules.
        """
        if event.entity_type != EntityType.DRIVER:
            return  # The driver domain only cares about Driver entities

        payload = event.payload or {}
        
        # Phone number is primarily used as the driver's unique business identifier
        phone_number = payload.get("phone_number", event.entity_id)

        # Route by event type
        if event.event_type == EventType.DRIVER_REGISTERED:
            await self._record_driver_registered(
                phone_number=phone_number,
                payload=payload,
                origin_id=str(event.id)
            )

        elif event.event_type == EventType.DRIVER_UPDATED:
            await self._record_driver_updated(
                phone_number=phone_number,
                payload=payload,
                origin_id=str(event.id)
            )
            
        elif event.event_type == EventType.DRIVER_STATUS_CHANGED:
            await self._record_driver_status_changed(
                phone_number=phone_number,
                payload=payload,
                origin_id=str(event.id)
            )

        elif event.event_type == EventType.DRIVER_LICENSE_UPDATED:
            await self._record_driver_license_updated(
                phone_number=phone_number,
                payload=payload,
                origin_id=str(event.id)
            )


    async def _record_driver_registered(self, phone_number: str, payload: dict, origin_id: str) -> None:
        driver = await self.uow.repositories.driver.get_driver_by_phone(phone_number)
        if not driver:
            driver = Driver(
                name=payload.get("name", "Unknown Driver"),
                phone_number=phone_number,
                employee_id=payload.get("employee_id"),
                status=DriverStatus.ACTIVE,
                origin_type="verified_event",
                origin_id=origin_id
            )
            
            employment_status = payload.get("employment_status")
            if employment_status:
                try:
                    driver.employment_status = EmploymentStatus(employment_status)
                except ValueError:
                    pass

        await self.uow.repositories.driver.upsert_driver(driver)
        
    async def _record_driver_updated(self, phone_number: str, payload: dict, origin_id: str) -> None:
        driver = await self.uow.repositories.driver.get_driver_by_phone(phone_number)
        if not driver:
            return # Cannot update a driver that doesn't exist

        if "name" in payload:
            driver.name = payload["name"]
        if "avatar_url" in payload:
            driver.avatar_url = payload["avatar_url"]
        
        employment_status = payload.get("employment_status")
        if employment_status:
            try:
                driver.employment_status = EmploymentStatus(employment_status)
            except ValueError:
                pass
            
        driver.origin_type = "verified_event"
        driver.origin_id = origin_id
        
        await self.uow.repositories.driver.upsert_driver(driver)

    async def _record_driver_status_changed(self, phone_number: str, payload: dict, origin_id: str) -> None:
        driver = await self.uow.repositories.driver.get_driver_by_phone(phone_number)
        if not driver:
            return
            
        new_status = payload.get("status")
        if new_status:
            try:
                driver.status = DriverStatus(new_status)
                driver.origin_type = "verified_event"
                driver.origin_id = origin_id
                await self.uow.repositories.driver.upsert_driver(driver)
            except ValueError:
                pass # Invalid status enum

    async def _record_driver_license_updated(self, phone_number: str, payload: dict, origin_id: str) -> None:
        driver = await self.uow.repositories.driver.get_driver_by_phone(phone_number)
        if not driver:
            return

        if "license_number" in payload:
            driver.license_number = payload["license_number"]
        if "license_valid_until" in payload:
            try:
                # Convert ISO string to date
                driver.license_valid_until = date.fromisoformat(payload["license_valid_until"])
            except (ValueError, TypeError):
                pass
                
        driver.origin_type = "verified_event"
        driver.origin_id = origin_id
        
        await self.uow.repositories.driver.upsert_driver(driver)

    # --- Read APIs ---

    async def get_driver(self, driver_id: int, company_id: Optional[int] = None) -> Optional[Driver]:
        return await self.uow.repositories.driver.get_driver_by_id(driver_id, company_id=company_id)

    async def search_drivers(
        self, 
        is_active: Optional[bool] = None, 
        limit: int = 50, 
        offset: int = 0,
        company_id: Optional[int] = None
    ) -> Sequence[Driver]:
        return await self.uow.repositories.driver.search_drivers(is_active=is_active, limit=limit, offset=offset, company_id=company_id)
