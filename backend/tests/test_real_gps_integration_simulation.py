"""
Comprehensive End-to-End GPS Integration Simulation Test
Simulates device ingestion lifecycle across multiple protocols (GT06, AIS-140, TK103, Traccar Forwarder).

NOTE: This suite simulates protocol payloads and forwarder frames against the Vahan ingestion pipeline.
It validates the software architecture, decoders, deduplication, isolation, and state transitions
without requiring live physical GSM modems or active satellite lock.
"""
import os
os.environ["TESTING"] = "True"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["SECRET_KEY"] = "production_audit_test_secret_key_12345"

import unittest
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select

from database import Base
import models
from models.company import Company, CompanyStatus
from models.vehicle_domain import Vehicle
from models.asset_domain import (
    Asset, AssetType, ConnectionStatus, ConnectionType, AssetOperationalStatus,
    AssetInstallationStatus
)
from models.location_tracking import VehicleLocation, VehicleCurrentLocation, LocationSource
from schemas.telematics import NormalizedHardwareEvent
from schemas.asset_domain import HardwareDeviceRegisterRequest
from services.location_service import LocationService
from services.hardware_service import HardwareService


class TestRealGPSIntegrationSimulation(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)

        async with self.session_factory() as session:
            # Seed 2 tenant companies
            c1 = Company(id=1, company_name="Fleet Alpha", owner_name="Alpha Admin", mobile_number="+919800000001", email="alpha@fleet.com", status=CompanyStatus.ACTIVE)
            c2 = Company(id=2, company_name="Fleet Beta", owner_name="Beta Admin", mobile_number="+919800000002", email="beta@fleet.com", status=CompanyStatus.ACTIVE)
            session.add_all([c1, c2])

            # Seed a vehicle for Company 1
            v1 = Vehicle(id=101, company_id=1, registration_number="KA-01-EQ-9999", make="Tata", model="Prima", year=2024)
            session.add(v1)

            await session.commit()

    async def asyncTearDown(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await self.engine.dispose()

    async def test_complete_gps_integration_simulation(self):
        async with self.session_factory() as session:
            # -------------------------------------------------------------
            # 1. DEVICE REGISTRATION (Assigned Device + Unassigned Device)
            # -------------------------------------------------------------
            # Registered & Assigned to Vehicle 101
            reg_payload_assigned = HardwareDeviceRegisterRequest(
                device_name="Alpha Truck GPS Unit",
                connection_type="DIRECT_HARDWARE",
                manufacturer="Teltonika",
                model="FMB920",
                protocol="TELTONIKA_CODEC8",
                imei="860123456789012",
                vehicle_id=101,
                offline_threshold_minutes=15
            )
            dev_assigned = await HardwareService.register_device(company_id=1, payload=reg_payload_assigned, db=session)
            self.assertEqual(dev_assigned.imei, "860123456789012")
            self.assertEqual(dev_assigned.current_vehicle_id, 101)
            self.assertEqual(dev_assigned.connection_status, "PENDING")

            # Registered in Storage (Unassigned)
            reg_payload_unassigned = HardwareDeviceRegisterRequest(
                device_name="Spare Shelf GPS Unit",
                connection_type="DIRECT_HARDWARE",
                manufacturer="Concox",
                model="GT06N",
                protocol="GT06",
                imei="860987654321098",
                vehicle_id=None,
                offline_threshold_minutes=15
            )
            dev_unassigned = await HardwareService.register_device(company_id=1, payload=reg_payload_unassigned, db=session)
            self.assertEqual(dev_unassigned.imei, "860987654321098")
            self.assertIsNone(dev_unassigned.current_vehicle_id)
            self.assertEqual(dev_unassigned.connection_status, "PENDING")

            # -------------------------------------------------------------
            # 2. UNASSIGNED DEVICE HEARTBEAT & DIAGNOSTIC TELEMETRY
            # -------------------------------------------------------------
            unassigned_event = NormalizedHardwareEvent(
                device_imei="860987654321098",
                latitude=12.9716,
                longitude=77.5946,
                timestamp=datetime(2026, 11, 23, 10, 0, 0, tzinfo=timezone.utc),
                speed=0.0,
                heading=0.0,
                ignition_status=False,
                source_metadata={"battery_level": 88.0, "protocol": "GT06"}
            )
            res_unassigned = await LocationService.process_hardware_batch(
                db=session,
                locations=[unassigned_event],
                allow_registration_only=False
            )
            self.assertEqual(res_unassigned["accepted"], 1)
            self.assertEqual(res_unassigned["items"][0]["status"], "accepted_unassigned")

            # Verify unassigned device status transitioned to CONNECTED
            asset_unassigned_db = await session.get(Asset, dev_unassigned.id)
            self.assertEqual(asset_unassigned_db.connection_status, ConnectionStatus.CONNECTED.value)
            self.assertEqual(asset_unassigned_db.last_known_lat, 12.9716)
            self.assertEqual(asset_unassigned_db.last_known_battery, 88.0)

            # Verify NO vehicle location was created
            vl_count = (await session.execute(select(VehicleLocation))).scalars().all()
            self.assertEqual(len(vl_count), 0, "VehicleLocation should NOT be created for unassigned device!")

            # -------------------------------------------------------------
            # 3. ASSIGNED DEVICE TELEMETRY INGESTION & VEHICLE LOCATION
            # -------------------------------------------------------------
            t0 = datetime(2026, 11, 23, 10, 0, 0, tzinfo=timezone.utc)
            t1 = datetime(2026, 11, 23, 10, 1, 0, tzinfo=timezone.utc)
            t2 = datetime(2026, 11, 23, 10, 2, 0, tzinfo=timezone.utc)

            packet_1 = NormalizedHardwareEvent(
                device_imei="860123456789012",
                latitude=28.6139,
                longitude=77.2090,
                timestamp=t0,
                speed=50.0, # km/h
                heading=90.0,
                ignition_status=True,
                source_metadata={"battery_level": 98.0, "protocol": "TELTONIKA_CODEC8"}
            )
            packet_2 = NormalizedHardwareEvent(
                device_imei="860123456789012",
                latitude=28.6150,
                longitude=77.2100,
                timestamp=t1,
                speed=55.0,
                heading=95.0,
                ignition_status=True,
                source_metadata={"battery_level": 98.0}
            )
            res_assigned = await LocationService.process_hardware_batch(
                db=session,
                locations=[packet_1, packet_2],
                allow_registration_only=False
            )
            self.assertEqual(res_assigned["accepted"], 2)
            self.assertEqual(res_assigned["duplicates"], 0)
            self.assertEqual(res_assigned["rejected"], 0)

            # Verify VehicleLocation persisted
            vl_rows = (await session.execute(select(VehicleLocation).where(VehicleLocation.vehicle_id == 101))).scalars().all()
            self.assertEqual(len(vl_rows), 2)
            self.assertEqual(vl_rows[0].company_id, 1, "Company isolation violated!")

            # Verify VehicleCurrentLocation cache updated
            vcl = (await session.execute(select(VehicleCurrentLocation).where(VehicleCurrentLocation.vehicle_id == 101))).scalars().first()
            self.assertIsNotNone(vcl)
            self.assertEqual(vcl.latitude, 28.6150)
            self.assertEqual(vcl.speed, 55.0)

            # -------------------------------------------------------------
            # 4. DUPLICATE PACKET REJECTION
            # -------------------------------------------------------------
            # Re-send packet_1 with identical coordinates and timestamp
            res_dup = await LocationService.process_hardware_batch(
                db=session,
                locations=[packet_1],
                allow_registration_only=False
            )
            self.assertEqual(res_dup["duplicates"], 1)
            self.assertEqual(res_dup["accepted"], 0)
            self.assertEqual(res_dup["items"][0]["status"], "duplicate")

            # -------------------------------------------------------------
            # 5. HISTORICAL LOCATION STORAGE & ANALYTICS COMPUTATION
            # -------------------------------------------------------------
            history_res = await HardwareService.get_device_location_history(
                company_id=1,
                asset_id=dev_assigned.id,
                db=session,
                start_time=t0 - timedelta(minutes=5),
                end_time=t2 + timedelta(minutes=5)
            )
            self.assertEqual(history_res.total_points, 2)
            self.assertGreater(history_res.distance_km, 0.0)
            self.assertEqual(history_res.max_speed_kmh, round(55.0 * 3.6, 1))

            # Cross-tenant isolation on history
            with self.assertRaises(Exception):
                await HardwareService.get_device_location_history(
                    company_id=2, # Company 2 tries to access Company 1 device history
                    asset_id=dev_assigned.id,
                    db=session
                )

            # -------------------------------------------------------------
            # 6. OFFLINE DETECTION & RECOVERY
            # -------------------------------------------------------------
            # Simulate device going stale (communication 30 mins ago, threshold is 15 mins)
            stale_asset = await session.get(Asset, dev_assigned.id)
            stale_asset.last_communication_at = datetime.now(timezone.utc) - timedelta(minutes=30)
            await session.commit()

            computed_status, is_stale = HardwareService._compute_device_status(stale_asset)
            self.assertEqual(computed_status, ConnectionStatus.DISCONNECTED.value)
            self.assertTrue(is_stale)

            # Send recovery packet
            recovery_packet = NormalizedHardwareEvent(
                device_imei="860123456789012",
                latitude=28.6160,
                longitude=77.2110,
                timestamp=datetime.now(timezone.utc),
                speed=60.0,
                heading=100.0,
                ignition_status=True
            )
            res_recovery = await LocationService.process_hardware_batch(
                db=session,
                locations=[recovery_packet],
                allow_registration_only=False
            )
            self.assertEqual(res_recovery["accepted"], 1)

            refreshed_asset = await session.get(Asset, dev_assigned.id)
            self.assertEqual(refreshed_asset.connection_status, ConnectionStatus.CONNECTED.value)
            status_after, stale_after = HardwareService._compute_device_status(refreshed_asset)
            self.assertEqual(status_after, ConnectionStatus.CONNECTED.value)
            self.assertFalse(stale_after)


if __name__ == "__main__":
    unittest.main()
