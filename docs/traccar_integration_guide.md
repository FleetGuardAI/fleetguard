# Vahan Universal GPS Telematics & Traccar Integration Architecture Guide

## 1. Executive Architecture Overview

Vahan implements a **provider-independent, multi-protocol GPS telematics architecture**. Rather than binding the platform to a single hardware vendor or single cloud platform API key, Vahan accepts telematics frames from virtually any hardware manufacturer on the global market.

```
+---------------------------------------------------------------------------------------------------+
|                                         GPS HARDWARE UNITS                                        |
|  [Teltonika Codec 8/8E/16]  [Concox / Jimi GT06]  [Coban TK103]  [AIS-140]  [MQTT / HTTP IoT]     |
+---------------------------------------------------------------------------------------------------+
                                                  │ (Cellular 2G/4G/LTE TCP/UDP/MQTT)
                                                  ▼
+---------------------------------------------------------------------------------------------------+
|                                 TELEMATICS INGESTION ENGINE                                       |
|  Traccar Open-Source Protocol Gateway  /  Direct Vahan Async TCP Listeners (Ports 5001-5140)      |
|  - Frame Parsing & Checksum Verification                                                          |
|  - Native Protocol Decoding (GT06, Codec 8, TK103, H02, JT/T 808, Queclink, AIS-140)             |
+---------------------------------------------------------------------------------------------------+
                                                  │ (Internal JSON Forwarding Webhook)
                                                  ▼
+---------------------------------------------------------------------------------------------------+
|                                     VAHAN BACKEND CORE                                            |
|  Endpoint: POST /api/v1/tracking/telematics/traccar                                               |
|  1. Device Identification via IMEI / Serial Number                                                |
|  2. Company Tenant Isolation Verification (Asset.company_id)                                      |
|  3. Deduplication Check (Timestamp + Coordinates)                                                 |
|  4. Coordinate & Telemetry Normalization (Speed, Heading, Ignition, Battery Voltage)              |
|  5. Non-Destructive Update: Asset Telemetry Cache + VehicleLocation History Table                 |
+---------------------------------------------------------------------------------------------------+
                                                  │ (PostgreSQL / Supabase + WebSockets)
                                                  ▼
+---------------------------------------------------------------------------------------------------+
|                                      VAHAN OWNER DASHBOARD                                        |
|  - Real-Time Hardware Summary Cards (Connected, Disconnected, Pending, With/Without GPS)          |
|  - Multi-Filter Device Management Table (Search, Status, Manufacturer, Provider, Assignment)       |
|  - Interactive Leaflet Live Tracking Map with Vehicle Heading & Pulse                             |
|  - Historical Route Playback (1x/2x/5x Speed, Distance Traveled km, Max/Avg Speed Analytics)      |
+---------------------------------------------------------------------------------------------------+
```

---

## 2. Supported Protocols & Verified Compatibility Registry

Vahan maintains an authoritative compatibility registry mapping manufacturers, default ports, and validated protocols:

| Manufacturer | Sample Models | Supported Protocol | Default Port | Ingestion Adapter |
|---|---|---|---|---|
| **Teltonika** | FMB920, FMC130, FMB120, FMC920, FMC640 | `TELTONIKA_CODEC8`, `TELTONIKA_CODEC8E`, `TELTONIKA_CODEC16` | `5027` | Native Traccar / TCP Decoder |
| **Concox / Jimi IoT** | WeTrack2, GT06N, JM-VL02, JM-VL03, JM-LG01 | `GT06`, `GT06N` | `5023` | Native Traccar / GT06Provider |
| **Coban** | TK103A, TK103B, TK303G, GPS311 | `TK103`, `GPS103` | `5001` | Native Traccar / TK103Provider |
| **Queclink** | GV300, GV50, GV500, GL300 | `QUECLINK_AT_TRACK` | `5004` | Native Traccar / ASCII Ingestion |
| **AIS-140 IRNSS** | Rosmerta, Minda, Arya Omni, Indian Certified | `AIS140` | `5140` | AIS140Provider (NMEA/M2M) |
| **Sinotrack** | ST-901, ST-902, ST-906 | `H02` | `5013` | Native Traccar / H02 Adapter |
| **Chinese National**| Heavy Freight Commercial Units | `JT808` (JT/T 808) | `5008` | Native Traccar / JT808 Adapter |
| **MQTT IoT** | Custom Gateways, EMQX, AWS IoT Core | `MQTT` | `8883` | MQTTProvider / JSON Topic |
| **Cloud REST APIs** | Traccar Cloud, Teltonika FOTA, Tracksolid | `HTTP_REST` | `443` | Polling & Webhook Clients |

---

## 3. Traccar Deployment & Production Configuration

### Quickstart with Docker Compose

A dedicated `docker-compose.traccar.yml` is provided at the repository root:

```bash
docker compose -f docker-compose.traccar.yml up -d
```

### Forwarder Configuration (`docs/traccar/traccar.xml`)

Traccar automatically forwards ingested, decoded positions directly to Vahan via internal webhook, authenticated with a shared secret to prevent unauthorized telemetry submission:

```xml
<entry key='forward.enable'>true</entry>
<entry key='forward.url'>http://vahan-backend:8000/api/v1/tracking/telematics/traccar</entry>
<entry key='forward.json'>true</entry>
<entry key='forward.header'>Content-Type: application/json&#x0A;X-Telematics-Secret: ${env.TELEMATICS_WEBHOOK_SECRET}</entry>

<!-- Anti-jitter & duplicate coordinate rejection -->
<entry key='filter.enable'>true</entry>
<entry key='filter.duplicate'>true</entry>
<entry key='filter.distance'>10</entry>
```

#### Webhook Authentication & Security Requirements

1. **Header Authentication Mandatory (`X-Telematics-Secret`)**:
   The forwarder MUST include the `X-Telematics-Secret` HTTP header matching the backend environment variable `TELEMATICS_WEBHOOK_SECRET`.
   Traccar Docker injects this via `CONFIG_USE_ENVIRONMENT_VARIABLES=true` and `FORWARD_HEADER=Content-Type: application/json\nX-Telematics-Secret: ${TELEMATICS_WEBHOOK_SECRET}`.
2. **Query-String Fallback Explicitly Disabled**:
   To prevent secret tokens from leaking into load balancer access logs, reverse proxy metrics (Nginx/Cloudflare), and browser histories, query string authentication (`?secret=...`) is strictly rejected by Vahan with HTTP 401.
3. **Rejection Behavior**:
   - If `TELEMATICS_WEBHOOK_SECRET` is not configured on the backend, endpoints return `503 Service Unavailable` with `"Telematics ingestion not configured"`.
   - If the incoming secret is missing or does not match, endpoints immediately return `401 Unauthorized` with `"Invalid telematics secret"`, preventing spoofed coordinates from reaching the processing engine.
4. **Environment Configuration**:
   Never hardcode secrets in config files. Pass `TELEMATICS_WEBHOOK_SECRET` securely via environment variables or secret managers (e.g., Docker secrets, Kubernetes secrets, or cloud platform env vars).

### Device SMS Configuration Syntax

To point cellular trackers to your Vahan ingestion cluster:

- **Concox / Jimi GT06**:
  `SERVER,1,<VAHAN_HOST>,5023,0#`
  `TIMER,10,60#` (Report every 10s moving, 60s stopped)
- **Coban TK103**:
  `adminip123456 <VAHAN_HOST> 5001`
  `fix030s***n123456`
- **Teltonika FMB920**:
  Configure APN, GPRS Domain (`<VAHAN_HOST>`), and Port (`5027`) via Teltonika Configurator over USB or SMS.

---

## 4. Multi-Tenant Isolation & Credential Security

1. **Company Scoping**: Every registered device in `assets` has a mandatory `company_id` foreign key with indexed tenant lookup. API endpoints reject any access attempt across company boundaries.
2. **Encrypted Credentials**: GPS provider passwords, API keys, and MQTT tokens are encrypted at rest using AES-GCM (Fernet key derived from `SECRET_KEY`).
3. **Redaction**: Responses from `/v1/assets/hardware/*` explicitly omit credentials, tokens, and sensitive authentication headers before returning to the frontend.
4. **Non-Destructive Reassignment**: Vehicle assignment transitions preserve historical records in `vehicle_locations` and audit log changes in `asset_history`.
