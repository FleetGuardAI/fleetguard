"""
Task 5: Synthetic Device Registration Test Suite
Validates the complete 10-point end-to-end verification criteria for:
- Device Name: Vahan Test Tracker 001
- IMEI: 359339075123456
- Manufacturer: Teltonika
- Model: FMB920
- Protocol: TELTONIKA_CODEC8
- Vehicle: RJ14UF0089
- Status: PENDING / PENDING CONFIG
"""
import asyncio
import os
import unittest
from datetime import datetime, timezone

os.environ["TESTING"] = "True"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["SECRET_KEY"] = "synthetic_registration_test_secret_key_12345"

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from database import Base
from models.company import Company
from models.user import User, UserRole
from models.vehicle_domain import Vehicle, VehicleStatus
from models.asset_domain import Asset, ConnectionStatus, ConnectionType, AssetInstallationStatus
from schemas.asset_domain import HardwareDeviceRegisterRequest
from services.hardware_service import HardwareService
from domain.hardware_registry.verified_protocols import get_verified_registry


class TestSyntheticDeviceRegistration(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        self.async_session = sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)

        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async with self.async_session() as db:
            # Create test company
            self.company = Company(
                id=10,
                company_name="Vahan Fleet Logistics",
                owner_name="Transport Owner",
                mobile_number="+919876543210",
                email="owner@vahanlogistics.com",
                status="ACTIVE",
            )
            db.add(self.company)

            # Create test vehicle RJ14UF0089
            self.vehicle = Vehicle(
                id=101,
                company_id=10,
                registration_number="RJ14UF0089",
                make="Tata",
                model="Signa 4825.TK",
                status=VehicleStatus.ACTIVE,
            )
            db.add(self.vehicle)
            await db.commit()

    async def asyncTearDown(self):
        await self.engine.dispose()

    async def test_full_synthetic_device_registration_workflow(self):
        """Executes and verifies all 10 criteria specified in Task 5."""
        async with self.async_session() as db:
            company_id = 10

            # -------------------------------------------------------------
            # CRITERION 1: Protocol dropdown / registry loads without error
            # -------------------------------------------------------------
            registry = get_verified_registry()
            self.assertIn("protocols", registry, "Criterion 1 Failed: Registry missing protocols list")
            self.assertIn("manufacturers", registry, "Criterion 1 Failed: Registry missing manufacturers list")
            codec8 = next((p for p in registry["protocols"] if p["id"] == "TELTONIKA_CODEC8"), None)
            self.assertIsNotNone(codec8, "Criterion 1 Failed: TELTONIKA_CODEC8 not in protocols registry")
            self.assertEqual(codec8["default_port"], 5027, "Criterion 1 Failed: Teltonika port must be 5027")

            # -------------------------------------------------------------
            # CRITERION 2: Registration payload is accepted (201 / 200)
            # -------------------------------------------------------------
            payload = HardwareDeviceRegisterRequest(
                device_name="Vahan Test Tracker 001",
                imei="359339075123456",
                manufacturer="Teltonika",
                model="FMB920",
                protocol="TELTONIKA_CODEC8",
                connection_type="TCP_DEVICE",
                vehicle_id=101,
                offline_threshold_minutes=15,
                gps_provider="Direct Vahan TCP",
                connection_config={
                    "serverHost": "ingest.thevahan.com",
                    "serverPort": 5027,
                },
                credentials={
                    "device_password": "teltonika_default_pass"
                }
            )

            response = await HardwareService.register_device(company_id, payload, db)
            self.assertIsNotNone(response, "Criterion 2 Failed: Registration returned None")
            self.assertEqual(response.device_name, "Vahan Test Tracker 001")
            self.assertEqual(response.imei, "359339075123456")

            # -------------------------------------------------------------
            # CRITERION 3: Asset record is created in the database
            # -------------------------------------------------------------
            asset_in_db = await db.get(Asset, response.id)
            self.assertIsNotNone(asset_in_db, "Criterion 3 Failed: Asset not persisted in database")
            self.assertEqual(asset_in_db.company_id, 10)
            self.assertEqual(asset_in_db.current_vehicle_id, 101)
            self.assertEqual(asset_in_db.manufacturer, "Teltonika")
            self.assertEqual(asset_in_db.model, "FMB920")
            self.assertEqual(asset_in_db.protocol, "TELTONIKA_CODEC8")

            # -------------------------------------------------------------
            # CRITERION 4: Device appears in the hardware assets list
            # -------------------------------------------------------------
            devices_list = await HardwareService.list_devices(
                company_id=10,
                db=db,
                page=1,
                page_size=10
            )
            self.assertEqual(devices_list.total, 1, "Criterion 4 Failed: List total count mismatch")
            self.assertEqual(len(devices_list.items), 1)
            self.assertEqual(devices_list.items[0].imei, "359339075123456")
            self.assertEqual(devices_list.items[0].vehicle_registration, "RJ14UF0089")

            # -------------------------------------------------------------
            # CRITERION 5: Device status is correctly set to PENDING (NOT CONNECTED)
            # -------------------------------------------------------------
            self.assertEqual(
                devices_list.items[0].connection_status.upper(),
                "PENDING",
                "Criterion 5 Failed: Unactivated device must be PENDING, never marked CONNECTED"
            )
            self.assertNotEqual(
                devices_list.items[0].connection_status.upper(),
                "CONNECTED",
                "Criterion 5 Failed: Device falsely marked CONNECTED without receiving raw GPS frames"
            )

            # -------------------------------------------------------------
            # CRITERION 6: Device details page opens without crashing
            # -------------------------------------------------------------
            details = await HardwareService.get_device_by_id(company_id=10, asset_id=response.id, db=db)
            self.assertIsNotNone(details, "Criterion 6 Failed: Device details returned None")
            self.assertEqual(details.id, response.id)
            self.assertEqual(details.vehicle_registration, "RJ14UF0089")

            # -------------------------------------------------------------
            # CRITERION 7: Configuration snippet matches TELTONIKA_CODEC8
            # -------------------------------------------------------------
            self.assertEqual(details.protocol, "TELTONIKA_CODEC8", "Criterion 7 Failed: Protocol mismatch")
            self.assertIn("serverPort", details.connection_config)
            self.assertEqual(details.connection_config["serverPort"], 5027)

            # -------------------------------------------------------------
            # CRITERION 8: Server host and port are displayed correctly
            # -------------------------------------------------------------
            self.assertEqual(details.connection_config["serverHost"], "ingest.thevahan.com")
            self.assertEqual(details.connection_config["serverPort"], 5027)

            # -------------------------------------------------------------
            # CRITERION 9: Telematics stream displays awaiting data status
            # -------------------------------------------------------------
            self.assertIsNone(details.last_communication_at, "Criterion 9 Failed: New device must have no communication timestamp")
            self.assertIsNone(details.last_known_lat, "Criterion 9 Failed: Lat must be None prior to ingestion")
            self.assertIsNone(details.last_known_lng, "Criterion 9 Failed: Lng must be None prior to ingestion")
            self.assertTrue(details.is_stale, "Criterion 9 Failed: Device with no telemetry must be flagged stale/awaiting")

            # -------------------------------------------------------------
            # CRITERION 10: Hardware summary cards update correctly
            # -------------------------------------------------------------
            summary = await HardwareService.get_dashboard_summary(company_id=10, db=db)
            self.assertEqual(summary.total_devices, 1, "Criterion 10 Failed: Total devices must be 1")
            self.assertEqual(summary.connected_devices, 0, "Criterion 10 Failed: Connected devices must be 0")
            self.assertEqual(summary.pending_devices, 1, "Criterion 10 Failed: Pending devices must be 1")
            self.assertEqual(summary.vehicles_with_gps, 1, "Criterion 10 Failed: Vehicles with GPS must be 1")
            self.assertEqual(summary.vehicles_without_gps, 0, "Criterion 10 Failed: Vehicles without GPS must be 0")

            print("\n=======================================================")
            print("ALL 10 TASK 5 SYNTHETIC DEVICE VERIFICATION CRITERIA PASSED:")
            print("  1. Protocol Dropdown / Registry Loaded: OK")
            print("  2. Registration Payload Accepted (201 Created): OK")
            print("  3. Asset Database Record Created: OK (Business ID:", response.business_id, ")")
            print("  4. Device Appears in Hardware List: OK (RJ14UF0089)")
            print("  5. Device Status Set to PENDING (NOT Connected): OK")
            print("  6. Device Details Fetched Without Crash: OK")
            print("  7. Configuration Snippet Matches TELTONIKA_CODEC8: OK")
            print("  8. Server Host & Port Displayed: OK (ingest.thevahan.com:5027)")
            print("  9. Telematics Stream Displays Awaiting Data: OK")
            print(" 10. Hardware Summary Cards Reflect Exact Values: OK")
            print("=======================================================\n")


if __name__ == "__main__":
    unittest.main()
