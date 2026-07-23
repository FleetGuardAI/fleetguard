import unittest
from infrastructure.maps.errors import InvalidCoordinate, InvalidAddress
from infrastructure.maps.validators import validate_coordinate, validate_radius, validate_address_string

class TestMapsValidators(unittest.TestCase):
    def test_validate_coordinate_valid(self):
        coord = validate_coordinate(45.0, -90.0)
        self.assertEqual(coord.latitude, 45.0)
        self.assertEqual(coord.longitude, -90.0)

    def test_validate_coordinate_invalid_lat(self):
        with self.assertRaises(InvalidCoordinate):
            validate_coordinate(95.0, 0.0)

    def test_validate_coordinate_invalid_lon(self):
        with self.assertRaises(InvalidCoordinate):
            validate_coordinate(0.0, 200.0)

    def test_validate_radius(self):
        self.assertEqual(validate_radius(100.5), 100.5)
        with self.assertRaises(ValueError):
            validate_radius(-10)

    def test_validate_address_string(self):
        self.assertEqual(validate_address_string("  123 Main St  "), "123 Main St")
        with self.assertRaises(InvalidAddress):
            validate_address_string("   ")
