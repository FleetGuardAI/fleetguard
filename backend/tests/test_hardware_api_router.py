import os
os.environ["TESTING"] = "True"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI
from datetime import datetime, timezone

from routers.asset_domain import router
from services.auth_service import get_current_user
from database import get_db
from models.user import User, UserRole
from schemas.asset_domain import (
    HardwareDashboardSummary,
    HardwareDeviceResponse,
    HardwareDeviceListResponse,
    DeviceTestConnectionResponse,
    DeviceLocationHistoryResponse,
    GPSProviderAccountResponse,
)

# Build a test FastAPI app mounting only the asset router
app = FastAPI()
app.include_router(router)

# Mock authenticated user
mock_user = User(
    id=1,
    company_id=10,
    email="admin@vahan.app",
    role=UserRole.COMPANY_ADMIN,
    is_active=True
)

app.dependency_overrides[get_current_user] = lambda: mock_user
app.dependency_overrides[get_db] = lambda: AsyncMock()

client = TestClient(app)


class TestHardwareAPIRouter(unittest.TestCase):
    @patch("services.hardware_service.HardwareService.get_dashboard_summary")
    def test_get_dashboard_summary_endpoint(self, mock_summary):
        mock_summary.return_value = HardwareDashboardSummary(
            total_devices=15,
            connected_devices=10,
            disconnected_devices=3,
            pending_devices=2,
            vehicles_with_gps=12,
            vehicles_without_gps=4
        )
        resp = client.get("/v1/assets/hardware/stats")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["total_devices"], 15)
        self.assertEqual(data["connected_devices"], 10)
        self.assertEqual(data["vehicles_with_gps"], 12)
        mock_summary.assert_called_once()
        self.assertEqual(mock_summary.call_args[0][0], 10)

    def test_get_protocols_registry_endpoint(self):
        resp = client.get("/v1/assets/hardware/protocols")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("protocols", data)
        self.assertIn("manufacturers", data)
        self.assertIn("TELTONIKA_CODEC8", [p["id"] for p in data["protocols"]])
        self.assertIn("GT06", [p["id"] for p in data["protocols"]])

    @patch("services.hardware_service.HardwareService.list_devices")
    def test_list_hardware_devices_endpoint(self, mock_list):
        mock_list.return_value = HardwareDeviceListResponse(
            total=1,
            items=[
                HardwareDeviceResponse(
                    id=1,
                    company_id=10,
                    business_id="HW-001",
                    device_name="Tracker 1",
                    asset_type="GPS_DEVICE",
                    manufacturer="Teltonika",
                    model="FMB920",
                    imei="865432019876543",
                    connection_type="DIRECT_HARDWARE",
                    connection_status="CONNECTED",
                    vehicle_registration="DL01AA1111",
                    installation_status="INSTALLED",
                    operational_status="OK",
                    offline_threshold_minutes=15,
                    is_stale=False,
                    history_records=[]
                )
            ],
            page=1,
            page_size=10,
            total_pages=1
        )
        resp = client.get("/v1/assets/hardware/devices?page=1&page_size=10")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["total"], 1)
        self.assertEqual(data["items"][0]["device_name"], "Tracker 1")
        self.assertEqual(mock_list.call_args[1]["company_id"], 10)

    @patch("services.hardware_service.HardwareService.register_device")
    def test_register_device_endpoint(self, mock_register):
        mock_register.return_value = HardwareDeviceResponse(
            id=99,
            company_id=10,
            business_id="HW-099",
            device_name="New Tracker",
            asset_type="GPS_DEVICE",
            manufacturer="Teltonika",
            model="FMB920",
            imei="865432019876543",
            connection_type="DIRECT_HARDWARE",
            connection_status="PENDING",
            installation_status="INSTALLED",
            operational_status="OK",
            offline_threshold_minutes=15,
            is_stale=True,
            history_records=[]
        )
        payload = {
            "device_name": "New Tracker",
            "connection_type": "DIRECT_HARDWARE",
            "manufacturer": "Teltonika",
            "model": "FMB920",
            "protocol": "TELTONIKA_CODEC8",
            "imei": "865432019876543",
            "vehicle_id": 1,
            "offline_threshold_minutes": 15
        }
        resp = client.post("/v1/assets/hardware/register", json=payload)
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertEqual(data["id"], 99)
        self.assertEqual(mock_register.call_args[0][0], 10)

    @patch("services.hardware_service.HardwareService.test_device_connection")
    def test_test_device_connection_endpoint(self, mock_test):
        mock_test.return_value = DeviceTestConnectionResponse(
            success=True,
            status="CONNECTED",
            message="Online",
            details={"latency_ms": 115}
        )
        resp = client.post("/v1/assets/hardware/devices/1/test-connection")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["status"], "CONNECTED")

    @patch("services.hardware_service.HardwareService.reassign_vehicle")
    def test_reassign_vehicle_endpoint(self, mock_reassign):
        mock_reassign.return_value = HardwareDeviceResponse(
            id=1,
            company_id=10,
            business_id="HW-001",
            device_name="Tracker 1",
            asset_type="GPS_DEVICE",
            connection_status="CONNECTED",
            current_vehicle_id=2,
            vehicle_registration="DL01BB2222",
            installation_status="INSTALLED",
            operational_status="OK",
            offline_threshold_minutes=15,
            is_stale=False
        )
        resp = client.post("/v1/assets/hardware/devices/1/reassign", json={"vehicle_id": 2, "force": True})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["current_vehicle_id"], 2)
        self.assertEqual(mock_reassign.call_args[0][0], 10)

    @patch("services.hardware_service.HardwareService.disconnect_device")
    def test_disconnect_device_endpoint(self, mock_disc):
        mock_disc.return_value = HardwareDeviceResponse(
            id=1,
            company_id=10,
            business_id="HW-001",
            device_name="Tracker 1",
            asset_type="GPS_DEVICE",
            connection_status="CONNECTED",
            current_vehicle_id=None,
            vehicle_registration=None,
            installation_status="IN_STORAGE",
            operational_status="OK",
            offline_threshold_minutes=15,
            is_stale=False
        )
        resp = client.post("/v1/assets/hardware/devices/1/disconnect")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIsNone(data["current_vehicle_id"])
        self.assertEqual(mock_disc.call_args[0][0], 10)

    @patch("services.hardware_service.HardwareService.remove_device")
    def test_remove_device_endpoint(self, mock_rem):
        mock_rem.return_value = {"success": True, "message": "Device retired"}
        resp = client.delete("/v1/assets/hardware/devices/1")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["success"])
        self.assertEqual(mock_rem.call_args[0][0], 10)

    @patch("services.hardware_service.HardwareService.get_device_location_history")
    def test_get_location_history_endpoint(self, mock_hist):
        mock_hist.return_value = DeviceLocationHistoryResponse(
            device_id=1,
            device_name="Tracker 1",
            total_points=2,
            distance_km=14.5,
            max_speed_kmh=65.0,
            avg_speed_kmh=42.0,
            points=[]
        )
        resp = client.get("/v1/assets/hardware/devices/1/locations")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["distance_km"], 14.5)
        self.assertEqual(mock_hist.call_args[1]["company_id"], 10)

    @patch("services.hardware_service.HardwareService.list_provider_accounts")
    def test_list_providers_endpoint(self, mock_provs):
        mock_provs.return_value = [
            GPSProviderAccountResponse(
                id=1,
                company_id=10,
                provider_type="traccar",
                name="Traccar Main",
                server_url="http://localhost:8082",
                sync_status="CONNECTED",
                device_count=5,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
        ]
        resp = client.get("/v1/assets/hardware/providers")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["name"], "Traccar Main")
        self.assertEqual(mock_provs.call_args[0][0], 10)

    @patch("services.hardware_service.HardwareService.list_quarantined_assets")
    def test_list_quarantined_assets_endpoint_authorized(self, mock_list):
        from models.admin_domain import AdminUser, AdminRole, AdminRoleType
        from services.admin_auth_service import get_current_admin
        from schemas.asset_domain import QuarantinedAssetItem

        admin_user = AdminUser(id=1, email="superadmin@vahan.com", is_active=True)
        admin_user.role = AdminRole(id=1, name=AdminRoleType.SUPER_ADMIN, description="Full Access")
        app.dependency_overrides[get_current_admin] = lambda: admin_user

        mock_list.return_value = [
            QuarantinedAssetItem(
                id=99,
                business_id="HW-QUAR-99",
                device_name="Orphaned GT06",
                imei="860123456789012",
                manufacturer="Concox",
                model="GT06",
                protocol="GT06",
                connection_status="DISCONNECTED",
                created_at=datetime.now(timezone.utc),
                quarantine_company_id=1
            )
        ]

        resp = client.get("/v1/admin/hardware/quarantined-assets")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["business_id"], "HW-QUAR-99")
        app.dependency_overrides.pop(get_current_admin, None)

    @patch("services.hardware_service.HardwareService.reassign_quarantined_asset")
    def test_reassign_quarantined_asset_endpoint_authorized(self, mock_reassign):
        from models.admin_domain import AdminUser, AdminRole, AdminRoleType
        from services.admin_auth_service import get_current_admin

        admin_user = AdminUser(id=1, email="superadmin@vahan.com", is_active=True)
        admin_user.role = AdminRole(id=1, name=AdminRoleType.SUPER_ADMIN, description="Full Access")
        app.dependency_overrides[get_current_admin] = lambda: admin_user

        mock_reassign.return_value = HardwareDeviceResponse(
            id=99,
            company_id=10,
            business_id="HW-QUAR-99",
            device_name="Reassigned GT06",
            imei="860123456789012",
            manufacturer="Concox",
            connection_status="DISCONNECTED",
            installation_status="IN_STORAGE",
            created_at=datetime.now(timezone.utc)
        )

        resp = client.post(
            "/v1/admin/hardware/quarantined-assets/99/reassign",
            json={
                "target_company_id": 10,
                "reason": "Reassigned following contract verification"
            }
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["company_id"], 10)
        app.dependency_overrides.pop(get_current_admin, None)

    def test_quarantined_assets_endpoint_unauthorized_for_anonymous_or_ordinary(self):
        # Without admin override, should return 401 Unauthorized
        resp = client.get("/v1/admin/hardware/quarantined-assets")
        self.assertEqual(resp.status_code, 401)


if __name__ == "__main__":
    unittest.main()
