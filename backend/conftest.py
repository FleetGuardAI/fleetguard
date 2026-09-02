import os
import pytest


# Disable Kafka and OTP Mock for tests by default
os.environ["KAFKA_ENABLED"] = "False"
os.environ["OTP_MOCK_MODE"] = "True"
os.environ["DEBUG"] = "True"

@pytest.fixture(scope="session", autouse=True)
async def cleanup_engine():
    from database import engine
    yield
    await engine.dispose()
