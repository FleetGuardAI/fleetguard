"""
Unit & Integration Tests for Hardware Assets Production Fixes (FIX 1 to FIX 6)
"""
import os
os.environ["TESTING"] = "True"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["SECRET_KEY"] = "production_audit_test_secret_key_12345"

import unittest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.testclient import TestClient

from config import settings
from routers.telematics import router as telematics_router
from database import get_db
from models.asset_domain import Asset, AssetType, ConnectionStatus, AssetOperationalStatus
from models.location_tracking import VehicleLocation
from schemas.telematics import NormalizedHardwareEvent
from schemas.asset_domain import GPSProviderAccountCreateRequest, GPSProviderAccountResponse
from services.location_service import LocationService


class TestTelematicsWebhookAuth(unittest.TestCase):
    def setUp(self):
        self.app = FastAPI()
        self.app.state.settings = settings
        self.app.include_router(telematics_router)
        self.app.dependency_overrides[get_db] = lambda: AsyncMock()
        self.client = TestClient(self.app)

    def test_unconfigured_secret_returns_503(self):
        settings.TELEMATICS_WEBHOOK_SECRET = None
        resp = self.client.post(
            "/api/v1/tracking/telematics/webhook",
            json=[{"latitude": 28.61, "longitude": 77.20, "timestamp": "2026-11-22T20:00:00Z"}]
        )
        self.assertEqual(resp.status_code, 503)
        self.assertIn("not configured", resp.json()["detail"])

    def test_invalid_secret_returns_401(self):
        settings.TELEMATICS_WEBHOOK_SECRET = "super_secure_telematics_secret"
        resp = self.client.post(
            "/api/v1/tracking/telematics/webhook",
            headers={"X-Telematics-Secret": "wrong_secret"},
            json=[{"latitude": 28.61, "longitude": 77.20, "timestamp": "2026-11-22T20:00:00Z"}]
        )
        self.assertEqual(resp.status_code, 401)
        self.assertIn("Invalid telematics secret", resp.json()["detail"])

    def test_missing_header_returns_401(self):
        settings.TELEMATICS_WEBHOOK_SECRET = "super_secure_telematics_secret"
        resp = self.client.post(
            "/api/v1/tracking/telematics/webhook",
            json=[{"latitude": 28.61, "longitude": 77.20, "timestamp": "2026-11-22T20:00:00Z"}]
        )
        self.assertEqual(resp.status_code, 401)

    @patch("services.location_service.LocationService.process_hardware_batch")
    def test_valid_header_secret_authenticates(self, mock_process):
        settings.TELEMATICS_WEBHOOK_SECRET = "super_secure_telematics_secret"
        mock_process.return_value = {"accepted": 1, "duplicates": 0, "rejected": 0, "items": []}
        
        resp = self.client.post(
            "/api/v1/tracking/telematics/webhook",
            headers={"X-Telematics-Secret": "super_secure_telematics_secret"},
            json=[{"device_imei": "123456789012345", "latitude": 28.61, "longitude": 77.20, "timestamp": "2026-11-22T20:00:00Z"}]
        )
        self.assertEqual(resp.status_code, 200)

    def test_query_param_secret_rejected_with_401(self):
        settings.TELEMATICS_WEBHOOK_SECRET = "super_secure_telematics_secret"
        resp = self.client.post(
            "/api/v1/tracking/telematics/webhook?secret=super_secure_telematics_secret",
            json=[{"device_imei": "123456789012345", "latitude": 28.61, "longitude": 77.20, "timestamp": "2026-11-22T20:00:00Z"}]
        )
        # Query parameter auth is strictly forbidden; must return 401
        self.assertEqual(resp.status_code, 401)


class TestUnassignedHardwareTelemetry(unittest.IsolatedAsyncioTestCase):
    async def test_unassigned_hardware_updates_asset_cache_without_vehicle_location(self):
        # Setup mock db and unassigned asset
        mock_asset = Asset(
            id=42,
            company_id=1,
            business_id="HW-TEST01",
            imei="860123456789012",
            serial_number="860123456789012",
            asset_type=AssetType.GPS_DEVICE,
            current_vehicle_id=None,  # Unassigned!
            connection_status=ConnectionStatus.PENDING.value,
            last_communication_at=None,
            last_known_lat=None,
            last_known_lng=None
        )

        mock_db = AsyncMock()
        mock_scalar_result = MagicMock()
        mock_scalar_result.scalars.return_value.all.return_value = [mock_asset]
        mock_db.execute.return_value = mock_scalar_result

        telemetry_event = NormalizedHardwareEvent(
            device_imei="860123456789012",
            latitude=19.0760,
            longitude=72.8777,
            timestamp=datetime(2026, 11, 22, 18, 30, tzinfo=timezone.utc),
            speed=45.5,
            heading=180.0,
            ignition_status=True,
            source_metadata={"battery_level": 94.5}
        )

        res = await LocationService.process_hardware_batch(
            db=mock_db,
            locations=[telemetry_event],
            allow_registration_only=False
        )

        # 1. Assert batch outcome
        self.assertEqual(res["accepted"], 1)
        self.assertEqual(res["rejected"], 0)
        self.assertEqual(res["items"][0]["status"], "accepted_unassigned")

        # 2. Assert Asset cache updated
        self.assertEqual(mock_asset.connection_status, ConnectionStatus.CONNECTED.value)
        self.assertEqual(mock_asset.operational_status, AssetOperationalStatus.OK)
        self.assertEqual(mock_asset.last_known_lat, 19.0760)
        self.assertEqual(mock_asset.last_known_lng, 72.8777)
        self.assertEqual(mock_asset.last_known_speed, 45.5)
        self.assertEqual(mock_asset.last_known_heading, 180.0)
        self.assertEqual(mock_asset.last_known_ignition, True)
        self.assertEqual(mock_asset.last_known_battery, 94.5)
        self.assertEqual(mock_asset.last_communication_at, datetime(2026, 11, 22, 18, 30, tzinfo=timezone.utc))

        # 3. Assert NO VehicleLocation was added to DB
        for call in mock_db.add.call_args_list:
            added_obj = call[0][0]
            self.assertFalse(isinstance(added_obj, VehicleLocation), "VehicleLocation should NOT be created for unassigned device")


class TestProviderAccountSchema(unittest.TestCase):
    def test_provider_account_create_request_schema(self):
        req = GPSProviderAccountCreateRequest(
            provider_type="traccar",
            name="Primary Traccar Gateway",
            server_url="http://traccar:8082",
            credentials="admin:secret_token_123",
            config={"sync_interval_seconds": 60}
        )
        self.assertEqual(req.name, "Primary Traccar Gateway")
        self.assertEqual(req.credentials, "admin:secret_token_123")
        self.assertEqual(req.server_url, "http://traccar:8082")

    def test_provider_account_response_omits_credentials(self):
        data = {
            "id": 1,
            "company_id": 5,
            "provider_type": "traccar",
            "name": "Production Traccar",
            "server_url": "http://traccar:8082",
            "account_id": "acc-100",
            "sync_status": "CONNECTED",
            "last_sync_at": datetime.now(timezone.utc),
            "sync_error": None,
            "device_count": 8,
            "config": {},
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        resp = GPSProviderAccountResponse.model_validate(data)
        serialized = resp.model_dump()
        self.assertNotIn("credentials", serialized)
        self.assertNotIn("encrypted_credentials", serialized)
        self.assertEqual(serialized["name"], "Production Traccar")
        self.assertEqual(serialized["sync_status"], "CONNECTED")


class TestAlembicLinearGraph(unittest.TestCase):
    def test_single_clean_head(self):
        from pathlib import Path
        from alembic.config import Config
        from alembic.script import ScriptDirectory

        backend_dir = Path(__file__).resolve().parent.parent
        ini_path = backend_dir / "alembic.ini"
        migrations_path = backend_dir / "migrations"

        alembic_cfg = Config(str(ini_path))
        alembic_cfg.set_main_option("script_location", str(migrations_path))
        script = ScriptDirectory.from_config(alembic_cfg)

        heads = script.get_heads()
        self.assertEqual(len(heads), 1, f"Expected 1 head, got {heads}")
        self.assertEqual(heads[0], "a2b3c4d5e6f7")


if __name__ == "__main__":
    unittest.main()
