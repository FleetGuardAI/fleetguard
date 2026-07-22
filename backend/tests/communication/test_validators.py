import unittest
from infrastructure.communication.validators import validate_required_fields, validate_sender_format, validate_timestamp_format

class TestValidators(unittest.TestCase):
    def test_required_fields(self):
        payload = {"a": 1, "b": 2}
        self.assertTrue(validate_required_fields(payload, ["a", "b"]))
        with self.assertRaises(ValueError):
            validate_required_fields(payload, ["a", "c"])

    def test_sender_format(self):
        self.assertTrue(validate_sender_format("+1234567890"))
        with self.assertRaises(ValueError):
            validate_sender_format("")

    def test_timestamp_format(self):
        self.assertTrue(validate_timestamp_format("2026-07-20T00:36:44Z"))
        with self.assertRaises(ValueError):
            validate_timestamp_format("")
