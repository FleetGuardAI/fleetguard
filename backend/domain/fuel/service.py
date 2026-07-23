"""
Fuel Operations Domain - Service
"""

import uuid
from typing import Optional

from domain.fuel.value_objects import Volume, Location, TankCalibration
from domain.fuel.repository import BaseFuelRepository

class FuelService:
    """
    Orchestrates the Fuel domain.
    """
    def __init__(self, repository: BaseFuelRepository):
        self._repository = repository

    def handle_fuel_fill(self, vehicle_id: str, liters: float, driver_id: Optional[uuid.UUID] = None, trip_id: Optional[uuid.UUID] = None, location: Optional[Location] = None) -> None:
        ledger = self._repository.get_ledger(vehicle_id)
        volume = Volume(liters=liters)
        
        tx, events = ledger.record_fill(volume, driver_id, trip_id, location)
        
        self._repository.save_transaction(tx)
        # EventBus publish omitted for brevity

    def handle_fuel_drain(self, vehicle_id: str, liters: float, driver_id: Optional[uuid.UUID] = None, trip_id: Optional[uuid.UUID] = None, location: Optional[Location] = None) -> None:
        ledger = self._repository.get_ledger(vehicle_id)
        volume = Volume(liters=liters)
        
        tx, events = ledger.record_drain(volume, driver_id, trip_id, location)
        
        self._repository.save_transaction(tx)
        # EventBus publish omitted for brevity

    def update_calibration(self, vehicle_id: str, max_capacity_liters: float) -> None:
        ledger = self._repository.get_ledger(vehicle_id)
        calib = TankCalibration(max_capacity_liters=max_capacity_liters)
        
        events = ledger.update_calibration(calib)
        self._repository.save_calibration(vehicle_id, calib)
