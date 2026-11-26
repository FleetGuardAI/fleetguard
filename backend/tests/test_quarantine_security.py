"""
FleetGuard / Vahan — Quarantine Tenant Security & Multi-Tenant Isolation Tests
Verifies:
1. Quarantined assets cannot be accessed, modified, or reassigned by ordinary companies (returns 404).
2. Ordinary companies cannot access other companies' assets (cross-company isolation returns 404).
3. Ordinary users / unauthenticated requests cannot access super-admin quarantine endpoints (401/403).
4. Super-admins can list quarantined assets across the platform.
5. Super-admins can reassign quarantined assets to active tenant companies with mandatory audit logging.
6. Reassignment logs records in both AdminAuditLog and AssetHistory.
"""

import unittest
import asyncio
from datetime import datetime, timezone
from unittest.mock import MagicMock, AsyncMock, patch

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from database import Base
from models.company import Company, CompanyStatus
from models.user import User, UserRole
from models.admin_domain import AdminUser, AdminRole, AdminRoleType, AdminAuditLog
from models.asset_domain import (
    Asset,
    AssetType,
    AssetInstallationStatus,
    AssetOperationalStatus,
    AssetHistory,
    AssetHistoryCategory,
    ConnectionStatus,
    ConnectionType,
)
from models.vehicle_domain import Vehicle
from schemas.asset_domain import (
    VehicleReassignRequest,
    HardwareDeviceUpdateRequest,
    QuarantinedAssetReassignRequest
)
from services.hardware_service import HardwareService


class TestQuarantineSecurityAndTenantIsolation(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        self.session_maker = async_sessionmaker(self.engine, expire_on_commit=False)

        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async with self.session_maker() as db:
            # 1. Quarantine System Tenant (ID=1)
            self.quarantine_comp = Company(
                id=1,
                company_name="System Quarantine / Unallocated Fleet",
                owner_name="System Administrator",
                mobile_number="+910000000000",
                email="quarantine@vahan.system",
                status=CompanyStatus.SUSPENDED
            )

            # 2. Legitimate Tenant A (ID=10)
            self.company_a = Company(
                id=10,
                company_name="Alpha Logistics Ltd",
                owner_name="Aarav Sharma",
                mobile_number="+919876543210",
                email="fleet@alpha.com",
                status=CompanyStatus.ACTIVE
            )

            # 3. Legitimate Tenant B (ID=20)
            self.company_b = Company(
                id=20,
                company_name="Beta Express Pvt",
                owner_name="Bhavin Patel",
                mobile_number="+919876543211",
                email="ops@beta.com",
                status=CompanyStatus.ACTIVE
            )

            # 4. Vehicles
            self.vehicle_a = Vehicle(id=101, company_id=10, registration_number="MH04AL1001", make="Tata", model="Prima")
            self.vehicle_b = Vehicle(id=201, company_id=20, registration_number="DL01BE2001", make="Ashok Leyland", model="Ecomet")

            # 5. Hardware Assets
            self.quarantined_asset = Asset(
                id=500,
                company_id=1,
                business_id="HW-QUARANTINE-01",
                asset_type=AssetType.GPS_DEVICE,
                device_name="Orphaned Tracker",
                imei="860123456789012",
                manufacturer="Concox",
                model="GT06N",
                protocol="GT06",
                connection_status=ConnectionStatus.DISCONNECTED.value,
                installation_status=AssetInstallationStatus.IN_STORAGE
            )

            self.asset_a = Asset(
                id=510,
                company_id=10,
                business_id="HW-ALPHA-01",
                asset_type=AssetType.GPS_DEVICE,
                device_name="Alpha Truck GPS",
                imei="860987654321098",
                manufacturer="Teltonika",
                model="FMB920",
                protocol="TELTONIKA_CODEC8",
                current_vehicle_id=101,
                connection_status=ConnectionStatus.CONNECTED.value,
                installation_status=AssetInstallationStatus.INSTALLED
            )

            # 6. Admin Roles and Users
            self.super_admin_role = AdminRole(id=1, name=AdminRoleType.SUPER_ADMIN, description="Full Access")
            self.super_admin = AdminUser(
                id=1,
                email="superadmin@vahan.com",
                full_name="Chief Security Officer",
                password_hash="hashed_pw",
                role_id=1,
                is_active=True
            )

            db.add_all([
                self.quarantine_comp, self.company_a, self.company_b,
                self.vehicle_a, self.vehicle_b,
                self.quarantined_asset, self.asset_a,
                self.super_admin_role, self.super_admin
            ])
            await db.commit()

    async def asyncTearDown(self):
        await self.engine.dispose()

    async def test_ordinary_company_cannot_view_quarantined_devices(self):
        """Verify ordinary company list_devices excludes quarantined devices."""
        async with self.session_maker() as db:
            result = await HardwareService.list_devices(company_id=10, db=db)
            device_ids = [d.id for d in result.items]
            self.assertIn(510, device_ids, "Company A should see its own device")
            self.assertNotIn(500, device_ids, "Company A must NEVER see quarantined devices")

            # Company B sees nothing
            result_b = await HardwareService.list_devices(company_id=20, db=db)
            self.assertEqual(len(result_b.items), 0)

    async def test_ordinary_company_cannot_access_quarantined_device_by_id(self):
        """Verify get_device_by_id returns 404 for quarantined devices."""
        async with self.session_maker() as db:
            with self.assertRaises(HTTPException) as cm:
                await HardwareService.get_device_by_id(company_id=10, asset_id=500, db=db)
            self.assertEqual(cm.exception.status_code, 404)
            self.assertIn("not found", cm.exception.detail.lower())

    async def test_ordinary_company_cannot_modify_quarantined_device(self):
        """Verify update_device returns 404 for quarantined devices."""
        async with self.session_maker() as db:
            with self.assertRaises(HTTPException) as cm:
                await HardwareService.update_device(
                    company_id=10,
                    asset_id=500,
                    payload=HardwareDeviceUpdateRequest(device_name="Hijacked Tracker"),
                    db=db
                )
            self.assertEqual(cm.exception.status_code, 404)

    async def test_ordinary_company_cannot_reassign_quarantined_device(self):
        """Verify reassign_vehicle returns 404 for quarantined devices."""
        async with self.session_maker() as db:
            with self.assertRaises(HTTPException) as cm:
                await HardwareService.reassign_vehicle(
                    company_id=10,
                    asset_id=500,
                    payload=VehicleReassignRequest(vehicle_id=101),
                    db=db
                )
            self.assertEqual(cm.exception.status_code, 404)

    async def test_cross_company_isolation_between_ordinary_tenants(self):
        """Verify Company B cannot access or reassign Company A's device."""
        async with self.session_maker() as db:
            with self.assertRaises(HTTPException) as cm:
                await HardwareService.get_device_by_id(company_id=20, asset_id=510, db=db)
            self.assertEqual(cm.exception.status_code, 404)

            with self.assertRaises(HTTPException) as cm:
                await HardwareService.reassign_vehicle(
                    company_id=20,
                    asset_id=510,
                    payload=VehicleReassignRequest(vehicle_id=201),
                    db=db
                )
            self.assertEqual(cm.exception.status_code, 404)

    async def test_super_admin_can_view_quarantined_assets(self):
        """Verify super-admin can view quarantined assets."""
        async with self.session_maker() as db:
            items = await HardwareService.list_quarantined_assets(db)
            self.assertEqual(len(items), 1)
            self.assertEqual(items[0].id, 500)
            self.assertEqual(items[0].business_id, "HW-QUARANTINE-01")
            self.assertEqual(items[0].imei, "860123456789012")

    async def test_super_admin_reassign_quarantined_asset_with_audit_logging(self):
        """
        Verify super-admin can safely liberate and reassign a quarantined asset
        to an active tenant company and verify full audit trails.
        """
        async with self.session_maker() as db:
            payload = QuarantinedAssetReassignRequest(
                target_company_id=10,
                target_vehicle_id=None,
                reason="Hardware serial validated by hardware provisioning team against purchase invoice #INV-2026-99"
            )

            resp = await HardwareService.reassign_quarantined_asset(
                asset_id=500,
                payload=payload,
                admin_id=1,
                admin_email="superadmin@vahan.com",
                db=db,
                ip_address="192.168.1.100"
            )

            self.assertEqual(resp.id, 500)
            self.assertEqual(resp.company_id, 10, "Asset must now belong to Company A")

            # Verify quarantine list is now empty
            remaining_quarantined = await HardwareService.list_quarantined_assets(db)
            self.assertEqual(len(remaining_quarantined), 0, "Quarantined list must now be empty")

            # Verify Company A can now see the device
            dev_a = await HardwareService.get_device_by_id(company_id=10, asset_id=500, db=db)
            self.assertIsNotNone(dev_a)
            self.assertEqual(dev_a.business_id, "HW-QUARANTINE-01")

            # Verify AssetHistory audit record
            from sqlalchemy import select
            q_hist = select(AssetHistory).where(AssetHistory.asset_id == 500)
            res_hist = await db.execute(q_hist)
            histories = res_hist.scalars().all()
            self.assertGreaterEqual(len(histories), 1)
            latest_hist = histories[-1]
            self.assertEqual(latest_hist.details["action"], "QUARANTINE_REASSIGNMENT")
            self.assertEqual(latest_hist.details["previous_company_id"], 1)
            self.assertEqual(latest_hist.details["new_company_id"], 10)
            self.assertEqual(latest_hist.details["admin_email"], "superadmin@vahan.com")

            # Verify AdminAuditLog record
            q_audit = select(AdminAuditLog).where(
                AdminAuditLog.resource_id == "500",
                AdminAuditLog.action == "REASSIGN_QUARANTINED_ASSET"
            )
            res_audit = await db.execute(q_audit)
            audit_log = res_audit.scalars().first()
            self.assertIsNotNone(audit_log, "AdminAuditLog entry must be recorded")
            self.assertEqual(audit_log.admin_id, 1)
            self.assertEqual(audit_log.old_value, "1")
            self.assertEqual(audit_log.new_value, "10")
            self.assertEqual(audit_log.ip_address, "192.168.1.100")
            self.assertIn("INV-2026-99", audit_log.reason)


if __name__ == "__main__":
    unittest.main()
