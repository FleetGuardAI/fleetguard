"""
Vehicle Management Domain - Queries and Projections
"""

import uuid
from typing import List
from domain.vehicle.repository import BaseVehicleRepository
from domain.vehicle.schemas import VehicleResponse

class VehicleQueries:
    """
    Handles read-only queries and builds projections (read models) for UI consumption.
    Decouples dashboard queries from the aggregate root.
    """
    def __init__(self, repository: BaseVehicleRepository):
        self.repository = repository

    def list_organization_vehicles(self, organization_id: uuid.UUID) -> List[VehicleResponse]:
        vehicles = self.repository.find_by_organization(organization_id)
        return [VehicleResponse.from_domain(v) for v in vehicles]

    def search_active_vehicles(self, organization_id: uuid.UUID) -> List[VehicleResponse]:
        vehicles = self.repository.search(status="ACTIVE")
        return [VehicleResponse.from_domain(v) for v in vehicles if v.organization_id == organization_id]
