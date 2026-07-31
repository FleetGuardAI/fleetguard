"""
FleetGuard — Driver WebSocket Endpoint

Provides real-time bi-directional messaging for active drivers.
Receives ping/pong, location updates, and pushes trip updates, vehicle assignments, and alerts.
"""

import json
import logging
from typing import Dict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

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

    def disconnect(self, driver_id: int):
        self.active_connections.pop(driver_id, None)
        logger.info(f"Driver #{driver_id} WebSocket disconnected")

    async def send_personal_message(self, message: dict, driver_id: int):
        if driver_id in self.active_connections:
            websocket = self.active_connections[driver_id]
            await websocket.send_text(json.dumps(message))

    async def broadcast(self, message: dict):
        for websocket in self.active_connections.values():
            await websocket.send_text(json.dumps(message))


ws_manager = ConnectionManager()


@router.websocket("/driver/{driver_id}")
async def driver_websocket_endpoint(
    websocket: WebSocket,
    driver_id: int,
    token: str = Query(...),
):
    """
    WebSocket connection for real-time driver updates.
    """
    await ws_manager.connect(driver_id, websocket)
    try:
        # Send initial connected message
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
        ws_manager.disconnect(driver_id)
    except Exception as e:
        logger.error(f"WS Exception driver #{driver_id}: {e}")
        ws_manager.disconnect(driver_id)
