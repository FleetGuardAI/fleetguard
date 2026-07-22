import unittest
from infrastructure.scheduler.registry import JobRegistry
from infrastructure.scheduler.errors import HandlerNotRegistered

class TestJobRegistry(unittest.TestCase):
    def test_registration_and_resolution(self):
        registry = JobRegistry()
        def dummy_handler(payload): pass
        
        registry.register("test_job", dummy_handler)
        resolved = registry.resolve("test_job")
        self.assertEqual(resolved, dummy_handler)
        
    def test_unregistered_handler(self):
        registry = JobRegistry()
        with self.assertRaises(HandlerNotRegistered):
            registry.resolve("missing_job")
