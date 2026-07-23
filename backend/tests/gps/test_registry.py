import unittest
from infrastructure.gps.registry import GPSProviderRegistry
from infrastructure.gps.providers.generic import GenericGPSProvider
from infrastructure.gps.providers.teltonika import TeltonikaProvider

class TestGPSRegistry(unittest.TestCase):
    def setUp(self):
        self.registry = GPSProviderRegistry()

    def test_register_and_get(self):
        self.registry.register(GenericGPSProvider)
        provider = self.registry.get_provider("generic")
        self.assertIsInstance(provider, GenericGPSProvider)

    def test_duplicate_registration(self):
        self.registry.register(GenericGPSProvider)
        with self.assertRaises(ValueError):
            self.registry.register(GenericGPSProvider)
            
    def test_missing_provider(self):
        with self.assertRaises(KeyError):
            self.registry.get_provider("non_existent")
