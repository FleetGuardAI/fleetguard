"""
Unit & Integration Tests for GPS Provider Account Lifecycle & Schema Verification
Covers: Create, List, Test Connection, Sync, Error Handling, Delete, and Multi-tenant Isolation.
"""
import os
os.environ["TESTING"] = "True"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["SECRET_KEY"] = "production_audit_test_secret_key_12345"

import unittest
from unittest.mock import AsyncMock, patch
from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from database import Base
import models
from models.company import Company, CompanyStatus
from models.asset_domain import GPSProviderAccount
from schemas.asset_domain import GPSProviderAccountCreateRequest, GPSProviderAccountResponse
from services.hardware_service import HardwareService


class TestGPSProviderLifecycle(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)

        # Seed 2 distinct companies for isolation testing
        async with self.session_factory() as session:
            c1 = Company(id=1, company_name="Company One", owner_name="Owner One", mobile_number="+919000000001", email="c1@vahan.app", status=CompanyStatus.ACTIVE)
            c2 = Company(id=2, company_name="Company Two", owner_name="Owner Two", mobile_number="+919000000002", email="c2@vahan.app", status=CompanyStatus.ACTIVE)
            session.add_all([c1, c2])
            await session.commit()

    async def asyncTearDown(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await self.engine.dispose()

    async def test_full_provider_lifecycle(self):
        async with self.session_factory() as session:
            # 1. CREATE ACCOUNT
            payload = GPSProviderAccountCreateRequest(
                provider_type="traccar",
                name="HQ Primary Traccar",
                server_url="http://traccar.internal:8082",
                credentials="admin:SecretPassword123",
                config={"sync_interval_seconds": 60, "username": "admin"}
            )
            created = await HardwareService.create_provider_account(company_id=1, payload=payload, db=session)
            self.assertIsNotNone(created.id)
            self.assertEqual(created.name, "HQ Primary Traccar")
            self.assertEqual(created.provider_type, "traccar")
            self.assertEqual(created.sync_status, "CONNECTED")
            account_id = created.id

            # 2. LIST ACCOUNTS (Company 1 should see it, Company 2 should see empty list)
            c1_list = await HardwareService.list_provider_accounts(company_id=1, db=session)
            self.assertEqual(len(c1_list), 1)
            self.assertEqual(c1_list[0].id, account_id)
            
            c2_list = await HardwareService.list_provider_accounts(company_id=2, db=session)
            self.assertEqual(len(c2_list), 0, "Company 2 leaked Company 1 provider account!")

            # 3. TEST CONNECTION (Success case)
            with patch("services.traccar_service.TraccarService.test_connection", new_callable=AsyncMock) as mock_test:
                mock_test.return_value = (True, "Connected to Traccar v6.5", {"version": "6.5"})
                test_res = await HardwareService.test_provider_account(company_id=1, account_id=account_id, db=session)
                self.assertTrue(test_res.success)
                self.assertEqual(test_res.status, "CONNECTED")
                self.assertIn("v6.5", test_res.message)

            # 4. TEST CONNECTION (Failure case)
            with patch("services.traccar_service.TraccarService.test_connection", new_callable=AsyncMock) as mock_test:
                mock_test.return_value = (False, "Connection refused at http://traccar.internal:8082", {})
                fail_res = await HardwareService.test_provider_account(company_id=1, account_id=account_id, db=session)
                self.assertFalse(fail_res.success)
                self.assertEqual(fail_res.status, "ERROR")

                # Verify database state was updated to ERROR
                acct = await session.get(GPSProviderAccount, account_id)
                self.assertEqual(acct.sync_status, "ERROR")
                self.assertIn("Connection refused", acct.sync_error)

            # 5. SYNC DEVICES (Failure case handling)
            with patch("services.traccar_service.TraccarService.sync_devices_and_positions", new_callable=AsyncMock) as mock_sync:
                mock_sync.side_effect = RuntimeError("Traccar API timeout after 15s")
                sync_res = await HardwareService.sync_provider_account(company_id=1, account_id=account_id, db=session)
                self.assertIn("error", sync_res)
                
                acct = await session.get(GPSProviderAccount, account_id)
                self.assertEqual(acct.sync_status, "ERROR")
                self.assertIn("timeout", acct.sync_error)

            # 6. SYNC DEVICES (Success case)
            with patch("services.traccar_service.TraccarService.sync_devices_and_positions", new_callable=AsyncMock) as mock_sync:
                mock_sync.return_value = {"total_provider_devices": 5, "matched_vahan_assets": 5, "positions_updated": 5}
                sync_res = await HardwareService.sync_provider_account(company_id=1, account_id=account_id, db=session)
                self.assertEqual(sync_res["matched_vahan_assets"], 5)

            # 7. CROSS-TENANT ISOLATION CHECK
            with self.assertRaises(HTTPException) as ctx:
                await HardwareService.delete_provider_account(company_id=2, account_id=account_id, db=session)
            self.assertEqual(ctx.exception.status_code, 404, "Company 2 was able to access Company 1 account!")

            # 8. DELETE ACCOUNT
            del_res = await HardwareService.delete_provider_account(company_id=1, account_id=account_id, db=session)
            self.assertTrue(del_res["success"])

            # Verify deleted from database
            post_del = await HardwareService.list_provider_accounts(company_id=1, db=session)
            self.assertEqual(len(post_del), 0)


if __name__ == "__main__":
    unittest.main()
