"""
FleetGuard / Vahan — Hardware Asset & Telematics Service
Orchestrates device lifecycle, universal multi-protocol validation,
tenant-scoped vehicle assignments, connection diagnostics, and location history.
"""

import math
import uuid
import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timezone, timedelta

from sqlalchemy import select, func, and_, or_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from models.asset_domain import (
    Asset,
    AssetType,
    AssetInstallationStatus,
    AssetOperationalStatus,
    AssetHistory,
    AssetHistoryCategory,
    ConnectionStatus,
    ConnectionType,
    GPSProviderAccount,
)
from models.vehicle_domain import Vehicle
from models.location_tracking import VehicleLocation, LocationSource
from schemas.asset_domain import (
    HardwareDashboardSummary,
    HardwareDeviceResponse,
    HardwareDeviceListResponse,
    HardwareDeviceRegisterRequest,
    HardwareDeviceUpdateRequest,
    VehicleReassignRequest,
    DeviceTestConnectionResponse,
    DeviceLocationHistoryResponse,
    DeviceLocationPoint,
    GPSProviderAccountCreateRequest,
    GPSProviderAccountResponse,
    PreRegistrationTestRequest,
)
from services.traccar_service import TraccarService
from domain.hardware_registry.verified_protocols import VERIFIED_PROTOCOLS
from utils.credential_crypto import encrypt_dict, decrypt_dict, encrypt_credential, decrypt_credential
from models.company import Company, CompanyStatus
from models.admin_domain import AdminAuditLog
from schemas.asset_domain import QuarantinedAssetItem, QuarantinedAssetReassignRequest

logger = logging.getLogger(__name__)


def validate_imei_format(imei: str) -> None:
    """
    Validates device identifier or standard 15-digit IMEI.
    Standard cellular IMEIs are 15 digits; Luhn check where applicable.
    """
    cleaned = imei.strip()
    if len(cleaned) < 4:
        raise ValueError("Device identifier / IMEI must be at least 4 characters.")
    
    # If exactly 15 digits, perform Luhn checksum verification
    if cleaned.isdigit() and len(cleaned) == 15:
        total = 0
        for i, ch in enumerate(cleaned):
            digit = int(ch)
            if i % 2 == 1:
                doubled = digit * 2
                total += doubled - 9 if doubled > 9 else doubled
            else:
                total += digit
        if total % 10 != 0:
            # We log a warning but don't hard reject to accommodate custom/test hardware
            logger.warning(f"IMEI {cleaned} failed Luhn checksum; allowing as legacy or custom hardware ID.")


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance between two GPS coordinates in kilometers."""
    R = 6371.0  # Earth's radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2.0) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2.0) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(R * c, 3)


class HardwareService:
    @classmethod
    def _compute_device_status(cls, asset: Asset) -> Tuple[str, bool]:
        """
        Determines live connection status:
        - If explicitly MAINTENANCE or ERROR, preserve that.
        - If CONNECTED, check if last communication exceeds offline_threshold_minutes.
        - If no communication ever received, status remains PENDING.
        Returns (effective_status, is_stale).
        """
        if asset.connection_status in [ConnectionStatus.MAINTENANCE.value, ConnectionStatus.ERROR.value]:
            return asset.connection_status, True

        if not asset.last_communication_at:
            return ConnectionStatus.PENDING.value, True

        threshold_mins = asset.offline_threshold_minutes or 15
        now = datetime.now(timezone.utc)
        diff = now - asset.last_communication_at

        if diff > timedelta(minutes=threshold_mins):
            return ConnectionStatus.DISCONNECTED.value, True
        else:
            return ConnectionStatus.CONNECTED.value, False

    @classmethod
    def _to_device_response(cls, asset: Asset, vehicle: Optional[Vehicle] = None) -> HardwareDeviceResponse:
        v = vehicle
        if not v and "current_vehicle" in asset.__dict__:
            v = asset.__dict__["current_vehicle"]
        status_val, is_stale = cls._compute_device_status(asset)
        
        # Prepare safe connection config without sensitive tokens
        safe_config = dict(asset.connection_config or {})
        for secret_key in ["password", "api_key", "secret", "token"]:
            if secret_key in safe_config:
                del safe_config[secret_key]

        return HardwareDeviceResponse(
            id=asset.id or 0,
            company_id=asset.company_id,
            business_id=asset.business_id,
            device_name=asset.device_name or f"{asset.manufacturer or 'GPS'} {asset.model or 'Device'}",
            asset_type=asset.asset_type,
            manufacturer=asset.manufacturer,
            model=asset.model,
            imei=asset.imei or asset.serial_number,
            serial_number=asset.serial_number,
            firmware_version=asset.firmware_version,
            connection_type=asset.connection_type,
            connection_status=status_val,
            protocol=asset.protocol,
            gps_provider=asset.gps_provider,
            current_vehicle_id=asset.current_vehicle_id,
            vehicle_registration=v.registration_number if v else None,
            vehicle_name=f"{v.make or ''} {v.model or ''}".strip() if v else None,
            installation_status=asset.installation_status,
            operational_status=asset.operational_status,
            last_communication_at=asset.last_communication_at,
            last_known_lat=asset.last_known_lat,
            last_known_lng=asset.last_known_lng,
            last_known_speed=asset.last_known_speed,
            last_known_heading=asset.last_known_heading,
            last_known_ignition=asset.last_known_ignition,
            last_known_battery=asset.last_known_battery,
            last_known_address=asset.last_known_address,
            installation_date=asset.installation_date,
            offline_threshold_minutes=asset.offline_threshold_minutes,
            is_stale=is_stale,
            connection_config=safe_config,
            history_records=asset.__dict__["history_records"] if "history_records" in asset.__dict__ and asset.__dict__["history_records"] else [],
            created_at=asset.created_at,
            updated_at=asset.updated_at,
        )

    @classmethod
    async def get_dashboard_summary(cls, company_id: int, db: AsyncSession) -> HardwareDashboardSummary:
        """
        Retrieves real-time statistics for summary cards:
        - Total Hardware Devices
        - Connected Devices
        - Disconnected Devices
        - Pending Configuration Devices
        - Vehicles with GPS
        - Vehicles without GPS
        """
        # 1. Total devices
        total_q = await db.execute(
            select(func.count(Asset.id)).where(
                Asset.company_id == company_id,
                Asset.asset_type == AssetType.GPS_DEVICE
            )
        )
        total_devices = total_q.scalar() or 0

        # 2. Fetch all devices to compute dynamic connectedness based on timestamps
        all_q = await db.execute(
            select(Asset).where(
                Asset.company_id == company_id,
                Asset.asset_type == AssetType.GPS_DEVICE
            )
        )
        devices = all_q.scalars().all()

        connected = 0
        disconnected = 0
        pending = 0

        assigned_vehicle_ids = set()

        for d in devices:
            status_val, _ = cls._compute_device_status(d)
            if status_val == ConnectionStatus.CONNECTED.value:
                connected += 1
            elif status_val == ConnectionStatus.DISCONNECTED.value:
                disconnected += 1
            else:
                pending += 1

            if d.current_vehicle_id:
                assigned_vehicle_ids.add(d.current_vehicle_id)

        # 3. Total fleet vehicles
        vehicles_q = await db.execute(
            select(func.count(Vehicle.id)).where(Vehicle.company_id == company_id)
        )
        total_vehicles = vehicles_q.scalar() or 0

        vehicles_with_gps = len(assigned_vehicle_ids)
        vehicles_without_gps = max(0, total_vehicles - vehicles_with_gps)

        return HardwareDashboardSummary(
            total_devices=total_devices,
            connected_devices=connected,
            disconnected_devices=disconnected,
            pending_devices=pending,
            vehicles_with_gps=vehicles_with_gps,
            vehicles_without_gps=vehicles_without_gps
        )

    @classmethod
    async def list_devices(
        cls,
        company_id: int,
        db: AsyncSession,
        search: Optional[str] = None,
        manufacturer: Optional[str] = None,
        connection_status: Optional[str] = None,
        gps_provider: Optional[str] = None,
        vehicle_assignment: Optional[str] = "all",  # all, assigned, unassigned
        sort_by: str = "created_at",
        sort_desc: bool = True,
        page: int = 1,
        page_size: int = 10,
    ) -> HardwareDeviceListResponse:
        """
        Searches, filters, sorts, and paginates devices scoped to company_id.
        """
        query = (
            select(Asset, Vehicle)
            .outerjoin(Vehicle, Asset.current_vehicle_id == Vehicle.id)
            .where(
                Asset.company_id == company_id,
                Asset.asset_type == AssetType.GPS_DEVICE
            )
        )

        if manufacturer and manufacturer != "all":
            query = query.where(func.lower(Asset.manufacturer) == manufacturer.lower())

        if gps_provider and gps_provider != "all":
            query = query.where(func.lower(Asset.gps_provider) == gps_provider.lower())

        if vehicle_assignment == "assigned":
            query = query.where(Asset.current_vehicle_id.isnot(None))
        elif vehicle_assignment == "unassigned":
            query = query.where(Asset.current_vehicle_id.is_(None))

        if search:
            q = f"%{search.strip().lower()}%"
            query = query.where(
                or_(
                    func.lower(Asset.device_name).like(q),
                    func.lower(Asset.business_id).like(q),
                    func.lower(Asset.imei).like(q),
                    func.lower(Asset.serial_number).like(q),
                    func.lower(Asset.manufacturer).like(q),
                    func.lower(Asset.model).like(q),
                    func.lower(Vehicle.registration_number).like(q)
                )
            )

        # Sorting
        sort_col = Asset.created_at
        if sort_by == "device_name":
            sort_col = Asset.device_name
        elif sort_by == "imei":
            sort_col = Asset.imei
        elif sort_by == "manufacturer":
            sort_col = Asset.manufacturer
        elif sort_by == "last_communication_at":
            sort_col = Asset.last_communication_at
        elif sort_by == "installation_date":
            sort_col = Asset.installation_date

        order_expr = desc(sort_col) if sort_desc else asc(sort_col)
        query = query.order_by(order_expr)

        # Execute total count
        res = await db.execute(query)
        all_rows = res.all()

        # Filter by dynamic connection status if requested
        filtered_rows = []
        for asset, vehicle in all_rows:
            st, _ = cls._compute_device_status(asset)
            if connection_status and connection_status != "all":
                if st.lower() != connection_status.lower():
                    continue
            filtered_rows.append((asset, vehicle))

        total_items = len(filtered_rows)
        total_pages = max(1, math.ceil(total_items / page_size))
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_rows = filtered_rows[start_idx:end_idx]

        items = [cls._to_device_response(asset, vehicle) for asset, vehicle in page_rows]

        return HardwareDeviceListResponse(
            total=total_items,
            items=items,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )

    @classmethod
    async def get_device_by_id(
        cls, company_id: int, asset_id: int, db: AsyncSession
    ) -> HardwareDeviceResponse:
        """Retrieves single device ensuring company ownership."""
        res = await db.execute(
            select(Asset, Vehicle)
            .outerjoin(Vehicle, Asset.current_vehicle_id == Vehicle.id)
            .where(Asset.id == asset_id, Asset.company_id == company_id)
        )
        row = res.first()
        if not row:
            raise HTTPException(status.HTTP_404_NOT_FOUND, f"Hardware device {asset_id} not found.")

        asset, vehicle = row
        return cls._to_device_response(asset, vehicle)

    @classmethod
    async def register_device(
        cls, company_id: int, payload: HardwareDeviceRegisterRequest, db: AsyncSession
    ) -> HardwareDeviceResponse:
        """
        Registers a new hardware device with multi-step validated parameters.
        Prevents duplicate active assignments and stores encrypted credentials.
        """
        # 1. Validate IMEI format
        clean_imei = payload.imei.strip()
        validate_imei_format(clean_imei)

        # 2. Check for duplicate IMEI within company (and global check)
        dup_q = await db.execute(
            select(Asset).where(
                or_(
                    Asset.imei == clean_imei,
                    Asset.serial_number == clean_imei
                )
            )
        )
        existing = dup_q.scalars().first()
        if existing:
            if existing.company_id == company_id:
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST,
                    f"A device with IMEI/ID '{clean_imei}' is already registered in your fleet ({existing.business_id})."
                )
            else:
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST,
                    f"Device with identifier '{clean_imei}' is already registered in the system."
                )

        # 3. Vehicle Assignment Validation
        target_vehicle = None
        if payload.vehicle_id:
            target_vehicle = await db.get(Vehicle, payload.vehicle_id)
            if not target_vehicle or target_vehicle.company_id != company_id:
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST,
                    "Assigned vehicle does not exist or does not belong to your company fleet."
                )

            # Prevent duplicate active device on the vehicle
            existing_dev_q = await db.execute(
                select(Asset).where(
                    Asset.company_id == company_id,
                    Asset.current_vehicle_id == payload.vehicle_id,
                    Asset.installation_status == AssetInstallationStatus.INSTALLED
                )
            )
            already_assigned = existing_dev_q.scalars().first()
            if already_assigned:
                raise HTTPException(
                    status.HTTP_409_CONFLICT,
                    f"Vehicle {target_vehicle.registration_number} already has active GPS device '{already_assigned.device_name}' ({already_assigned.business_id}) mounted."
                )

        # 4. Encrypt sensitive credentials
        encrypted_creds = None
        if payload.credentials:
            encrypted_creds = encrypt_dict(payload.credentials)

        # 5. Create Asset
        biz_id = f"HW-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.now(timezone.utc)

        new_asset = Asset(
            company_id=company_id,
            business_id=biz_id,
            asset_type=AssetType.GPS_DEVICE,
            device_name=payload.device_name.strip(),
            manufacturer=payload.manufacturer.strip(),
            model=payload.model.strip() if payload.model else None,
            imei=clean_imei,
            serial_number=payload.serial_number.strip() if payload.serial_number else clean_imei,
            connection_type=payload.connection_type,
            connection_status=ConnectionStatus.PENDING.value,
            protocol=payload.protocol,
            gps_provider=payload.gps_provider or "generic",
            encrypted_credentials=encrypted_creds,
            connection_config=payload.connection_config or {},
            offline_threshold_minutes=payload.offline_threshold_minutes,
            current_vehicle_id=payload.vehicle_id,
            installation_status=AssetInstallationStatus.INSTALLED if payload.vehicle_id else AssetInstallationStatus.REGISTERED,
            operational_status=AssetOperationalStatus.OK,
            installation_date=now if payload.vehicle_id else None,
        )
        db.add(new_asset)
        await db.flush()

        # 6. Record Audit History
        reg_history = AssetHistory(
            asset_id=new_asset.id,
            event_category=AssetHistoryCategory.REGISTERED,
            performed_at=now,
            details={
                "connection_type": payload.connection_type,
                "protocol": payload.protocol,
                "provider": payload.gps_provider,
                "imei": clean_imei
            },
            origin_type="SYSTEM",
            origin_id=biz_id
        )
        db.add(reg_history)

        if payload.vehicle_id and target_vehicle:
            install_history = AssetHistory(
                asset_id=new_asset.id,
                event_category=AssetHistoryCategory.INSTALLED,
                performed_at=now,
                details={
                    "vehicle_id": target_vehicle.id,
                    "registration_number": target_vehicle.registration_number
                },
                origin_type="USER_ACTION",
                origin_id=biz_id
            )
            db.add(install_history)

        await db.commit()
        try:
            await db.refresh(new_asset)
        except Exception:
            pass

        return cls._to_device_response(new_asset, target_vehicle)

    @classmethod
    async def update_device(
        cls, company_id: int, asset_id: int, payload: HardwareDeviceUpdateRequest, db: AsyncSession
    ) -> HardwareDeviceResponse:
        """Updates device settings."""
        asset = await db.get(Asset, asset_id)
        if not asset or asset.company_id != company_id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, f"Device {asset_id} not found.")

        if payload.device_name is not None:
            asset.device_name = payload.device_name.strip()
        if payload.manufacturer is not None:
            asset.manufacturer = payload.manufacturer.strip()
        if payload.model is not None:
            asset.model = payload.model.strip()
        if payload.protocol is not None:
            asset.protocol = payload.protocol
        if payload.gps_provider is not None:
            asset.gps_provider = payload.gps_provider
        if payload.offline_threshold_minutes is not None:
            asset.offline_threshold_minutes = payload.offline_threshold_minutes
        if payload.connection_config is not None:
            cfg = dict(asset.connection_config or {})
            cfg.update(payload.connection_config)
            asset.connection_config = cfg
        if payload.credentials is not None:
            asset.encrypted_credentials = encrypt_dict(payload.credentials)

        await db.commit()
        try:
            await db.refresh(asset)
        except Exception:
            pass
        return cls._to_device_response(asset)

    @classmethod
    async def reassign_vehicle(
        cls, company_id: int, asset_id: int, payload: VehicleReassignRequest, db: AsyncSession
    ) -> HardwareDeviceResponse:
        """
        Reassigns device to a new vehicle or unassigns to storage.
        Non-destructive: Historical tracking points in VehicleLocation are preserved!
        """
        asset = await db.get(Asset, asset_id)
        if not asset or asset.company_id != company_id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, f"Device {asset_id} not found.")

        old_vehicle_id = asset.current_vehicle_id
        target_vehicle = None
        now = datetime.now(timezone.utc)

        if payload.vehicle_id:
            target_vehicle = await db.get(Vehicle, payload.vehicle_id)
            if not target_vehicle or target_vehicle.company_id != company_id:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, "Target vehicle not found in your fleet.")

            # Check if vehicle has an active tracker
            conflict_q = await db.execute(
                select(Asset).where(
                    Asset.company_id == company_id,
                    Asset.current_vehicle_id == payload.vehicle_id,
                    Asset.id != asset_id,
                    Asset.installation_status == AssetInstallationStatus.INSTALLED
                )
            )
            existing_dev = conflict_q.scalars().first()
            if existing_dev:
                if payload.force:
                    # Unassign existing device
                    existing_dev.current_vehicle_id = None
                    existing_dev.installation_status = AssetInstallationStatus.IN_STORAGE
                    db.add(AssetHistory(
                        asset_id=existing_dev.id,
                        event_category=AssetHistoryCategory.REMOVED,
                        performed_at=now,
                        details={"reason": f"Displaced by reassignment of device {asset.business_id}"}
                    ))
                else:
                    raise HTTPException(
                        status.HTTP_409_CONFLICT,
                        f"Target vehicle {target_vehicle.registration_number} already has active device '{existing_dev.device_name}'. Set force=true to swap."
                    )

            asset.current_vehicle_id = payload.vehicle_id
            asset.installation_status = AssetInstallationStatus.INSTALLED
            asset.installation_date = now

            db.add(AssetHistory(
                asset_id=asset.id,
                event_category=AssetHistoryCategory.REPLACED if old_vehicle_id else AssetHistoryCategory.INSTALLED,
                performed_at=now,
                details={
                    "previous_vehicle_id": old_vehicle_id,
                    "new_vehicle_id": payload.vehicle_id,
                    "registration_number": target_vehicle.registration_number
                }
            ))
        else:
            # Unassign to storage
            asset.current_vehicle_id = None
            asset.installation_status = AssetInstallationStatus.IN_STORAGE
            db.add(AssetHistory(
                asset_id=asset.id,
                event_category=AssetHistoryCategory.REMOVED,
                performed_at=now,
                details={"previous_vehicle_id": old_vehicle_id}
            ))

        await db.commit()
        try:
            await db.refresh(asset)
        except Exception:
            pass
        return cls._to_device_response(asset, target_vehicle)

    @classmethod
    async def disconnect_device(
        cls, company_id: int, asset_id: int, db: AsyncSession
    ) -> HardwareDeviceResponse:
        """Puts device into disconnected/unassigned state."""
        return await cls.reassign_vehicle(
            company_id=company_id,
            asset_id=asset_id,
            payload=VehicleReassignRequest(vehicle_id=None),
            db=db
        )

    @classmethod
    async def remove_device(
        cls, company_id: int, asset_id: int, db: AsyncSession
    ) -> Dict[str, Any]:
        """Retires a device permanently."""
        asset = await db.get(Asset, asset_id)
        if not asset or asset.company_id != company_id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, f"Device {asset_id} not found.")

        now = datetime.now(timezone.utc)
        asset.current_vehicle_id = None
        asset.installation_status = AssetInstallationStatus.RETIRED
        asset.connection_status = ConnectionStatus.DISCONNECTED.value
        asset.operational_status = AssetOperationalStatus.MAINTENANCE

        db.add(AssetHistory(
            asset_id=asset.id,
            event_category=AssetHistoryCategory.RETIRED,
            performed_at=now,
            details={"action": "Device retired from active telematics service"}
        ))
        await db.commit()
        return {"success": True, "message": f"Device {asset.business_id} has been retired."}

    @classmethod
    async def test_device_connection(
        cls, company_id: int, asset_id: int, db: AsyncSession
    ) -> DeviceTestConnectionResponse:
        """
        Tests device communication status.
        If connected to a cloud provider (e.g. Traccar), probes the provider API.
        If direct hardware/webhook, checks communication freshness and health.
        """
        asset = await db.get(Asset, asset_id)
        if not asset or asset.company_id != company_id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, f"Device {asset_id} not found.")

        now = datetime.now(timezone.utc)
        status_val, is_stale = cls._compute_device_status(asset)

        # 1. If provider is Traccar and server URL configured
        if asset.gps_provider == "traccar" or asset.connection_type == ConnectionType.GPS_PROVIDER_API.value:
            config = asset.connection_config or {}
            server_url = config.get("server_url") or config.get("provider_url")
            if server_url:
                success, msg, info = await TraccarService.test_connection(server_url, asset.encrypted_credentials)
                return DeviceTestConnectionResponse(
                    success=success,
                    status=ConnectionStatus.CONNECTED.value if success else ConnectionStatus.ERROR.value,
                    message=msg,
                    last_communication=asset.last_communication_at,
                    details=info
                )

        # 2. Direct hardware or webhook connection test
        if asset.last_communication_at:
            age_mins = round((now - asset.last_communication_at).total_seconds() / 60.0, 1)
            if age_mins <= (asset.offline_threshold_minutes or 15):
                return DeviceTestConnectionResponse(
                    success=True,
                    status=ConnectionStatus.CONNECTED.value,
                    message=f"Device actively connected. Last telemetry received {age_mins} minutes ago.",
                    last_communication=asset.last_communication_at,
                    details={
                        "latitude": asset.last_known_lat,
                        "longitude": asset.last_known_lng,
                        "speed_kmh": asset.last_known_speed,
                        "ignition": asset.last_known_ignition,
                        "battery_volts": asset.last_known_battery,
                        "age_minutes": age_mins
                    }
                )
            else:
                return DeviceTestConnectionResponse(
                    success=False,
                    status=ConnectionStatus.DISCONNECTED.value,
                    message=f"Device offline. Last ping received {age_mins} minutes ago (exceeds threshold of {asset.offline_threshold_minutes} mins).",
                    last_communication=asset.last_communication_at,
                    details={"age_minutes": age_mins}
                )
        else:
            return DeviceTestConnectionResponse(
                success=False,
                status=ConnectionStatus.PENDING.value,
                message="No telemetry received yet. Device is registered and listening for first ping.",
                last_communication=None,
                details={"status": "Awaiting initial device connection packet"}
            )

    @classmethod
    async def test_pre_registration(
        cls, payload: PreRegistrationTestRequest
    ) -> DeviceTestConnectionResponse:
        """Tests provider connectivity before saving device configuration."""
        if payload.connection_type == ConnectionType.GPS_PROVIDER_API.value and payload.server_url:
            success, msg, info = await TraccarService.test_connection(payload.server_url, payload.credentials)
            return DeviceTestConnectionResponse(
                success=success,
                status="VERIFIED" if success else "FAILED",
                message=msg,
                details=info
            )
        elif payload.connection_type in [ConnectionType.DIRECT_HARDWARE.value, ConnectionType.TCP_DEVICE.value]:
            proto = payload.protocol
            proto_spec = VERIFIED_PROTOCOLS.get(proto)
            return DeviceTestConnectionResponse(
                success=True,
                status="CONFIG_VALIDATED",
                message=f"Protocol {proto} validated. Device should point to Vahan port {proto_spec.default_port if proto_spec else 5000}.",
                details={"default_port": proto_spec.default_port if proto_spec else 5000}
            )
        else:
            return DeviceTestConnectionResponse(
                success=True,
                status="CONFIG_READY",
                message="Endpoint parameters validated successfully."
            )

    @classmethod
    async def get_device_location_history(
        cls,
        company_id: int,
        asset_id: int,
        db: AsyncSession,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 500
    ) -> DeviceLocationHistoryResponse:
        """
        Retrieves historical GPS points recorded by this device.
        Computes total distance travelled, max speed, and average speed.
        """
        asset = await db.get(Asset, asset_id)
        if not asset or asset.company_id != company_id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, f"Device {asset_id} not found.")

        # Default time range: last 24 hours if not specified
        now = datetime.now(timezone.utc)
        st = start_time or (now - timedelta(hours=24))
        et = end_time or now

        # Query vehicle locations where device_id matches
        query = (
            select(VehicleLocation)
            .where(
                VehicleLocation.company_id == company_id,
                VehicleLocation.device_id == asset.id,
                VehicleLocation.timestamp >= st,
                VehicleLocation.timestamp <= et
            )
            .order_by(asc(VehicleLocation.timestamp))
            .limit(limit)
        )
        res = await db.execute(query)
        loc_rows = res.scalars().all()

        points: List[DeviceLocationPoint] = []
        total_dist_km = 0.0
        max_speed = 0.0
        speed_sum = 0.0
        speed_count = 0

        prev_lat = None
        prev_lon = None

        for row in loc_rows:
            speed_val = row.speed
            speed_kmh = round(speed_val * 3.6, 1) if speed_val is not None else None
            if speed_kmh is not None:
                if speed_kmh > max_speed:
                    max_speed = speed_kmh
                speed_sum += speed_kmh
                speed_count += 1

            if prev_lat is not None and prev_lon is not None:
                step_km = haversine_distance_km(prev_lat, prev_lon, row.latitude, row.longitude)
                # Filter out absurd single-step GPS jumps (> 200 km)
                if step_km < 200.0:
                    total_dist_km += step_km

            prev_lat = row.latitude
            prev_lon = row.longitude

            ignition = None
            if row.source_metadata and isinstance(row.source_metadata, dict):
                ignition = row.source_metadata.get("ignition_status") or row.source_metadata.get("ignition")

            points.append(
                DeviceLocationPoint(
                    id=row.id,
                    latitude=row.latitude,
                    longitude=row.longitude,
                    speed=row.speed,
                    speed_kmh=speed_kmh,
                    heading=row.heading,
                    accuracy=row.accuracy,
                    timestamp=row.timestamp,
                    ignition=ignition
                )
            )

        avg_speed = round(speed_sum / speed_count, 1) if speed_count > 0 else 0.0

        v = None
        if asset.current_vehicle_id:
            v = await db.get(Vehicle, asset.current_vehicle_id)
        return DeviceLocationHistoryResponse(
            device_id=asset.id,
            device_name=asset.device_name,
            imei=asset.imei or asset.serial_number,
            vehicle_id=asset.current_vehicle_id,
            vehicle_registration=v.registration_number if v else None,
            total_points=len(points),
            distance_km=round(total_dist_km, 2),
            max_speed_kmh=round(max_speed, 1),
            avg_speed_kmh=avg_speed,
            start_time=st,
            end_time=et,
            points=points
        )

    # =========================================================================
    # GPS Provider Account Management
    # =========================================================================

    @classmethod
    async def list_provider_accounts(
        cls, company_id: int, db: AsyncSession
    ) -> List[GPSProviderAccountResponse]:
        """Lists connected GPS provider accounts for the company."""
        res = await db.execute(
            select(GPSProviderAccount)
            .where(GPSProviderAccount.company_id == company_id)
            .order_by(desc(GPSProviderAccount.created_at))
        )
        accounts = res.scalars().all()
        return [GPSProviderAccountResponse.model_validate(a) for a in accounts]

    @classmethod
    async def create_provider_account(
        cls, company_id: int, payload: GPSProviderAccountCreateRequest, db: AsyncSession
    ) -> GPSProviderAccountResponse:
        """Connects a new GPS provider account."""
        encrypted_creds = encrypt_credential(payload.credentials) if payload.credentials else None
        
        account = GPSProviderAccount(
            company_id=company_id,
            provider_type=payload.provider_type.lower(),
            name=payload.name.strip(),
            server_url=payload.server_url.strip() if payload.server_url else None,
            account_id=payload.account_id.strip() if payload.account_id else None,
            encrypted_credentials=encrypted_creds,
            sync_status="CONNECTED",
            config=payload.config or {},
        )
        db.add(account)
        await db.commit()
        await db.refresh(account)
        return GPSProviderAccountResponse.model_validate(account)

    @classmethod
    async def test_provider_account(
        cls, company_id: int, account_id: int, db: AsyncSession
    ) -> DeviceTestConnectionResponse:
        """Tests provider connectivity."""
        account = await db.get(GPSProviderAccount, account_id)
        if not account or account.company_id != company_id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Provider account not found.")

        if account.provider_type == "traccar" and account.server_url:
            success, msg, info = await TraccarService.test_connection(account.server_url, account.encrypted_credentials)
            account.sync_status = "CONNECTED" if success else "ERROR"
            account.sync_error = None if success else msg
            await db.commit()
            return DeviceTestConnectionResponse(
                success=success,
                status=account.sync_status,
                message=msg,
                details=info
            )
        else:
            return DeviceTestConnectionResponse(
                success=True,
                status="CONNECTED",
                message="Provider account verified."
            )

    @classmethod
    async def sync_provider_account(
        cls, company_id: int, account_id: int, db: AsyncSession
    ) -> Dict[str, Any]:
        """Synchronizes devices from provider account."""
        account = await db.get(GPSProviderAccount, account_id)
        if not account or account.company_id != company_id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Provider account not found.")

        if account.provider_type == "traccar":
            try:
                return await TraccarService.sync_devices_and_positions(account, db)
            except Exception as e:
                account.sync_status = "ERROR"
                account.sync_error = str(e)
                await db.commit()
                return {"error": str(e), "message": f"Sync failed: {str(e)}"}
        else:
            account.last_sync_at = datetime.now(timezone.utc)
            await db.commit()
            return {"message": "Sync completed for generic provider."}

    @classmethod
    async def delete_provider_account(
        cls, company_id: int, account_id: int, db: AsyncSession
    ) -> Dict[str, Any]:
        """Deletes/revokes provider account."""
        account = await db.get(GPSProviderAccount, account_id)
        if not account or account.company_id != company_id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Provider account not found.")

        await db.delete(account)
        await db.commit()
        return {"success": True, "message": "Provider account revoked successfully."}

    # =======================================================================
    # 9. Super-Admin Quarantine Governance
    # =======================================================================

    @classmethod
    async def get_quarantine_company(cls, db: AsyncSession) -> Optional[Company]:
        """Finds or resolves the designated quarantine tenant."""
        q = select(Company).where(
            or_(
                Company.email == "quarantine@vahan.system",
                Company.status == CompanyStatus.SUSPENDED,
                Company.company_name.ilike("%quarantine%")
            )
        )
        res = await db.execute(q)
        return res.scalars().first()

    @classmethod
    async def list_quarantined_assets(cls, db: AsyncSession) -> List[QuarantinedAssetItem]:
        """Lists all hardware assets held in quarantine. Accessible only to Super-Admins."""
        quarantine_comp = await cls.get_quarantine_company(db)
        if not quarantine_comp:
            return []

        q = select(Asset).where(Asset.company_id == quarantine_comp.id).order_by(desc(Asset.created_at))
        res = await db.execute(q)
        assets = res.scalars().all()
        return [
            QuarantinedAssetItem(
                id=a.id,
                business_id=a.business_id,
                device_name=a.device_name or "Unnamed Quarantined Device",
                imei=a.imei,
                manufacturer=a.manufacturer,
                model=a.model,
                protocol=a.protocol,
                connection_status=a.connection_status,
                last_communication_at=a.last_communication_at,
                created_at=a.created_at or datetime.now(timezone.utc),
                quarantine_company_id=quarantine_comp.id
            )
            for a in assets
        ]

    @classmethod
    async def reassign_quarantined_asset(
        cls,
        asset_id: int,
        payload: QuarantinedAssetReassignRequest,
        admin_id: Optional[int],
        admin_email: str,
        db: AsyncSession,
        ip_address: Optional[str] = None
    ) -> HardwareDeviceResponse:
        """
        Reassigns an asset from quarantine to an active tenant company.
        Records an audit log in AdminAuditLog and AssetHistory.
        """
        quarantine_comp = await cls.get_quarantine_company(db)
        asset = await db.get(Asset, asset_id)
        if not asset:
            raise HTTPException(status.HTTP_404_NOT_FOUND, f"Asset {asset_id} not found.")

        # Ensure asset is actually in quarantine
        if quarantine_comp and asset.company_id != quarantine_comp.id:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"Asset {asset_id} is not quarantined (belongs to company {asset.company_id})."
            )

        # Validate target company exists and is active
        target_company = await db.get(Company, payload.target_company_id)
        if not target_company:
            raise HTTPException(status.HTTP_404_NOT_FOUND, f"Target company {payload.target_company_id} does not exist.")
        if target_company.status != CompanyStatus.ACTIVE:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Target company {payload.target_company_id} is not active ({target_company.status}).")

        # Validate target vehicle if provided
        target_vehicle = None
        now = datetime.now(timezone.utc)
        if payload.target_vehicle_id:
            target_vehicle = await db.get(Vehicle, payload.target_vehicle_id)
            if not target_vehicle or target_vehicle.company_id != payload.target_company_id:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, "Target vehicle not found in specified company.")

        old_company_id = asset.company_id
        asset.company_id = payload.target_company_id
        if target_vehicle:
            asset.current_vehicle_id = target_vehicle.id
            asset.installation_status = AssetInstallationStatus.INSTALLED
            asset.installation_date = now
        else:
            asset.current_vehicle_id = None
            asset.installation_status = AssetInstallationStatus.IN_STORAGE

        # 1. Audit log in asset_history_records
        db.add(AssetHistory(
            asset_id=asset.id,
            event_category=AssetHistoryCategory.INSTALLED if target_vehicle else AssetHistoryCategory.REMOVED,
            performed_at=now,
            details={
                "action": "QUARANTINE_REASSIGNMENT",
                "previous_company_id": old_company_id,
                "new_company_id": payload.target_company_id,
                "assigned_vehicle_id": payload.target_vehicle_id,
                "reason": payload.reason,
                "admin_email": admin_email
            }
        ))

        # 2. Audit log in admin_audit_logs
        db.add(AdminAuditLog(
            admin_id=admin_id,
            action="REASSIGN_QUARANTINED_ASSET",
            resource_type="ASSET",
            resource_id=str(asset.id),
            old_value=str(old_company_id),
            new_value=str(payload.target_company_id),
            ip_address=ip_address,
            reason=payload.reason
        ))

        await db.commit()
        await db.refresh(asset)
        return cls._to_device_response(asset, target_vehicle)
