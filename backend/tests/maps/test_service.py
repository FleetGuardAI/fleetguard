import unittest
from infrastructure.maps.maps_service import MapsService
from infrastructure.maps.models import Coordinate, Geofence

class TestMapsService(unittest.TestCase):
    def setUp(self):
        self.service = MapsService()

    def test_calculate_distance(self):
        # Distance between NY and London
        ny = Coordinate(latitude=40.7128, longitude=-74.0060)
        london = Coordinate(latitude=51.5074, longitude=-0.1278)
        
        dist = self.service.calculate_distance(ny, london)
        # Expected ~5570 km
        self.assertTrue(5500000 < dist < 5600000)

    def test_is_inside_geofence(self):
        center = Coordinate(latitude=0.0, longitude=0.0)
        geofence = Geofence(center=center, radius_meters=1000.0)
        
        # Exact center
        inside_coord = Coordinate(latitude=0.0, longitude=0.0)
        self.assertTrue(self.service.is_inside_geofence(inside_coord, geofence))
        
        # Very far away
        outside_coord = Coordinate(latitude=1.0, longitude=1.0)
        self.assertFalse(self.service.is_inside_geofence(outside_coord, geofence))

    def test_unimplemented_api_boundaries(self):
        coord = Coordinate(latitude=0.0, longitude=0.0)
        with self.assertRaises(NotImplementedError):
            self.service.reverse_geocode(coord)
            
        with self.assertRaises(NotImplementedError):
            self.service.forward_geocode("123 Main St")
            
        with self.assertRaises(NotImplementedError):
            self.service.calculate_route(coord, coord)
            
        with self.assertRaises(NotImplementedError):
            self.service.snap_to_road([coord])
