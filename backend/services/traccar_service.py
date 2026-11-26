"""
FleetGuard / Vahan — Traccar GPS Ingestion Engine Integration Service
Provides REST API integration with Traccar GPS tracking server (https://www.traccar.org).
Handles server health checks, device registration, position synchronization,
and webhook forwarder parsing while preserving Vahan's multi-tenant company isolation.
"""

import httpx
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from models.asset_domain import Asset, AssetType, ConnectionStatus, GPSProviderAccount
from schemas.telematics import NormalizedHardwareEvent
from utils.credential_crypto import decrypt_credential

logger = logging.getLogger(__name__)


class TraccarService:
    """
    Manages communication with external or self-hosted Traccar GPS server.
    """

    @classmethod
    def _get_auth_headers(cls, credentials_raw: Optional[str]) -> Dict[str, str]:
        """
        Parses credentials (token or username:password) and returns HTTP headers.
        """
        if not credentials_raw:
            return {}
        
        creds = decrypt_credential(credentials_raw) or credentials_raw
        if ":" in creds:
            import base64
            auth_b64 = base64.b64encode(creds.encode("utf-8")).decode("utf-8")
            return {"Authorization": f"Basic {auth_b64}"}
        else:
            # Bearer or API token
            return {"Authorization": f"Bearer {creds}"}

    @classmethod
    async def test_connection(
        cls, server_url: str, credentials: Optional[str] = None
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Tests connectivity to the Traccar server via /api/server or /api/session.
        Returns (success: bool, message: str, server_info: dict).
        """
        url = server_url.rstrip("/")
        headers = cls._get_auth_headers(credentials)
        headers["Accept"] = "application/json"

        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                # 1. Probe server metadata
                res = await client.get(f"{url}/api/server", headers=headers)
                if res.status_code == 200:
                    data = res.json()
                    version = data.get("version", "Unknown")
                    name = data.get("name", "Traccar")
                    return True, f"Connected to {name} v{version}", data
                elif res.status_code in [401, 403]:
                    # Server is reachable but auth failed
                    return False, f"Server reachable but authentication failed (HTTP {res.status_code})", {}
                else:
                    return False, f"Server returned HTTP {res.status_code}: {res.text[:100]}", {}
        except httpx.ConnectError:
            return False, f"Connection refused or unreachable at {url}", {}
        except httpx.TimeoutException:
            return False, f"Connection timed out after 10s connecting to {url}", {}
        except Exception as e:
            return False, f"Error communicating with Traccar: {str(e)}", {}

    @classmethod
    async def fetch_devices(
        cls, server_url: str, credentials: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetches all registered devices from Traccar /api/devices.
        """
        url = server_url.rstrip("/")
        headers = cls._get_auth_headers(credentials)
        headers["Accept"] = "application/json"

        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.get(f"{url}/api/devices", headers=headers)
            if res.status_code == 200:
                return res.json()
            else:
                logger.error(f"Failed to fetch Traccar devices: {res.status_code} - {res.text}")
                return []

    @classmethod
    async def fetch_positions(
        cls, server_url: str, credentials: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetches latest positions for all devices from Traccar /api/positions.
        """
        url = server_url.rstrip("/")
        headers = cls._get_auth_headers(credentials)
        headers["Accept"] = "application/json"

        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.get(f"{url}/api/positions", headers=headers)
            if res.status_code == 200:
                return res.json()
            return []

    @classmethod
    async def register_device(
        cls, server_url: str, credentials: Optional[str], device_name: str, unique_id: str
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Registers a new device in Traccar via POST /api/devices.
        """
        url = server_url.rstrip("/")
        headers = cls._get_auth_headers(credentials)
        headers["Content-Type"] = "application/json"
        headers["Accept"] = "application/json"

        payload = {
            "name": device_name,
            "uniqueId": unique_id,
            "category": "truck",
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(f"{url}/api/devices", json=payload, headers=headers)
                if res.status_code in [200, 201]:
                    return True, "Device registered in Traccar successfully", res.json()
                elif res.status_code == 400 and "uniqueId" in res.text.lower():
                    return True, "Device already registered in Traccar", None
                else:
                    return False, f"Traccar registration failed ({res.status_code}): {res.text[:150]}", None
        except Exception as e:
            return False, f"Failed to register in Traccar: {str(e)}", None

    @classmethod
    def parse_forward_payload(cls, raw_data: Dict[str, Any]) -> NormalizedHardwareEvent:
        """
        Translates a Traccar webhook / forwarder event into Vahan's NormalizedHardwareEvent.
        Supports both Traccar HTTP parameter forwarding and JSON forwarding.
        """
        pos = raw_data.get("position", raw_data)
        dev = raw_data.get("device", {})
        
        unique_id = str(dev.get("uniqueId") or raw_data.get("uniqueId") or pos.get("deviceId") or raw_data.get("id", ""))
        
        lat = float(pos.get("latitude", 0.0))
        lng = float(pos.get("longitude", 0.0))
        
        # Parse timestamp
        ts_raw = pos.get("fixTime") or pos.get("deviceTime") or pos.get("serverTime") or pos.get("timestamp")
        if isinstance(ts_raw, str):
            try:
                dt = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
            except ValueError:
                dt = datetime.now(timezone.utc)
        elif isinstance(ts_raw, (int, float)):
            dt = datetime.fromtimestamp(ts_raw / 1000.0 if ts_raw > 1e11 else ts_raw, tz=timezone.utc)
        else:
            dt = datetime.now(timezone.utc)

        # Speed: Traccar sends knots -> convert to km/h
        speed_val = pos.get("speed")
        speed_kmh = float(speed_val) * 1.852 if speed_val is not None else None

        heading_val = pos.get("course") or pos.get("heading")
        heading = float(heading_val) if heading_val is not None else None

        # Attributes: ignition, battery
        attrs = pos.get("attributes", {})
        if not isinstance(attrs, dict):
            attrs = {}

        ignition = None
        if "ignition" in attrs:
            ignition = bool(attrs["ignition"])
        elif "ignition" in pos:
            ignition = bool(pos["ignition"])

        return NormalizedHardwareEvent(
            device_imei=unique_id,
            latitude=lat,
            longitude=lng,
            timestamp=dt,
            speed=speed_kmh,
            heading=heading,
            accuracy=float(pos.get("accuracy", 1.0)) if "accuracy" in pos else None,
            ignition_status=ignition,
            source_metadata={
                "provider": "traccar",
                "protocol": pos.get("protocol"),
                "attributes": attrs,
                "altitude": pos.get("altitude"),
                "raw_speed_knots": speed_val
            }
        )

    @classmethod
    async def sync_devices_and_positions(
        cls, account: GPSProviderAccount, db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Synchronizes all devices and latest positions from Traccar into Vahan's Asset table.
        Scoped to account.company_id.
        """
        if not account.server_url:
            return {"error": "Server URL not configured for provider account"}

        devices = await cls.fetch_devices(account.server_url, account.encrypted_credentials)
        positions = await cls.fetch_positions(account.server_url, account.encrypted_credentials)
        
        # Index positions by deviceId
        pos_by_device_id = {p.get("deviceId"): p for p in positions if "deviceId" in p}

        synced_count = 0
        updated_positions = 0

        for d in devices:
            unique_id = str(d.get("uniqueId", "")).strip()
            if not unique_id:
                continue

            # Check if device exists in company
            asset_q = await db.execute(
                select(Asset).where(
                    and_(
                        Asset.company_id == account.company_id,
                        Asset.imei == unique_id
                    )
                )
            )
            asset = asset_q.scalar_one_or_none()

            traccar_dev_id = d.get("id")
            pos = pos_by_device_id.get(traccar_dev_id)

            if asset:
                # Update status
                traccar_status = d.get("status") # online, offline, unknown
                if traccar_status == "online":
                    asset.connection_status = ConnectionStatus.CONNECTED.value
                elif traccar_status == "offline":
                    asset.connection_status = ConnectionStatus.DISCONNECTED.value

                if pos:
                    asset.last_known_lat = float(pos.get("latitude", asset.last_known_lat))
                    asset.last_known_lng = float(pos.get("longitude", asset.last_known_lng))
                    
                    sp = pos.get("speed")
                    if sp is not None:
                        asset.last_known_speed = round(float(sp) * 1.852, 2)
                        
                    course = pos.get("course")
                    if course is not None:
                        asset.last_known_heading = round(float(course), 2)
                        
                    fix_time = pos.get("fixTime") or pos.get("deviceTime")
                    if fix_time:
                        try:
                            asset.last_communication_at = datetime.fromisoformat(fix_time.replace("Z", "+00:00"))
                        except Exception:
                            pass
                    updated_positions += 1
                synced_count += 1

        account.device_count = len(devices)
        account.last_sync_at = datetime.now(timezone.utc)
        account.sync_status = "CONNECTED"
        account.sync_error = None

        await db.commit()

        return {
            "total_provider_devices": len(devices),
            "matched_vahan_assets": synced_count,
            "positions_updated": updated_positions,
            "synced_at": account.last_sync_at.isoformat()
        }
