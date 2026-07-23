import unittest
from datetime import datetime, timezone
from infrastructure.gps.normalizers import (
    normalize_coordinate,
    normalize_speed,
    normalize_heading,
    normalize_ignition,
    normalize_timestamp
)

class TestGPSNormalizers(unittest.TestCase):
    def test_normalize_coordinate(self):
        self.assertEqual(normalize_coordinate(12.3456789), 12.345679)
        self.assertEqual(normalize_coordinate("12.345"), 12.345)

    def test_normalize_speed(self):
        self.assertEqual(normalize_speed(60), 60.0)
        self.assertEqual(normalize_speed(60, "mph"), 96.56)
        self.assertEqual(normalize_speed(10, "m/s"), 36.0)

    def test_normalize_heading(self):
        self.assertEqual(normalize_heading(90), 90.0)
        self.assertEqual(normalize_heading(370), 10.0)
        self.assertEqual(normalize_heading(-10), 350.0)

    def test_normalize_ignition(self):
        self.assertTrue(normalize_ignition(True))
        self.assertTrue(normalize_ignition(1))
        self.assertTrue(normalize_ignition("ON"))
        self.assertFalse(normalize_ignition(False))
        self.assertFalse(normalize_ignition(0))
        self.assertFalse(normalize_ignition("off"))
        
    def test_normalize_timestamp(self):
        # Integer seconds
        dt = normalize_timestamp(1672531200)
        self.assertEqual(dt.year, 2023)
        self.assertEqual(dt.tzinfo, timezone.utc)
        
        # ISO string
        dt2 = normalize_timestamp("2023-01-01T00:00:00Z")
        self.assertEqual(dt2.year, 2023)
        self.assertEqual(dt2.tzinfo, timezone.utc)
