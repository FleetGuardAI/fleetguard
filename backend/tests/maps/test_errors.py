import unittest
from infrastructure.maps.errors import MapsServiceUnavailable, InvalidCoordinate

class TestMapsErrors(unittest.TestCase):
    def test_error_inheritance(self):
        with self.assertRaises(Exception):
            raise MapsServiceUnavailable("Test")
            
        with self.assertRaises(Exception):
            raise InvalidCoordinate("Test")
