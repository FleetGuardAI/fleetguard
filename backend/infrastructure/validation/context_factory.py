"""
FleetGuard — Validation Context Factory
Assembles the standard ValidationContext for the Validation Engine, keeping rules pure
by fetching all necessary external state upfront.
"""

from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from schemas.validation_sdk import ValidationContext
from schemas.operational_event import OperationalEventResponse, EntityType
from schemas.evidence_package import EvidencePackage
from schemas.fuel_domain import CurrentFuelState
from infrastructure.uow import SqlAlchemyUnitOfWork

logger = logging.getLogger(__name__)

class ValidationContextFactory:
    """
    Builds a rich context for the Validation Engine.
    Pre-fetches domain-specific data based on the event type and entity.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        # We can construct a lightweight UOW or use direct repositories.
        # Since we just need reads, using a session directly with repositories is fine.
        from infrastructure.uow import RepositoryRegistry
        self.repositories = RepositoryRegistry(db)

    async def build(
        self, 
        event: OperationalEventResponse, 
        package: EvidencePackage,
        evidence_records: List[Dict[str, Any]]
    ) -> ValidationContext:
        """
        Assembles and returns a populated ValidationContext.
        """
        business_state: Dict[str, Any] = {}
        
        # Specific context building based on Entity Type
        if event.entity_type == EntityType.VEHICLE:
            try:
                vehicle_id = int(event.entity_id)
                vehicle = await self.repositories.vehicle.get_vehicle_by_id(vehicle_id)
                if vehicle:
                    # Provide essential vehicle metadata for rules (e.g. tank capacity check)
                    business_state["vehicle"] = {
                        "id": vehicle.id,
                        "tank_capacity": vehicle.tank_capacity,
                        "status": vehicle.status.value if vehicle.status else None
                    }
                    
                    # Fetch current fuel state
                    fuel_state = await self.repositories.fuel_state.get_fuel_state_by_vehicle(vehicle_id)
                    if fuel_state:
                        business_state["current_fuel_state"] = CurrentFuelState(
                            vehicle_id=vehicle_id,
                            current_fuel_liters=fuel_state.current_level,
                            capacity_liters=vehicle.tank_capacity,
                            source=fuel_state.source,
                            reliability=fuel_state.reliability,
                            last_updated=fuel_state.last_updated_at,
                            last_operational_event_id=fuel_state.last_operational_event_id
                        )
            except ValueError:
                logger.warning(f"Invalid vehicle ID format in event entity_id: {event.entity_id}")
            except Exception as e:
                logger.error(f"Error fetching vehicle state for ValidationContext: {e}")

        # You can add other entity-specific context builders here (e.g. Driver, Expense)

        return ValidationContext(
            event=event,
            evidence_package=package,
            evidence_records=evidence_records,
            business_state=business_state,
            configuration={},
            metadata={"built_by": "ValidationContextFactory"}
        )
