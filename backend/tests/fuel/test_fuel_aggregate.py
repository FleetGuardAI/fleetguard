import unittest
from datetime import datetime, timezone
import uuid

from domain.fuel.aggregate import FuelLedger
from domain.fuel.value_objects import Volume, TankCalibration
from domain.fuel.errors import CapacityExceededError, NegativeBalanceError
from domain.fuel.models import TransactionType

class TestFuelLedger(unittest.TestCase):
    def setUp(self):
        self.vehicle_id = "veh-123"
        self.ledger = FuelLedger(self.vehicle_id)

    def test_record_fill(self):
        volume = Volume(liters=50.0)
        tx, events = self.ledger.record_fill(volume)
        
        self.assertEqual(self.ledger.current_balance, 50.0)
        self.assertEqual(len(self.ledger.transactions), 1)
        self.assertEqual(tx.transaction_type, TransactionType.FILL)
        self.assertEqual(tx.volume.liters, 50.0)
        self.assertEqual(len(events), 2) # FuelFillRecorded, FuelBalanceUpdated

    def test_record_drain(self):
        # Setup initial balance
        self.ledger.record_fill(Volume(liters=100.0))
        
        tx, events = self.ledger.record_drain(Volume(liters=20.0))
        
        self.assertEqual(self.ledger.current_balance, 80.0)
        self.assertEqual(tx.transaction_type, TransactionType.DRAIN)
        self.assertEqual(tx.volume.liters, 20.0)

    def test_negative_balance_prevented(self):
        with self.assertRaises(NegativeBalanceError):
            self.ledger.record_drain(Volume(liters=10.0))
            
    def test_capacity_exceeded_prevented(self):
        self.ledger.update_calibration(TankCalibration(max_capacity_liters=100.0))
        
        self.ledger.record_fill(Volume(liters=80.0))
        
        with self.assertRaises(CapacityExceededError):
            self.ledger.record_fill(Volume(liters=30.0))

if __name__ == "__main__":
    unittest.main()
