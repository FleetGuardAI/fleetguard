"""
Fuel Operations Domain - Repository
"""

import abc
from typing import List, Optional
from domain.fuel.aggregate import FuelLedger
from domain.fuel.models import FuelTransaction
from domain.fuel.value_objects import TankCalibration

class BaseFuelRepository(abc.ABC):
    @abc.abstractmethod
    def get_ledger(self, vehicle_id: str) -> FuelLedger:
        pass
        
    @abc.abstractmethod
    def save_transaction(self, transaction: FuelTransaction) -> None:
        pass

    @abc.abstractmethod
    def save_calibration(self, vehicle_id: str, calibration: TankCalibration) -> None:
        pass

class InMemoryFuelRepository(BaseFuelRepository):
    def __init__(self):
        self._transactions: List[FuelTransaction] = []
        self._calibrations = {}

    def get_ledger(self, vehicle_id: str) -> FuelLedger:
        ledger = FuelLedger(vehicle_id)
        vehicle_txs = [t for t in self._transactions if t.vehicle_id == vehicle_id]
        calib = self._calibrations.get(vehicle_id)
        ledger.load_from_history(vehicle_txs, calib)
        return ledger

    def save_transaction(self, transaction: FuelTransaction) -> None:
        self._transactions.append(transaction)

    def save_calibration(self, vehicle_id: str, calibration: TankCalibration) -> None:
        self._calibrations[vehicle_id] = calibration
