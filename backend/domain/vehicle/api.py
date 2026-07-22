"""
Vehicle Management Domain - API
"""

import uuid
from typing import List
from domain.vehicle.schemas import RegisterVehicleRequest, VehicleResponse, StateChangeRequest, UpdateConfigurationRequest
from domain.vehicle.vehicle_service import VehicleService
from domain.vehicle.queries import VehicleQueries

class VehicleAPI:
    """
    Mock FastAPI-like routing controller.
    """
    def __init__(self, service: VehicleService, queries: VehicleQueries):
        self.service = service
        self.queries = queries

    def register_vehicle(self, request: RegisterVehicleRequest) -> VehicleResponse:
        vehicle, events = self.service.register_vehicle(request)
        # In a real app, events would be dispatched to a message bus here
        return VehicleResponse.from_domain(vehicle)

    def get_vehicle(self, vehicle_id: uuid.UUID) -> VehicleResponse:
        vehicle = self.service.get_vehicle(vehicle_id)
        if not vehicle:
            raise ValueError("Not found") # Would be HTTPException 404
        return VehicleResponse.from_domain(vehicle)
        
    def list_organization_vehicles(self, organization_id: uuid.UUID) -> List[VehicleResponse]:
        return self.queries.list_organization_vehicles(organization_id)

    def activate_vehicle(self, vehicle_id: uuid.UUID, request: StateChangeRequest) -> VehicleResponse:
        vehicle, events = self.service.activate_vehicle(vehicle_id, request.reason)
        return VehicleResponse.from_domain(vehicle)
        
    def update_configuration(self, vehicle_id: uuid.UUID, request: UpdateConfigurationRequest) -> VehicleResponse:
        vehicle, events = self.service.update_configuration(vehicle_id, request.configuration)
        return VehicleResponse.from_domain(vehicle)
