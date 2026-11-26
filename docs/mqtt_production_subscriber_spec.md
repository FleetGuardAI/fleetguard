# Vahan — Production MQTT Telematics Subscriber Specification & Implementation Plan

> **Status**: Architecture Specification & Implementation Plan  
> **Target Subsystem**: `backend/workers/mqtt_subscriber.py`  
> **Compliance**: Production IoT/Telematics Ingestion Standards

---

## 1. Architectural Overview

Currently, Vahan normalizes MQTT payloads via REST webhook calls (`backend/infrastructure/gps/providers/mqtt.py`). However, for production IoT deployments with cellular-connected MQTT GPS gateways (such as Teltonika FMT100 MQTT firmware, Queclink MQTT trackers, or custom ESP32/Nordic nRF9160 IoT hubs), Vahan requires a **dedicated, long-lived background MQTT daemon**.

```mermaid
flowchart LR
    A["Cellular IoT GPS Devices"] -->|MQTT over TLS (8883)| B["MQTT Broker (EMQX / Mosquitto)"]
    subgraph VahanWorker["Vahan MQTT Ingestion Worker"]
        C["Asyncio MQTT Client Loop (aiomqtt)"]
        D["Topic Parser & IMEI Extractor"]
        E["Tenant Isolation & Auth Verification"]
        F["Packet Deduplication & Batch Buffer"]
    end
    B -->|Subscribe vahan/+/devices/+/telemetry| C
    C --> D --> E --> F
    F -->|process_hardware_batch| G["LocationService & PostgreSQL"]
    H["Prometheus / Health Check (:9100)"] --- C
```

---

## 2. Broker Authentication & TLS Configuration

### 2.1 Transport Layer Security (TLS 1.3)
All device-to-broker and worker-to-broker traffic must be encrypted using TLS:
- **Port**: `8883` (MQTTS).
- **Minimum Protocol**: TLS v1.3 (RFC 8446) with TLS v1.2 fallback.
- **Cipher Suites**: `TLS_AES_256_GCM_SHA384`, `TLS_CHACHA20_POLY1305_SHA256`, `ECDHE-RSA-AES256-GCM-SHA384`.
- **Certificate Verification**: Full certificate chain validation against CA bundle (`ssl.CERT_REQUIRED`).

### 2.2 Client Authentication
- **Worker Credentials**: Dedicated high-privilege service account credentials stored in environment variables:
  - `MQTT_BROKER_HOST=mqtt.thevahan.com`
  - `MQTT_BROKER_PORT=8883`
  - `MQTT_USERNAME=vahan_subscriber_daemon`
  - `MQTT_PASSWORD_FILE=/run/secrets/mqtt_worker_secret`
  - `MQTT_CA_CERT_PATH=/etc/ssl/certs/vahan_mqtt_ca.crt`
  - `MQTT_CLIENT_CERT_PATH=/etc/ssl/certs/vahan_subscriber.crt`
  - `MQTT_CLIENT_KEY_PATH=/etc/ssl/certs/vahan_subscriber.key`

---

## 3. Topic Architecture & Mapping

### 3.1 Standard Multi-Tenant Topic Structure
```text
vahan/{company_id}/devices/{imei}/telemetry
vahan/{company_id}/devices/{imei}/events
vahan/{company_id}/devices/{imei}/status
```

### 3.2 Wildcard Subscription
The Vahan subscriber daemon subscribes using MQTT wildcards:
```text
vahan/+/devices/+/telemetry
```
- First wildcard (`+`): `company_id` (e.g. `10` or `system`).
- Second wildcard (`+`): `imei` (15-digit hardware IMEI).

---

## 4. IMEI Identification & Multi-Tenant Isolation

1. **Extraction**:
   - Primary: Extracted directly from MQTT topic tokens (`topic.split("/")[3]`).
   - Secondary: Validated against JSON payload body (`payload.get("imei")` or `payload.get("device_id")`).
2. **Tenant Validation**:
   - The daemon extracts `topic_company_id = int(topic.split("/")[1])`.
   - The daemon queries Vahan's database:
     ```sql
     SELECT id, company_id, current_vehicle_id, connection_status 
     FROM assets 
     WHERE imei = :imei AND asset_type = 'GPS_DEVICE';
     ```
   - **Cross-Tenant Guard**: If `asset.company_id != topic_company_id`, the packet is immediately rejected, and a security audit warning is emitted to prevent cross-tenant spoofing.

---

## 5. Reconnection & Resilience Handling

1. **Persistent Session**:
   - Connects with `clean_session=False` and a stable Client ID (`vahan-subscriber-node-01`).
   - Subscription QoS: `QoS 1` (At least once).
2. **Exponential Backoff**:
   - Initial retry: 1.0 second.
   - Max backoff: 60.0 seconds.
   - Jitter: Uniform random jitter $\pm 20\%$ to prevent thundering herds on broker restart.
3. **Keepalive & Ping**:
   - `keepalive=30` seconds. Heartbeat pings sent automatically if idle.

---

## 6. Duplicate Detection & Batch Processing

1. **Buffering**: Incoming messages are placed into an in-memory `asyncio.Queue` (max size: 10,000 items).
2. **Batch Flusher**: A background task drains the queue every 500ms or when 100 packets accumulate.
3. **Database Fingerprinting**: Passes normalized events to `LocationService.process_hardware_batch()`, which validates:
   - SHA-256 fingerprint idempotency pre-check.
   - Unique constraint check on `VehicleLocation.event_fingerprint`.
   - Zero duplicate insertions.

---

## 7. Health Monitoring & Observability

- **Prometheus Metrics**:
  - `mqtt_messages_received_total{protocol="mqtt"}`
  - `mqtt_messages_processed_total{status="accepted|duplicate|rejected"}`
  - `mqtt_connection_state{state="connected|disconnected"}`
  - `mqtt_batch_duration_seconds`
- **Liveness Probe**:
  - The worker exposes a lightweight HTTP health endpoint on `http://127.0.0.1:9100/healthz`.
  - Returns `200 OK` if the MQTT connection loop is alive and last message was received within threshold.

---

## 8. Reference Implementation: `backend/workers/mqtt_subscriber.py`

```python
"""
FleetGuard / Vahan — Production Async MQTT Telematics Subscriber Daemon
"""
import asyncio
import json
import logging
import ssl
from typing import Dict, Any, List
from datetime import datetime, timezone
import aiomqtt
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from config import settings
from schemas.telematics import NormalizedHardwareEvent
from services.location_service import LocationService

logger = logging.getLogger("vahan.worker.mqtt")

class MQTTTelematicsSubscriber:
    def __init__(self):
        self.queue = asyncio.Queue(maxsize=10000)
        self.engine = create_async_engine(settings.DATABASE_URL)
        self.session_maker = async_sessionmaker(self.engine, expire_on_commit=False)
        self.is_running = False

    def _build_ssl_context(self) -> ssl.SSLContext:
        ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        if getattr(settings, "MQTT_CA_CERT_PATH", None):
            ctx.load_verify_locations(settings.MQTT_CA_CERT_PATH)
        return ctx

    async def run(self):
        self.is_running = True
        asyncio.create_task(self._batch_consumer())
        
        reconnect_interval = 1.0
        while self.is_running:
            try:
                ssl_ctx = self._build_ssl_context() if settings.MQTT_USE_TLS else None
                async with aiomqtt.Client(
                    hostname=settings.MQTT_BROKER_HOST,
                    port=settings.MQTT_BROKER_PORT,
                    username=settings.MQTT_USERNAME,
                    password=settings.MQTT_PASSWORD,
                    ssl_context=ssl_ctx,
                    client_id=f"vahan-sub-{settings.NODE_ID}",
                    clean_session=False,
                    keepalive=30
                ) as client:
                    reconnect_interval = 1.0
                    logger.info("Connected to MQTT broker. Subscribing to telemetry topics...")
                    await client.subscribe("vahan/+/devices/+/telemetry", qos=1)
                    
                    async for message in client.messages:
                        await self._on_message(message)
            except aiomqtt.MqttError as err:
                logger.error(f"MQTT connection error: {err}. Retrying in {reconnect_interval:.1f}s...")
                await asyncio.sleep(reconnect_interval)
                reconnect_interval = min(reconnect_interval * 2, 60.0)

    async def _on_message(self, message):
        try:
            payload = json.loads(message.payload.decode("utf-8"))
            topic_parts = message.topic.value.split("/")
            company_id = int(topic_parts[1])
            imei = topic_parts[3]

            event = NormalizedHardwareEvent(
                device_imei=imei,
                latitude=float(payload["latitude"]),
                longitude=float(payload["longitude"]),
                timestamp=datetime.fromisoformat(payload["timestamp"]).replace(tzinfo=timezone.utc),
                speed=float(payload.get("speed", 0.0)),
                heading=float(payload.get("heading", 0.0)),
                ignition_status=bool(payload.get("ignition", False)),
                source_metadata={"topic": message.topic.value, "company_id": company_id}
            )
            await self.queue.put(event)
        except Exception as e:
            logger.warning(f"Failed to parse MQTT packet: {e}")

    async def _batch_consumer(self):
        while self.is_running:
            batch = []
            try:
                # Wait for at least 1 item
                item = await asyncio.wait_for(self.queue.get(), timeout=0.5)
                batch.append(item)
                # Drain up to 100 items
                while len(batch) < 100 and not self.queue.empty():
                    batch.append(self.queue.get_nowait())
            except asyncio.TimeoutError:
                pass

            if batch:
                async with self.session_maker() as db:
                    await LocationService.process_hardware_batch(db, batch)
                    await db.commit()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    subscriber = MQTTTelematicsSubscriber()
    asyncio.run(subscriber.run())
```
