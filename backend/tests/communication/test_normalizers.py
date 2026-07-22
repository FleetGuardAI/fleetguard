import unittest
from datetime import timezone
from infrastructure.communication.normalizers import normalize_phone_number, normalize_timestamp, normalize_text

class TestNormalizers(unittest.TestCase):
    def test_normalize_phone(self):
        self.assertEqual(normalize_phone_number(" 123-456 "), "+123456")
        self.assertEqual(normalize_phone_number("+123"), "+123")
        self.assertEqual(normalize_phone_number("(555) 123-4567"), "+5551234567")
        self.assertEqual(normalize_phone_number(""), "")

    def test_normalize_timestamp(self):
        dt = normalize_timestamp("2026-07-20T00:36:44Z")
        self.assertEqual(dt.year, 2026)
        self.assertEqual(dt.tzinfo, timezone.utc)

    def test_normalize_text(self):
        self.assertEqual(normalize_text("  hello  "), "hello")
        self.assertEqual(normalize_text(""), "")
