"""
Driver Management Domain - API
"""

import uuid
from typing import List
from domain.driver.schemas import RegisterDriverRequest, StateChangeRequest
from domain.driver.projections import DriverSummary
from domain.driver.service import DriverService
from domain.driver.queries import DriverQueryService

class DriverAPI:
    """
    Mock FastAPI-like routing controller.
    """
    def __init__(self, service: DriverService, queries: DriverQueryService):
        self.service = service
        self.queries = queries

    def register_driver(self, request: RegisterDriverRequest) -> DriverSummary:
        driver, events = self.service.register_driver(request)
        return DriverSummary.from_domain(driver)

    def get_driver(self, driver_id: uuid.UUID) -> DriverSummary:
        driver = self.service.get_driver(driver_id)
        if not driver:
            raise ValueError("Not found")
        return DriverSummary.from_domain(driver)
        
    def list_organization_drivers(self, organization_id: uuid.UUID) -> List[DriverSummary]:
        return self.queries.drivers_by_organization(organization_id)

    def activate_driver(self, driver_id: uuid.UUID, request: StateChangeRequest) -> DriverSummary:
        driver, events = self.service.activate_driver(driver_id, request.reason)
        return DriverSummary.from_domain(driver)
        
    def suspend_driver(self, driver_id: uuid.UUID, request: StateChangeRequest) -> DriverSummary:
        driver, events = self.service.suspend_driver(driver_id, request.reason)
        return DriverSummary.from_domain(driver)
