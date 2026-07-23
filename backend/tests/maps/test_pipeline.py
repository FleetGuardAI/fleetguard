import unittest
from unittest.mock import patch
from infrastructure.maps.maps_service import MapsService
from infrastructure.maps.models import Coordinate, Route, Address

class TestMapsPipeline(unittest.TestCase):
    def setUp(self):
        self.service = MapsService()

    @patch.object(MapsService, '_make_route_request')
    def test_calculate_eta(self, mock_route_req):
        origin = Coordinate(latitude=10.0, longitude=20.0)
        dest = Coordinate(latitude=11.0, longitude=21.0)
        
        mock_route = Route(
            origin=origin,
            destination=dest,
            distance_meters=1000,
            duration_seconds=3600,
            polyline="enc_poly"
        )
        mock_route_req.return_value = mock_route
        
        eta = self.service.calculate_eta(origin, dest)
        self.assertEqual(eta, 3600)
        mock_route_req.assert_called_once_with(origin, dest)
        
    @patch.object(MapsService, '_make_reverse_geocode_request')
    def test_reverse_geocode_pipeline(self, mock_rev_geo):
        coord = Coordinate(latitude=10.0, longitude=20.0)
        mock_address = Address(formatted_address="Test Address")
        mock_rev_geo.return_value = mock_address
        
        address = self.service.reverse_geocode(coord)
        self.assertEqual(address.formatted_address, "Test Address")
        mock_rev_geo.assert_called_once_with(coord)
