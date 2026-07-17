"""
FleetGuard — Kafka Event Serialization
Formats Operational Events into a versioned Kafka message envelope.
"""

import json
from datetime import datetime, timezone
from typing import Any, Dict

from schemas.operational_event import OperationalEventResponse


class EventSerializer:
    """
    Handles serializing and deserializing events for Kafka transport.
    """

    @staticmethod
    def serialize(event: OperationalEventResponse) -> bytes:
        """
        Wrap an OperationalEventResponse in a standard versioned envelope
        and serialize to JSON bytes.
        """
        # We model_dump() with mode='json' to ensure all datetimes/UUIDs are strings
        payload = event.model_dump(mode='json')
        
        envelope = {
            "event_id": str(event.id),
            "event_type": event.event_type.value,
            "entity_type": event.entity_type.value,
            "entity_id": event.entity_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": "1.0",
            "payload": payload,
            "metadata": {
                "source": "fleetguard-core"
            }
        }
        return json.dumps(envelope).encode("utf-8")

    @staticmethod
    def deserialize(data: bytes) -> OperationalEventResponse:
        """
        Deserialize a JSON byte array from Kafka back into an OperationalEventResponse.
        """
        envelope = json.loads(data.decode("utf-8"))
        
        # In version 1.0, the payload is exactly the OperationalEventResponse schema
        payload = envelope.get("payload", {})
        return OperationalEventResponse.model_validate(payload)
