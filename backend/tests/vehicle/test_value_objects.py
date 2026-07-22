import unittest
from domain.vehicle.value_objects import RegistrationNumber, VIN
from domain.vehicle.errors import InvalidIdentifier

class TestValueObjects(unittest.TestCase):
    def test_registration_number(self):
        valid = RegistrationNumber(value="AB-1234-XYZ")
        self.assertEqual(valid.value, "AB-1234-XYZ")
        
        with self.assertRaises(InvalidIdentifier):
            RegistrationNumber(value="")
            
        with self.assertRaises(InvalidIdentifier):
            RegistrationNumber(value="INVALID REG") # Space not allowed in our simplistic regex

    def test_vin(self):
        valid = VIN(value="1HGCM82633A004352")
        self.assertEqual(valid.value, "1HGCM82633A004352")
        
        with self.assertRaises(InvalidIdentifier):
            VIN(value="SHORT")
            
        with self.assertRaises(InvalidIdentifier):
            VIN(value="1HGCM82633A004352X") # 18 chars
