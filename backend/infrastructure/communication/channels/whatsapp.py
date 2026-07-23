"""
Message Gateway Framework - WhatsApp Channel Adapter
"""

import uuid
from typing import Dict, Any, List

from infrastructure.communication.base import BaseCommunicationChannel
from infrastructure.communication.models import Communication, Attachment, CommunicationType
from infrastructure.communication.validators import validate_required_fields, validate_sender_format, validate_timestamp_format
from infrastructure.communication.normalizers import normalize_phone_number, normalize_timestamp, normalize_text


class WhatsAppChannel(BaseCommunicationChannel):
    """
    Adapter for processing incoming webhooks from WhatsApp Business API.
    """

    @classmethod
    def key(cls) -> str:
        return "whatsapp"

    @classmethod
    def name(cls) -> str:
        return "WhatsApp Business API"

    def validate(self, payload: Dict[str, Any]) -> bool:
        """
        Validates the expected payload structure for a WhatsApp message.
        """
        # Basic validation for our mock/stub structure
        validate_required_fields(payload, ["message_id", "from", "to", "timestamp", "type"])
        validate_sender_format(payload["from"])
        validate_timestamp_format(payload["timestamp"])
        return True

    def extract_attachments(self, payload: Dict[str, Any]) -> List[Attachment]:
        """
        Extracts attachments from a WhatsApp payload.
        WhatsApp sends media payloads like {"type": "image", "image": {"id": "...", "mime_type": "...", "link": "..."}}
        """
        msg_type = payload.get("type")
        attachments = []
        
        # Stub implementation assuming 'media' key contains list of media objects in raw payload
        if msg_type in ["image", "document", "audio", "video"]:
            media_data = payload.get(msg_type, {})
            if media_data:
                attachments.append(Attachment(
                    attachment_id=uuid.uuid4(),
                    media_type=media_data.get("mime_type", "application/octet-stream"),
                    filename=media_data.get("filename"),
                    file_size=media_data.get("file_size"),
                    checksum=media_data.get("sha256"),
                    storage_uri=media_data.get("link", f"whatsapp://media/{media_data.get('id', '')}")
                ))
        return attachments

    def normalize(self, payload: Dict[str, Any], attachments: List[Attachment]) -> Communication:
        """
        Normalizes the payload into standard Communication object.
        """
        raw_type = payload.get("type", "text")
        
        type_mapping = {
            "text": CommunicationType.TEXT,
            "image": CommunicationType.IMAGE,
            "document": CommunicationType.DOCUMENT,
            "audio": CommunicationType.AUDIO,
            "video": CommunicationType.VIDEO,
            "system": CommunicationType.SYSTEM
        }
        
        msg_type = type_mapping.get(raw_type, CommunicationType.TEXT)
        
        text_content = ""
        if msg_type == CommunicationType.TEXT:
            text_data = payload.get("text", {})
            text_content = text_data.get("body", "")
        elif msg_type == CommunicationType.DOCUMENT:
            doc_data = payload.get("document", {})
            text_content = doc_data.get("caption", "")
        elif msg_type == CommunicationType.IMAGE:
            img_data = payload.get("image", {})
            text_content = img_data.get("caption", "")

        return Communication(
            message_id=payload["message_id"],
            channel=self.key(),
            sender=normalize_phone_number(payload["from"]),
            receiver=normalize_phone_number(payload["to"]),
            timestamp=normalize_timestamp(payload["timestamp"]),
            message_type=msg_type,
            text=normalize_text(text_content),
            attachments=attachments,
            metadata={"original_type": raw_type}
        )
