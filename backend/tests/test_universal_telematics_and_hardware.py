import os
os.environ["TESTING"] = "True"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

import unittest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException

from models.asset_domain import (
    Asset,
    AssetType,
    AssetInstallationStatus,
    AssetOperationalStatus,
    ConnectionStatus,
    ConnectionType,
    GPSProviderAccount,
)
from models.vehicle_domain import Vehicle, VehicleStatus
from models.location_tracking import VehicleLocation, LocationSource
from schemas.asset_domain import (
    HardwareDeviceRegisterRequest,
    HardwareDeviceUpdateRequest,
    VehicleReassignRequest,
    PreRegistrationTestRequest,
)
from schemas.telematics import NormalizedHardwareEvent
from services.hardware_service import (
    HardwareService,
    validate_imei_format,
    haversine_distance_km,
)
from services.traccar_service import TraccarService
from services.location_service import LocationService
from utils.credential_crypto import encrypt_credential, decrypt_credential, encrypt_dict, decrypt_dict
from infrastructure.gps.registry import create_default_registry
from domain.hardware_registry.verified_protocols import get_verified_registry


def make_test_asset(**kwargs):
    defaults = {
        "id": 1,
        "company_id": 1,
        "business_id": "HW-001",
        "device_name": "Test GPS",
        "asset_type": AssetType.GPS_DEVICE,
        "manufacturer": "Teltonika",
        "model": "FMB920",
        "imei": "865432019876543",
        "serial_number": "865432019876543",
        "connection_type": ConnectionType.DIRECT_HARDWARE.value,
        "connection_status": ConnectionStatus.PENDING.value,
        "installation_status": AssetInstallationStatus.INSTALLED,
        "operational_status": AssetOperationalStatus.OK,
        "offline_threshold_minutes": 15,
        "current_vehicle_id": 1,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    defaults.update(kwargs)
    return Asset(**defaults)


def create_mock_db():
    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()
    return db


class TestProtocolNormalizationAndCrypto(unittest.TestCase):
    def test_credential_encryption_and_decryption(self):
        raw_token = "traccar_admin_sec_994411_xyz"
        cipher = encrypt_credential(raw_token)
        self.assertNotEqual(raw_token, cipher)
        self.assertIn("gAAAAA", cipher)

        recovered = decrypt_credential(cipher)
        self.assertEqual(raw_token, recovered)
        self.assertIsNone(decrypt_credential("corrupt-invalid-token"))

        d = {"api_key": "sec_123", "password": "pass"}
        enc_d = encrypt_dict(d)
        dec_d = decrypt_dict(enc_d)
        self.assertEqual(dec_d, d)

    def test_universal_protocols_registry(self):
        reg = create_default_registry()
        providers = reg.list_providers()
        for p in ["generic", "teltonika", "queclink", "traccar", "ais140", "gt06", "tk103", "mqtt"]:
            self.assertIn(p, providers)

        compat = get_verified_registry()
        self.assertGreater(len(compat["protocols"]), 8)
        self.assertGreater(len(compat["manufacturers"]), 5)

    def test_ais140_normalization(self):
        reg = create_default_registry()
        provider = reg.get_provider("ais140")
        raw = {
            "imei": "864201041234567",
            "latitude": 28.6139,
            "longitude": 77.2090,
            "timestamp": "2026-11-22T10:30:00Z",
            "speed": 45.5,
            "heading": 180.0,
            "altitude": 215.0,
            "ignition": True,
            "emergency_status": False
        }
        pos = provider.receive(raw)
        self.assertEqual(pos.device_id, "864201041234567")
        self.assertAlmostEqual(pos.latitude, 28.6139, places=4)
        self.assertAlmostEqual(pos.longitude, 77.2090, places=4)
        self.assertTrue(pos.ignition)
        self.assertEqual(pos.speed, 45.5)

    def test_gt06_normalization(self):
        reg = create_default_registry()
        provider = reg.get_provider("gt06")
        raw = {
            "imei": "860012345678901",
            "latitude": 28.5355,
            "longitude": 77.3910,
            "timestamp": "2026-11-22T10:35:00Z",
            "speed": 60.0,
            "heading": 90.0,
            "ignition": True
        }
        pos = provider.receive(raw)
        self.assertEqual(pos.device_id, "860012345678901")
        self.assertAlmostEqual(pos.latitude, 28.5355, places=4)
        self.assertEqual(pos.speed, 60.0)

    def test_tk103_normalization(self):
        reg = create_default_registry()
        provider = reg.get_provider("tk103")
        raw = {
            "imei": "860099998888777",
            "latitude": 19.0760,
            "longitude": 72.8777,
            "timestamp": "2026-11-22T10:40:00Z",
            "speed": 35.0,
            "heading": 120.0,
            "ignition": False
        }
        pos = provider.receive(raw)
        self.assertEqual(pos.device_id, "860099998888777")
        self.assertAlmostEqual(pos.latitude, 19.0760, places=4)
        self.assertFalse(pos.ignition)

    def test_traccar_payload_parsing(self):
        raw = {
            "device": {"name": "Truck 1", "uniqueId": "860011223344556"},
            "position": {
                "latitude": 19.0760,
                "longitude": 72.8777,
                "speed": 25.0,  # knots
                "course": 90.0,
                "fixTime": "2026-11-22T11:00:00Z",
                "attributes": {"ignition": True, "batteryLevel": 95}
            }
        }
        event = TraccarService.parse_forward_payload(raw)
        self.assertEqual(event.device_imei, "860011223344556")
        self.assertAlmostEqual(event.latitude, 19.0760, places=4)
        self.assertAlmostEqual(event.longitude, 72.8777, places=4)
        self.assertAlmostEqual(event.speed, 46.3, places=1)
        self.assertTrue(event.ignition_status)

    def test_imei_validation(self):
        validate_imei_format("865432019876543")
        validate_imei_format("TELTONIKA-DEV-001")
        with self.assertRaises(ValueError):
            validate_imei_format("12")

    def test_haversine_distance(self):
        dist = haversine_distance_km(28.6139, 77.2090, 28.4595, 77.0266)
        self.assertGreater(dist, 23.0)
        self.assertLess(dist, 30.0)


class TestHardwareServiceLogic(unittest.TestCase):
    def test_compute_device_status(self):
        now = datetime.now(timezone.utc)
        
        a_connected = make_test_asset(
            connection_status=ConnectionStatus.CONNECTED.value,
            last_communication_at=now - timedelta(minutes=2),
            offline_threshold_minutes=15
        )
        st, is_stale = HardwareService._compute_device_status(a_connected)
        self.assertEqual(st, ConnectionStatus.CONNECTED.value)
        self.assertFalse(is_stale)

        a_disconnected = make_test_asset(
            connection_status=ConnectionStatus.CONNECTED.value,
            last_communication_at=now - timedelta(minutes=20),
            offline_threshold_minutes=15
        )
        st, is_stale = HardwareService._compute_device_status(a_disconnected)
        self.assertEqual(st, ConnectionStatus.DISCONNECTED.value)
        self.assertTrue(is_stale)

        a_pending = make_test_asset(
            connection_status=ConnectionStatus.PENDING.value,
            last_communication_at=None,
            offline_threshold_minutes=15
        )
        st, is_stale = HardwareService._compute_device_status(a_pending)
        self.assertEqual(st, ConnectionStatus.PENDING.value)
        self.assertTrue(is_stale)

        a_maint = make_test_asset(
            connection_status=ConnectionStatus.MAINTENANCE.value,
            last_communication_at=now,
            offline_threshold_minutes=15
        )
        st, is_stale = HardwareService._compute_device_status(a_maint)
        self.assertEqual(st, ConnectionStatus.MAINTENANCE.value)

    def test_register_device_duplicate_prevention(self):
        async def run():
            mock_db = create_mock_db()
            existing = make_test_asset(id=99, imei="860000000000001")
            
            mock_res = MagicMock()
            mock_res.scalars.return_value.first.return_value = existing
            mock_db.execute = AsyncMock(return_value=mock_res)

            payload = HardwareDeviceRegisterRequest(
                device_name="Tracker 1",
                connection_type=ConnectionType.DIRECT_HARDWARE.value,
                manufacturer="Concox",
                imei="860000000000001"
            )
            with self.assertRaises(HTTPException) as cm:
                await HardwareService.register_device(company_id=1, payload=payload, db=mock_db)
            self.assertEqual(cm.exception.status_code, 400)
            self.assertIn("already registered", cm.exception.detail)
        asyncio.run(run())

    def test_register_device_vehicle_conflict_prevention(self):
        async def run():
            mock_db = create_mock_db()
            v1 = Vehicle(id=1, company_id=1, registration_number="DL01AA1111")
            mock_db.get = AsyncMock(return_value=v1)

            mock_res1 = MagicMock()
            mock_res1.scalars.return_value.first.return_value = None

            conflict_device = make_test_asset(id=50, device_name="Old GPS", business_id="HW-OLD")
            mock_res2 = MagicMock()
            mock_res2.scalars.return_value.first.return_value = conflict_device
            mock_db.execute = AsyncMock(side_effect=[mock_res1, mock_res2])

            payload = HardwareDeviceRegisterRequest(
                device_name="New GPS",
                connection_type=ConnectionType.DIRECT_HARDWARE.value,
                manufacturer="Teltonika",
                imei="860000000000002",
                vehicle_id=1
            )
            with self.assertRaises(HTTPException) as cm:
                await HardwareService.register_device(company_id=1, payload=payload, db=mock_db)
            self.assertEqual(cm.exception.status_code, 409)
            self.assertIn("already has active GPS device", cm.exception.detail)
        asyncio.run(run())

    def test_register_device_unauthorized_vehicle_rejected(self):
        async def run():
            mock_db = create_mock_db()
            v_other = Vehicle(id=99, company_id=2, registration_number="MH04XX9999")
            mock_db.get = AsyncMock(return_value=v_other)

            mock_res1 = MagicMock()
            mock_res1.scalars.return_value.first.return_value = None
            mock_db.execute = AsyncMock(return_value=mock_res1)

            payload = HardwareDeviceRegisterRequest(
                device_name="Stealth GPS",
                connection_type=ConnectionType.DIRECT_HARDWARE.value,
                manufacturer="Teltonika",
                imei="860000000000003",
                vehicle_id=99
            )
            with self.assertRaises(HTTPException) as cm:
                await HardwareService.register_device(company_id=1, payload=payload, db=mock_db)
            self.assertEqual(cm.exception.status_code, 400)
            self.assertIn("does not belong to your company", cm.exception.detail)
        asyncio.run(run())

    def test_register_device_success(self):
        async def run():
            mock_db = create_mock_db()
            v1 = Vehicle(id=1, company_id=1, registration_number="DL01AA1111")
            mock_db.get = AsyncMock(return_value=v1)

            mock_res1 = MagicMock()
            mock_res1.scalars.return_value.first.return_value = None
            mock_res2 = MagicMock()
            mock_res2.scalars.return_value.first.return_value = None
            mock_db.execute = AsyncMock(side_effect=[mock_res1, mock_res2])

            payload = HardwareDeviceRegisterRequest(
                device_name="Apex Gateway 1",
                connection_type=ConnectionType.DIRECT_HARDWARE.value,
                manufacturer="Teltonika",
                model="FMB920",
                protocol="TELTONIKA_CODEC8",
                imei="865432019876543",
                vehicle_id=1,
                credentials={"api_key": "secret_key_fleet_123"},
                offline_threshold_minutes=15
            )
            resp = await HardwareService.register_device(company_id=1, payload=payload, db=mock_db)
            self.assertEqual(resp.device_name, "Apex Gateway 1")
            self.assertEqual(resp.imei, "865432019876543")
            self.assertEqual(resp.vehicle_registration, "DL01AA1111")
            self.assertEqual(resp.connection_status, ConnectionStatus.PENDING.value)
            self.assertGreaterEqual(mock_db.add.call_count, 2)
        asyncio.run(run())

    def test_reassign_vehicle_success(self):
        async def run():
            mock_db = create_mock_db()
            asset = make_test_asset(id=1, current_vehicle_id=1)
            target_v = Vehicle(id=2, company_id=1, registration_number="DL01BB2222")
            mock_db.get = AsyncMock(side_effect=[asset, target_v])
            
            mock_res_conflict = MagicMock()
            mock_res_conflict.scalars.return_value.first.return_value = None
            mock_db.execute = AsyncMock(return_value=mock_res_conflict)

            payload = VehicleReassignRequest(vehicle_id=2)
            resp = await HardwareService.reassign_vehicle(company_id=1, asset_id=1, payload=payload, db=mock_db)
            self.assertEqual(asset.current_vehicle_id, 2)
            self.assertEqual(asset.installation_status, AssetInstallationStatus.INSTALLED)
            self.assertEqual(mock_db.add.call_count, 1)
        asyncio.run(run())

    def test_disconnect_device_to_storage(self):
        async def run():
            mock_db = create_mock_db()
            asset = make_test_asset(id=1, current_vehicle_id=1)
            mock_db.get = AsyncMock(return_value=asset)

            resp = await HardwareService.disconnect_device(company_id=1, asset_id=1, db=mock_db)
            self.assertIsNone(asset.current_vehicle_id)
            self.assertEqual(asset.installation_status, AssetInstallationStatus.IN_STORAGE)
            self.assertEqual(mock_db.add.call_count, 1)
        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
