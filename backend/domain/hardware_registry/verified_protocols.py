"""
FleetGuard / Vahan — Verified Hardware & GPS Protocol Compatibility Registry
Defines verified manufacturers, models, firmware compatibility, default ports,
and telemetry capabilities for Universal GPS Integration.
"""

from typing import Dict, Any, List
from pydantic import BaseModel


class ProtocolSpec(BaseModel):
    id: str
    name: str
    transport: str  # TCP, UDP, HTTP, MQTT, REST
    default_port: int
    supports_ignition: bool
    supports_heading: bool
    supports_speed: bool
    supports_altitude: bool
    supports_battery: bool
    description: str


class ManufacturerSpec(BaseModel):
    id: str
    name: str
    country: str
    models: List[str]
    supported_protocols: List[str]
    recommended_connection: str  # DIRECT_HARDWARE, TCP_DEVICE, GPS_PROVIDER_API, MQTT_DEVICE
    notes: str


# --- Verified GPS Protocols ---
VERIFIED_PROTOCOLS: Dict[str, ProtocolSpec] = {
    "GT06": ProtocolSpec(
        id="GT06",
        name="Concox / Jimi GT06 / GT06N",
        transport="TCP",
        default_port=5023,
        supports_ignition=True,
        supports_heading=True,
        supports_speed=True,
        supports_altitude=False,
        supports_battery=True,
        description="Standard binary protocol used by Jimi IoT, Concox, and hundreds of OEM GPS tracking units."
    ),
    "TELTONIKA_CODEC8": ProtocolSpec(
        id="TELTONIKA_CODEC8",
        name="Teltonika Codec 8",
        transport="TCP",
        default_port=5027,
        supports_ignition=True,
        supports_heading=True,
        supports_speed=True,
        supports_altitude=True,
        supports_battery=True,
        description="Teltonika standard binary protocol with AVL data packet parsing (FMB920, FMB120)."
    ),
    "TELTONIKA_CODEC8E": ProtocolSpec(
        id="TELTONIKA_CODEC8E",
        name="Teltonika Codec 8 Extended",
        transport="TCP",
        default_port=5027,
        supports_ignition=True,
        supports_heading=True,
        supports_speed=True,
        supports_altitude=True,
        supports_battery=True,
        description="Extended AVL data packet supporting CAN-bus telemetry, BLE sensors, and advanced I/O."
    ),
    "TELTONIKA_CODEC16": ProtocolSpec(
        id="TELTONIKA_CODEC16",
        name="Teltonika Codec 16",
        transport="TCP",
        default_port=5027,
        supports_ignition=True,
        supports_heading=True,
        supports_speed=True,
        supports_altitude=True,
        supports_battery=True,
        description="High-density binary protocol used for rich vehicle telematics and video telematics data."
    ),
    "TK103": ProtocolSpec(
        id="TK103",
        name="Coban / Xexun TK103 / GPS103",
        transport="TCP",
        default_port=5002,
        supports_ignition=True,
        supports_heading=True,
        supports_speed=True,
        supports_altitude=False,
        supports_battery=False,
        description="Widely deployed ASCII text protocol for vehicle trackers and asset locators."
    ),
    "H02": ProtocolSpec(
        id="H02",
        name="H02 Protocol",
        transport="TCP",
        default_port=5013,
        supports_ignition=True,
        supports_heading=True,
        supports_speed=True,
        supports_altitude=False,
        supports_battery=True,
        description="Compact ASCII/binary protocol common in budget OBD and trailer trackers."
    ),
    "JT808": ProtocolSpec(
        id="JT808",
        name="JT/T 808 National Standard",
        transport="TCP",
        default_port=5088,
        supports_ignition=True,
        supports_heading=True,
        supports_speed=True,
        supports_altitude=True,
        supports_battery=True,
        description="Chinese National Standard protocol for commercial vehicle telematics and dashcams."
    ),
    "QUECLINK": ProtocolSpec(
        id="QUECLINK",
        name="Queclink @Track Protocol",
        transport="TCP",
        default_port=5004,
        supports_ignition=True,
        supports_heading=True,
        supports_speed=True,
        supports_altitude=True,
        supports_battery=True,
        description="Queclink proprietary ASCII @Track protocol with comprehensive acknowledge & command support."
    ),
    "AIS140": ProtocolSpec(
        id="AIS140",
        name="AIS-140 Indian Telematics Standard",
        transport="TCP",
        default_port=5140,
        supports_ignition=True,
        supports_heading=True,
        supports_speed=True,
        supports_altitude=True,
        supports_battery=True,
        description="Mandatory Indian Government AIS-140 Intelligent Transport System specification with SOS alerts."
    ),
    "MQTT": ProtocolSpec(
        id="MQTT",
        name="MQTT Telematics Stream",
        transport="MQTT",
        default_port=8883,
        supports_ignition=True,
        supports_heading=True,
        supports_speed=True,
        supports_altitude=True,
        supports_battery=True,
        description="Pub/Sub JSON telemetry over MQTT topics for connected vehicles and modern IoT gateways."
    ),
    "HTTP_REST": ProtocolSpec(
        id="HTTP_REST",
        name="HTTP / HTTPS REST Webhook",
        transport="HTTP",
        default_port=443,
        supports_ignition=True,
        supports_heading=True,
        supports_speed=True,
        supports_altitude=True,
        supports_battery=True,
        description="Direct HTTP POST endpoint ingestion for cellular trackers and custom cloud forwarders."
    ),
    "TRACCAR_WEBHOOK": ProtocolSpec(
        id="TRACCAR_WEBHOOK",
        name="Traccar Ingestion Engine Forwarder",
        transport="HTTP",
        default_port=8082,
        supports_ignition=True,
        supports_heading=True,
        supports_speed=True,
        supports_altitude=True,
        supports_battery=True,
        description="Universal protocol aggregation via local or hosted Traccar multi-protocol gateway."
    ),
}


# --- Verified Hardware Manufacturers ---
VERIFIED_MANUFACTURERS: List[ManufacturerSpec] = [
    ManufacturerSpec(
        id="teltonika",
        name="Teltonika Telematics",
        country="Lithuania",
        models=["FMB920", "FMB120", "FMB140", "FMC130", "FMM130", "FMC640", "TFT100"],
        supported_protocols=["TELTONIKA_CODEC8", "TELTONIKA_CODEC8E", "TELTONIKA_CODEC16", "MQTT"],
        recommended_connection="DIRECT_HARDWARE",
        notes="Industry benchmark for reliability. Codec 8 / 8E verified."
    ),
    ManufacturerSpec(
        id="jimi_concox",
        name="Jimi IoT / Concox",
        country="China",
        models=["GT06N", "WeTrack2", "VG02U", "JM-VL03", "JM-VG04", "JM-LL01"],
        supported_protocols=["GT06", "HTTP_REST"],
        recommended_connection="DIRECT_HARDWARE",
        notes="High-volume fleet trackers. GT06 protocol verified."
    ),
    ManufacturerSpec(
        id="queclink",
        name="Queclink Wireless",
        country="China",
        models=["GL300", "GV55", "GV300", "GV75", "GV500"],
        supported_protocols=["QUECLINK", "HTTP_REST"],
        recommended_connection="DIRECT_HARDWARE",
        notes="@Track protocol verified for asset and vehicle tracking."
    ),
    ManufacturerSpec(
        id="coban",
        name="Coban / Xexun",
        country="China",
        models=["TK103A", "TK103B", "TK102", "GPS103"],
        supported_protocols=["TK103"],
        recommended_connection="DIRECT_HARDWARE",
        notes="Standard TK103 protocol units."
    ),
    ManufacturerSpec(
        id="ruptela",
        name="Ruptela",
        country="Lithuania",
        models=["Eco4 Light", "Eco4 Light+", "Trace5", "Pro5"],
        supported_protocols=["TELTONIKA_CODEC8", "HTTP_REST"],
        recommended_connection="DIRECT_HARDWARE",
        notes="European commercial telematics units."
    ),
    ManufacturerSpec(
        id="ais140_certified",
        name="AIS-140 Certified (Indian Standard)",
        country="India",
        models=["Minda iConnect", "Rosmerta Telematics", "Arya Omnitalk", "Matchwell AIS", "Blackcat AIS140"],
        supported_protocols=["AIS140", "HTTP_REST"],
        recommended_connection="DIRECT_HARDWARE",
        notes="Government-mandated commercial vehicle tracking with emergency panic button support."
    ),
    ManufacturerSpec(
        id="generic_iot",
        name="Generic IoT / OBD-II / Cloud Forwarder",
        country="Global",
        models=["Smart OBD-II", "Solar Trailer Tracker", "Bluetooth Beacon Hub", "Asset Tracker Pro"],
        supported_protocols=["HTTP_REST", "MQTT", "TRACCAR_WEBHOOK"],
        recommended_connection="GPS_PROVIDER_API",
        notes="Supports custom REST webhooks, MQTT, and Traccar forwarders."
    ),
    ManufacturerSpec(
        id="other",
        name="Other Manufacturer / Custom Integration",
        country="Custom",
        models=["Custom Hardware", "Third-Party Server", "White-Label Unit"],
        supported_protocols=["HTTP_REST", "MQTT", "GT06", "TELTONIKA_CODEC8", "TK103", "TRACCAR_WEBHOOK"],
        recommended_connection="OTHER",
        notes="Manual parameter configuration."
    ),
]


def get_verified_registry() -> Dict[str, Any]:
    """Returns the complete compatibility registry for frontend inspection and selection."""
    return {
        "protocols": [p.model_dump() for p in VERIFIED_PROTOCOLS.values()],
        "manufacturers": [m.model_dump() for m in VERIFIED_MANUFACTURERS],
        "connection_types": [
            {"id": "GPS_PROVIDER_API", "name": "GPS Provider Cloud API", "description": "Connect via provider cloud REST API (Traccar, Teltonika Fleet, etc.)"},
            {"id": "DIRECT_HARDWARE", "name": "Direct GPS Hardware", "description": "Configure device directly to send telemetry to Vahan GPS gateway"},
            {"id": "TCP_DEVICE", "name": "Direct TCP Socket Protocol", "description": "Raw TCP socket parsing (GT06, Teltonika, Queclink, AIS-140)"},
            {"id": "MQTT_DEVICE", "name": "MQTT IoT Stream", "description": "Subscribe to JSON telemetry from an MQTT broker"},
            {"id": "WEBHOOK", "name": "Webhook Ingestion", "description": "Receive normalized HTTP POST payloads with HMAC token verification"},
            {"id": "OTHER", "name": "Other Supported Integration", "description": "Custom endpoint or specialized telematics proxy"},
        ]
    }
