import unittest
from pydantic import ValidationError
from infrastructure.maps.models import Coordinate, Address

class TestMapsModels(unittest.TestCase):
    def test_coordinate_immutability(self):
        coord = Coordinate(latitude=10.0, longitude=20.0)
        with self.assertRaises(ValidationError):
            coord.latitude = 15.0

    def test_address_immutability(self):
        addr = Address(formatted_address="123 Main St", locality="City")
        with self.assertRaises(ValidationError):
            addr.locality = "New City"
