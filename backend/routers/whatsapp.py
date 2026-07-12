"""
FleetGuard — WhatsApp Webhook Router
Handles incoming messages from the Meta WhatsApp Business API.
"""

from fastapi import APIRouter, Request, Query, HTTPException
from fastapi.responses import PlainTextResponse
from typing import Any

from config import settings

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp"])


@router.get("/webhook", response_class=PlainTextResponse)
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
) -> str:
    """
    WhatsApp webhook verification endpoint.
    Meta sends a GET request with a challenge token during webhook registration.
    We must respond with the challenge value if the verify token matches.
    """
    if hub_mode == "subscribe" and hub_verify_token == settings.WHATSAPP_VERIFY_TOKEN:
        return hub_challenge or ""
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/webhook")
async def receive_webhook(request: Request) -> dict[str, Any]:
    """
    Receive incoming WhatsApp messages (text, image, location).

    Full implementation in Phase 2 will:
    1. Parse the incoming message type (text/image/location)
    2. If image → send to OpenAI Vision for OCR receipt extraction
    3. Request driver's live location
    4. Check for duplicate receipts
    5. Apply fair price logic and set risk_flag
    6. Create a Ticket in the database
    7. Notify the fleet owner dashboard

    Currently returns the raw payload for debugging.
    """
    body = await request.json()

    # Extract message data from the WhatsApp webhook payload structure
    entry = body.get("entry", [])
    if not entry:
        return {"status": "no_entry"}

    changes = entry[0].get("changes", [])
    if not changes:
        return {"status": "no_changes"}

    value = changes[0].get("value", {})
    messages = value.get("messages", [])

    if not messages:
        # This is a status update (sent, delivered, read), not a message
        return {"status": "status_update_received"}

    message = messages[0]
    sender_phone = message.get("from", "")
    message_type = message.get("type", "")
    message_id = message.get("id", "")

    response_data: dict[str, Any] = {
        "status": "received",
        "message_id": message_id,
        "from": sender_phone,
        "type": message_type,
    }

    if message_type == "text":
        response_data["text"] = message.get("text", {}).get("body", "")

    elif message_type == "image":
        image_info = message.get("image", {})
        response_data["image_id"] = image_info.get("id", "")
        response_data["caption"] = image_info.get("caption", "")
        # Phase 2: Download image → OCR → Create ticket

    elif message_type == "location":
        location = message.get("location", {})
        response_data["latitude"] = location.get("latitude")
        response_data["longitude"] = location.get("longitude")
        response_data["location_name"] = location.get("name", "")
        # Phase 2: Attach location to pending ticket

    return response_data
