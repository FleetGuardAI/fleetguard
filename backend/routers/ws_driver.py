"""
FleetGuard — Driver & Fleet WebSocket Endpoints

Provides real-time bi-directional messaging for active drivers and fleet managers.
Secured with central JWT authentication, active session verification, and strict role/tenant authorization.
"""

import json
import logging
from typing import Dict, List, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status, Depends
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.user import User, UserRole
from models.auth_session import AuthSession
from models.driver_domain import Driver
from utils.security import decode_access_token

logger = logging.getLogger("fleetguard.ws")

router = APIRouter(prefix="/api/v1/ws", tags=["WebSocket"])


class ConnectionManager:
    """Manages active driver WebSocket connections."""

    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}

    async def connect(self, driver_id: int, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[driver_id] = websocket
        logger.info(f"Driver #{driver_id} WebSocket connected")

    def disconnect(self, driver_id: int, websocket: Optional[WebSocket] = None):
        if driver_id in self.active_connections:
            if websocket is None or self.active_connections[driver_id] == websocket:
                self.active_connections.pop(driver_id, None)
                logger.info(f"Driver #{driver_id} WebSocket disconnected")

    async def send_personal_message(self, message: dict, driver_id: int):
        if driver_id in self.active_connections:
            websocket = self.active_connections[driver_id]
            await websocket.send_text(json.dumps(message))

    async def broadcast(self, message: dict):
        for websocket in list(self.active_connections.values()):
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.warning(f"Error broadcasting to driver socket: {e}")


ws_manager = ConnectionManager()


class OwnerConnectionManager:
    """Manages active owner/dispatcher WebSocket connections for fleet tracking."""

    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, company_id: int, websocket: WebSocket):
        await websocket.accept()
        if company_id not in self.active_connections:
            self.active_connections[company_id] = []
        self.active_connections[company_id].append(websocket)
        logger.info(f"Owner/Dispatcher for company #{company_id} WebSocket connected")

    def disconnect(self, company_id: int, websocket: WebSocket):
        if company_id in self.active_connections:
            if websocket in self.active_connections[company_id]:
                self.active_connections[company_id].remove(websocket)
            if not self.active_connections[company_id]:
                del self.active_connections[company_id]
            logger.info(f"Owner/Dispatcher for company #{company_id} WebSocket disconnected")

    async def broadcast_to_company(self, company_id: int, message: dict):
        if company_id in self.active_connections:
            for websocket in list(self.active_connections[company_id]):
                try:
                    await websocket.send_text(json.dumps(message))
                except Exception as e:
                    logger.warning(f"Error broadcasting to company #{company_id} socket: {e}")


owner_ws_manager = OwnerConnectionManager()


def extract_ws_token(websocket: WebSocket, token_query: Optional[str]) -> Optional[str]:
    """
    FG-SEC-001: Extract authentication token prioritizing secure headers over query strings.
    1. Authorization header: 'Bearer <token>'
    2. Sec-WebSocket-Protocol: 'bearer, <token>' or '<token>'
    3. Query parameter: '?token=<token>' (fallback for standard browser WebSocket API)
    """
    auth_header = websocket.headers.get("authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:].strip()

    sec_proto = websocket.headers.get("sec-websocket-protocol")
    if sec_proto:
        parts = [p.strip() for p in sec_proto.split(",")]
        for p in parts:
            if p.lower() != "bearer" and len(p) > 20:
                return p

    if token_query and str(token_query).strip():
        return token_query.strip()

    return None


async def authenticate_ws_token(websocket: WebSocket, token_query: Optional[str], db: AsyncSession) -> Optional[User]:
    """
    Authenticate a WebSocket connection token using central JWT and session verification.
    Validates token signature, expiration, active unrevoked session, and user active status.
    Returns the authenticated User or None.
    """
    token = extract_ws_token(websocket, token_query)
    if not token or not str(token).strip():
        return None
    try:
        payload = decode_access_token(token.strip())
        user_id_str: Optional[str] = payload.get("sub")
        token_jti: Optional[str] = payload.get("jti")
        token_company_id: Optional[int] = payload.get("company_id")
        token_type: Optional[str] = payload.get("type")
        if not user_id_str or not token_jti or token_type == "refresh":
            return None
        user_id = int(user_id_str)
    except (JWTError, ValueError, TypeError):
        return None

    now = datetime.now(timezone.utc)
    session_result = await db.execute(
        select(AuthSession).where(
            AuthSession.session_jti == token_jti,
            AuthSession.user_id == user_id,
            AuthSession.revoked_at.is_(None),
            AuthSession.expires_at > now,
        )
    )
    auth_session = session_result.scalar_one_or_none()
    if auth_session is None:
        return None

    user_result = await db.execute(select(User).where(User.id == user_id))
    user: Optional[User] = user_result.scalar_one_or_none()
    if user is None or not user.is_active:
        return None

    if token_company_id is not None and user.company_id != int(token_company_id):
        return None

    auth_session.last_seen_at = now
    await db.commit()
    return user


@router.websocket("/driver/{driver_id}")
async def driver_websocket_endpoint(
    websocket: WebSocket,
    driver_id: int,
    token: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """
    WebSocket connection for real-time driver updates.
    Requires authenticated driver or authorized company manager.
    """
    user = await authenticate_ws_token(websocket, token, db)
    if not user:
        logger.warning(f"Rejected unauthenticated driver WS connection for driver #{driver_id}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    driver_result = await db.execute(select(Driver).where(Driver.id == driver_id))
    driver = driver_result.scalar_one_or_none()
    if not driver:
        logger.warning(f"Rejected WS connection: Driver #{driver_id} not found (user #{user.id})")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Authorization:
    # Drivers can only subscribe to their own stream
    if user.role == UserRole.DRIVER:
        if driver.user_id != user.id and driver.phone_number != user.mobile_number:
            logger.warning(
                f"Rejected unauthorized driver WS: Driver user #{user.id} tried accessing driver #{driver_id}"
            )
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
    else:
        # Fleet manager / admin / dispatcher must belong to same company
        allowed_roles = [
            UserRole.COMPANY_ADMIN,
            UserRole.FLEET_MANAGER,
            UserRole.DISPATCHER,
            UserRole.ADMIN,
            UserRole.SUPER_ADMIN,
        ]
        if user.role not in allowed_roles:
            logger.warning(
                f"Rejected unauthorized driver WS: User #{user.id} with role {user.role} cannot subscribe"
            )
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        if user.role != UserRole.SUPER_ADMIN and driver.company_id != user.company_id:
            logger.warning(
                f"Rejected cross-tenant driver WS: User #{user.id} (company #{user.company_id}) "
                f"tried accessing driver #{driver_id} (company #{driver.company_id})"
            )
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

    await ws_manager.connect(driver_id, websocket)
    try:
        await websocket.send_text(json.dumps({
            "type": "connection_established",
            "driver_id": driver_id,
            "status": "connected",
        }))

        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                msg_type = msg.get("type")

                if msg_type == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                elif msg_type == "duty_change":
                    logger.info(f"Driver #{driver_id} duty change: {msg.get('status')}")
                    await websocket.send_text(json.dumps({"type": "ack", "event": "duty_change"}))
                else:
                    await websocket.send_text(json.dumps({"type": "ack"}))

            except json.JSONDecodeError:
                pass

    except WebSocketDisconnect:
        ws_manager.disconnect(driver_id, websocket)
    except Exception as e:
        logger.error(f"WS Exception driver #{driver_id}: {e}")
        ws_manager.disconnect(driver_id, websocket)


@router.websocket("/fleet/{company_id}")
async def fleet_websocket_endpoint(
    websocket: WebSocket,
    company_id: int,
    token: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """
    WebSocket connection for real-time fleet telemetry.
    Requires authenticated company manager or admin. Rejects drivers and cross-tenant users.
    """
    user = await authenticate_ws_token(websocket, token, db)
    if not user:
        logger.warning(f"Rejected unauthenticated fleet WS connection for company #{company_id}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Drivers are not permitted to listen to company-wide fleet tracking
    if user.role == UserRole.DRIVER:
        logger.warning(
            f"Rejected unauthorized fleet WS: Driver user #{user.id} tried accessing company #{company_id} fleet stream"
        )
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    allowed_roles = [
        UserRole.COMPANY_ADMIN,
        UserRole.FLEET_MANAGER,
        UserRole.DISPATCHER,
        UserRole.ADMIN,
        UserRole.SUPER_ADMIN,
    ]
    if user.role not in allowed_roles:
        logger.warning(
            f"Rejected unauthorized fleet WS: User #{user.id} with role {user.role} cannot subscribe"
        )
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Tenant isolation
    if user.role != UserRole.SUPER_ADMIN and user.company_id != company_id:
        logger.warning(
            f"Rejected cross-tenant fleet WS: User #{user.id} (company #{user.company_id}) "
            f"tried accessing company #{company_id}"
        )
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await owner_ws_manager.connect(company_id, websocket)
    try:
        await websocket.send_text(json.dumps({"type": "connection_established", "status": "connected"}))
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        owner_ws_manager.disconnect(company_id, websocket)
    except Exception as e:
        logger.error(f"WS Exception owner for company #{company_id}: {e}")
        owner_ws_manager.disconnect(company_id, websocket)
