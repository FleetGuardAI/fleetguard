import unittest
from infrastructure.fuel.registry import FuelProviderRegistry
from infrastructure.fuel.providers.generic import GenericFuelProvider

class TestFuelRegistry(unittest.TestCase):
    def setUp(self):
        self.registry = FuelProviderRegistry()

    def test_register_and_get(self):
        self.registry.register(GenericFuelProvider)
        provider = self.registry.get_provider("generic")
        self.assertIsInstance(provider, GenericFuelProvider)

    def test_duplicate_registration(self):
        self.registry.register(GenericFuelProvider)
        with self.assertRaises(ValueError):
            self.registry.register(GenericFuelProvider)
            
    def test_missing_provider(self):
        with self.assertRaises(KeyError):
            self.registry.get_provider("non_existent")
