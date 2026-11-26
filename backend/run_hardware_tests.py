import os
os.environ["TESTING"] = "True"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["SECRET_KEY"] = "production_audit_test_secret_key_12345"
os.environ["TELEMATICS_WEBHOOK_SECRET"] = "traccar_forwarder_secret_key_999"

import sys
import unittest

if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    import tests.test_universal_telematics_and_hardware as mod_telematics
    import tests.test_hardware_api_router as mod_router
    import tests.test_hardware_production_fixes as mod_fixes
    import tests.test_provider_lifecycle as mod_provider
    import tests.test_real_gps_integration_simulation as mod_sim
    import tests.test_migration_safety as mod_migration
    import tests.test_quarantine_security as mod_quarantine
    import tests.test_raw_wire_protocols_and_forwarder as mod_wire
    
    suite.addTests(loader.loadTestsFromModule(mod_telematics))
    suite.addTests(loader.loadTestsFromModule(mod_router))
    suite.addTests(loader.loadTestsFromModule(mod_fixes))
    suite.addTests(loader.loadTestsFromModule(mod_provider))
    suite.addTests(loader.loadTestsFromModule(mod_sim))
    suite.addTests(loader.loadTestsFromModule(mod_migration))
    suite.addTests(loader.loadTestsFromModule(mod_quarantine))
    suite.addTests(loader.loadTestsFromModule(mod_wire))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
