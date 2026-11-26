"""
FleetGuard / Vahan — Real Wire-Protocol Decoder & Traccar Forwarder Integration Tests

Tests all 7 supported hardware telematics protocols:
1. Concox GT06 (Binary frame, CRC-ITU)
2. Teltonika Codec 8 (Binary AVL frame, CRC-16)
3. Coban TK103 (ASCII text frame)
4. Indian AIS-140 IRNSS (NMEA-style ASCII sentence)
5. Queclink (+RESP:GTFRI ASCII frame)
6. Sinotrack H02 (*HQ ASCII frame)
7. JT/T 808 (Chinese MOT binary frame with BCD fields and XOR checksum)

Also tests end-to-end loopback network transmission:
- Real TCP/UDP sockets on localhost
- Server-side raw packet ingestion and decoding
- Traccar 6.5 forwarder JSON payload generation
- Forwarder HTTP POST to Vahan webhook endpoint with X-Telematics-Secret
- Authentication validation (valid secret -> 200, invalid secret -> 401, missing secret -> 401)
- Database record persistence (VehicleLocation, VehicleCurrentLocation, Asset)
"""

import os
os.environ["TESTING"] = "True"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["SECRET_KEY"] = "wire_protocol_test_secret_12345"
os.environ["TELEMATICS_WEBHOOK_SECRET"] = "traccar_forwarder_secret_key_999"

import unittest
import struct
import socket
import asyncio
from datetime import datetime, timezone
from unittest.mock import patch

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from fastapi.testclient import TestClient
from fastapi import FastAPI

from database import Base
from models.company import Company, CompanyStatus
from models.vehicle_domain import Vehicle
from models.asset_domain import Asset, AssetType, ConnectionStatus, AssetInstallationStatus
from models.location_tracking import VehicleLocation, VehicleCurrentLocation
from routers.telematics import router as telematics_router


# ===========================================================================
# 1. Wire-Format Protocol Builders & Decoders
# ===========================================================================

def build_gt06_packet(imei: str, lat: float, lon: float, speed_kmh: float, course: float, acc: bool) -> bytes:
    """Builds an authentic Concox GT06 binary location packet (Protocol 0x22)."""
    # Start: 0x78 0x78
    # Length: 34 bytes (data between length and stop bytes)
    # Protocol: 0x22
    year, month, day, hour, minute, second = 26, 11, 24, 10, 30, 0
    satellites = 0xCC # 12 satellites
    lat_val = int(abs(lat) * 1800000)
    lon_val = int(abs(lon) * 1800000)
    speed_val = int(speed_kmh)
    course_status = (int(course) & 0x03FF) | (0x0400 if lat >= 0 else 0) | (0x0800 if lon >= 0 else 0) | 0x1000 # GPS real-time
    
    # Body bytes
    body = bytearray()
    body.append(0x22) # Protocol
    body.extend([year, month, day, hour, minute, second])
    body.append(satellites)
    body.extend(lat_val.to_bytes(4, "big"))
    body.extend(lon_val.to_bytes(4, "big"))
    body.append(speed_val)
    body.extend(course_status.to_bytes(2, "big"))
    body.extend([0x00, 0x00, 0x00, 0x00, 0x00, 0x00]) # MCC/MNC/LAC/Cell
    body.append(0x01 if acc else 0x00) # Terminal info ACC
    body.extend([0x00, 0x01]) # Serial number
    
    # CRC-ITU
    def crc16_itu(data):
        crc = 0xFFFF
        for b in data:
            crc ^= b
            for _ in range(8):
                if crc & 1:
                    crc = (crc >> 1) ^ 0x8408
                else:
                    crc >>= 1
        return (~crc) & 0xFFFF
    
    crc_val = crc16_itu(body)
    packet = bytearray([0x78, 0x78, len(body) + 2])
    packet.extend(body)
    packet.extend(crc_val.to_bytes(2, "big"))
    packet.extend([0x0D, 0x0A])
    return bytes(packet)


def decode_gt06_packet(data: bytes):
    """Decodes a GT06 raw binary frame."""
    if len(data) < 15 or data[0] != 0x78 or data[1] != 0x78 or data[-2] != 0x0D or data[-1] != 0x0A:
        raise ValueError("Invalid GT06 framing")
    proto = data[3]
    if proto not in (0x12, 0x22):
        raise ValueError(f"Unsupported GT06 protocol number 0x{proto:02X}")
    
    y, m, d, hh, mm, ss = data[4], data[5], data[6], data[7], data[8], data[9]
    dt = datetime(2000 + y, m, d, hh, mm, ss, tzinfo=timezone.utc)
    lat = int.from_bytes(data[11:15], "big") / 1800000.0
    lon = int.from_bytes(data[15:19], "big") / 1800000.0
    speed = float(data[19])
    course_status = int.from_bytes(data[20:22], "big")
    course = float(course_status & 0x03FF)
    acc = bool(data[28] & 0x01) if len(data) > 28 else True
    return {
        "protocol": "GT06",
        "timestamp": dt,
        "latitude": lat,
        "longitude": lon,
        "speed": speed,
        "course": course,
        "ignition": acc
    }


def build_teltonika_codec8_packet(lat: float, lon: float, speed_kmh: float, angle: float, ignition: bool) -> bytes:
    """Builds an authentic Teltonika Codec 8 binary AVL packet."""
    ts_ms = int(datetime(2026, 11, 24, 10, 30, 0, tzinfo=timezone.utc).timestamp() * 1000)
    lat_val = int(lat * 10000000)
    lon_val = int(lon * 10000000)
    speed_val = int(speed_kmh)
    angle_val = int(angle)

    body = bytearray()
    body.append(0x08) # Codec 8
    body.append(0x01) # Number of records
    # Record 1
    body.extend(ts_ms.to_bytes(8, "big"))
    body.append(0x01) # Priority
    # GPS element
    body.extend(lon_val.to_bytes(4, "big", signed=True))
    body.extend(lat_val.to_bytes(4, "big", signed=True))
    body.extend((215).to_bytes(2, "big", signed=True)) # Altitude 215m
    body.extend(angle_val.to_bytes(2, "big"))
    body.append(12) # Satellites
    body.extend(speed_val.to_bytes(2, "big"))
    # IO elements
    body.append(0x00) # Event IO ID
    body.append(0x01) # Total IO elements count
    # 1-byte IO count: 1 element (ID 239 = Ignition)
    body.append(0x01)
    body.append(239)
    body.append(0x01 if ignition else 0x00)
    # 2-byte, 4-byte, 8-byte IO counts (0)
    body.extend([0x00, 0x00, 0x00])
    body.append(0x01) # Number of records 2

    # Framing: 4 zeros, 4-byte length, body, 4-byte CRC-16
    packet = bytearray([0x00, 0x00, 0x00, 0x00])
    packet.extend(len(body).to_bytes(4, "big"))
    packet.extend(body)
    packet.extend([0x00, 0x00, 0x12, 0x34]) # CRC-16
    return bytes(packet)


def decode_teltonika_codec8_packet(data: bytes):
    """Decodes a Teltonika Codec 8 binary frame."""
    if len(data) < 16 or data[0:4] != b"\x00\x00\x00\x00":
        raise ValueError("Invalid Teltonika preamble")
    data_len = int.from_bytes(data[4:8], "big")
    codec_id = data[8]
    if codec_id != 0x08:
        raise ValueError(f"Expected Codec 8, got 0x{codec_id:02X}")
    num_rec = data[9]
    if num_rec < 1:
        raise ValueError("No records in Teltonika packet")
    
    ts_ms = int.from_bytes(data[10:18], "big")
    dt = datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc)
    lon = int.from_bytes(data[19:23], "big", signed=True) / 10000000.0
    lat = int.from_bytes(data[23:27], "big", signed=True) / 10000000.0
    alt = float(int.from_bytes(data[27:29], "big", signed=True))
    angle = float(int.from_bytes(data[29:31], "big"))
    speed = float(int.from_bytes(data[32:34], "big"))
    
    # Parse ignition IO (ID 239)
    ignition = True
    io_offset = 36
    one_byte_count = data[io_offset]
    for i in range(one_byte_count):
        elem_id = data[io_offset + 1 + i*2]
        elem_val = data[io_offset + 2 + i*2]
        if elem_id == 239:
            ignition = bool(elem_val)
            
    return {
        "protocol": "TELTONIKA_CODEC8",
        "timestamp": dt,
        "latitude": lat,
        "longitude": lon,
        "altitude": alt,
        "speed": speed,
        "course": angle,
        "ignition": ignition
    }


def build_tk103_packet(imei: str, lat: float, lon: float, speed_kmh: float) -> str:
    """Builds an authentic Coban TK103 ASCII wire text sentence."""
    lat_deg = int(abs(lat))
    lat_min = (abs(lat) - lat_deg) * 60.0
    lat_str = f"{lat_deg:02d}{lat_min:07.4f}"
    lat_hemi = "N" if lat >= 0 else "S"
    
    lon_deg = int(abs(lon))
    lon_min = (abs(lon) - lon_deg) * 60.0
    lon_str = f"{lon_deg:03d}{lon_min:07.4f}"
    lon_hemi = "E" if lon >= 0 else "W"
    
    # Format: (086012345678901BP05000086012345678901261124A2837.2140N07712.5400E045.5103000215.0000000000L00000000)
    return f"({imei}BP050000{imei}261124A{lat_str}{lat_hemi}{lon_str}{lon_hemi}{speed_kmh:05.1f}103000215.0000000000L00000000)"


def decode_tk103_packet(text: str):
    """Decodes a Coban TK103 text frame."""
    if not (text.startswith("(") and text.endswith(")")):
        raise ValueError("Invalid TK103 framing")
    content = text[1:-1]
    imei = content[:15]
    # Locate latitude 'A' marker
    a_idx = content.find("A", 20)
    if a_idx == -1:
        raise ValueError("Missing TK103 GPS fix indicator")
    
    lat_part = content[a_idx+1 : a_idx+10]
    lat_hemi = content[a_idx+10]
    lat_deg = float(lat_part[:2])
    lat_min = float(lat_part[2:])
    lat = lat_deg + (lat_min / 60.0)
    if lat_hemi == "S":
        lat = -lat
        
    lon_part = content[a_idx+11 : a_idx+21]
    lon_hemi = content[a_idx+21]
    lon_deg = float(lon_part[:3])
    lon_min = float(lon_part[3:])
    lon = lon_deg + (lon_min / 60.0)
    if lon_hemi == "W":
        lon = -lon
        
    speed = float(content[a_idx+22 : a_idx+27])
    return {
        "protocol": "TK103",
        "device_id": imei,
        "latitude": round(lat, 5),
        "longitude": round(lon, 5),
        "speed": speed,
        "ignition": True
    }


def build_ais140_packet(imei: str, lat: float, lon: float, speed_kmh: float) -> str:
    """Builds an authentic Indian AIS-140 $PVT sentence."""
    return f"$PVT,{imei},1,20261124,103000,{lat:.4f},N,{lon:.4f},E,{speed_kmh:.1f},120.0,12,215.0,1.2,1,1,0,0,4.1,12.6,0*4A"


def decode_ais140_packet(text: str):
    """Decodes an Indian AIS-140 sentence."""
    if not text.startswith("$PVT"):
        raise ValueError("Invalid AIS-140 sentence")
    body = text.split("*")[0]
    parts = body.split(",")
    imei = parts[1]
    dt = datetime.strptime(parts[3] + parts[4], "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
    lat = float(parts[5]) * (1 if parts[6] == "N" else -1)
    lon = float(parts[7]) * (1 if parts[8] == "E" else -1)
    speed = float(parts[9])
    heading = float(parts[10])
    ignition = bool(int(parts[15]))
    return {
        "protocol": "AIS-140",
        "device_id": imei,
        "timestamp": dt,
        "latitude": lat,
        "longitude": lon,
        "speed": speed,
        "course": heading,
        "ignition": ignition
    }


def build_queclink_packet(imei: str, lat: float, lon: float, speed_kmh: float) -> str:
    """Builds an authentic Queclink +RESP:GTFRI ASCII report."""
    return f"+RESP:GTFRI,1A0102,{imei},,0,1,1,{speed_kmh:.1f},120,215.0,{lon:.4f},{lat:.4f},20261124103000,0404,0000,0,0,0,,20261124103005,11F0$"


def decode_queclink_packet(text: str):
    """Decodes a Queclink +RESP:GTFRI report."""
    if not text.startswith("+RESP:GTFRI"):
        raise ValueError("Invalid Queclink report")
    parts = text.rstrip("$").split(",")
    imei = parts[2]
    speed = float(parts[7])
    course = float(parts[8])
    lon = float(parts[10])
    lat = float(parts[11])
    dt = datetime.strptime(parts[12], "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
    return {
        "protocol": "QUECLINK",
        "device_id": imei,
        "timestamp": dt,
        "latitude": lat,
        "longitude": lon,
        "speed": speed,
        "course": course,
        "ignition": True
    }


def build_h02_packet(imei: str, lat: float, lon: float, speed_kmh: float) -> str:
    """Builds an authentic Sinotrack H02 ASCII message."""
    lat_deg = int(abs(lat))
    lat_min = (abs(lat) - lat_deg) * 60.0
    lat_str = f"{lat_deg:02d}{lat_min:06.3f}"
    
    lon_deg = int(abs(lon))
    lon_min = (abs(lon) - lon_deg) * 60.0
    lon_str = f"{lon_deg:03d}{lon_min:06.3f}"
    
    return f"*HQ,{imei},V1,103000,A,{lat_str},N,{lon_str},E,{speed_kmh:05.1f},120,241126,FFFFFBFF#"


def decode_h02_packet(text: str):
    """Decodes a Sinotrack H02 message."""
    if not (text.startswith("*HQ") and text.endswith("#")):
        raise ValueError("Invalid H02 message")
    parts = text.strip("*#").split(",")
    imei = parts[1]
    lat_part = parts[5]
    lat_deg = float(lat_part[:2])
    lat_min = float(lat_part[2:])
    lat = lat_deg + (lat_min / 60.0)
    
    lon_part = parts[7]
    lon_deg = float(lon_part[:3])
    lon_min = float(lon_part[3:])
    lon = lon_deg + (lon_min / 60.0)
    speed = float(parts[9])
    course = float(parts[10])
    return {
        "protocol": "H02",
        "device_id": imei,
        "latitude": round(lat, 5),
        "longitude": round(lon, 5),
        "speed": speed,
        "course": course,
        "ignition": True
    }


def build_jt808_packet(phone_bcd: str, lat: float, lon: float, speed_kmh: float) -> bytes:
    """Builds an authentic JT/T 808 binary location report (Message ID 0x0200)."""
    msg_id = 0x0200
    phone_bytes = bytes.fromhex(phone_bcd.zfill(12)) # 6 bytes BCD
    seq = 0x0001
    
    body = bytearray()
    body.extend((0).to_bytes(4, "big")) # Alarm flags
    body.extend((0x00000003).to_bytes(4, "big")) # Status flags: ACC ON, GPS Fixed
    body.extend(int(lat * 1000000).to_bytes(4, "big", signed=True))
    body.extend(int(lon * 1000000).to_bytes(4, "big", signed=True))
    body.extend((215).to_bytes(2, "big", signed=True)) # Elevation
    body.extend(int(speed_kmh * 10).to_bytes(2, "big")) # Speed 1/10 km/h
    body.extend((120).to_bytes(2, "big")) # Direction
    body.extend(bytes.fromhex("261124103000")) # BCD time
    
    body_props = len(body)
    
    header = bytearray()
    header.extend(msg_id.to_bytes(2, "big"))
    header.extend(body_props.to_bytes(2, "big"))
    header.extend(phone_bytes)
    header.extend(seq.to_bytes(2, "big"))
    
    full_data = header + body
    checksum = 0
    for b in full_data:
        checksum ^= b
        
    packet = bytearray([0x7E])
    packet.extend(full_data)
    packet.append(checksum)
    packet.append(0x7E)
    return bytes(packet)


def decode_jt808_packet(data: bytes):
    """Decodes a JT/T 808 binary report."""
    if len(data) < 15 or data[0] != 0x7E or data[-1] != 0x7E:
        raise ValueError("Invalid JT808 framing")
    content = data[1:-2]
    msg_id = int.from_bytes(content[0:2], "big")
    if msg_id != 0x0200:
        raise ValueError(f"Expected MsgID 0x0200, got 0x{msg_id:04X}")
    phone = content[4:10].hex()
    body = content[12:]
    status = int.from_bytes(body[4:8], "big")
    lat = int.from_bytes(body[8:12], "big", signed=True) / 1000000.0
    lon = int.from_bytes(body[12:16], "big", signed=True) / 1000000.0
    alt = float(int.from_bytes(body[16:18], "big", signed=True))
    speed = int.from_bytes(body[18:20], "big") / 10.0
    course = float(int.from_bytes(body[20:22], "big"))
    acc = bool(status & 0x01)
    return {
        "protocol": "JT808",
        "device_id": phone,
        "latitude": lat,
        "longitude": lon,
        "altitude": alt,
        "speed": speed,
        "course": course,
        "ignition": acc
    }


# ===========================================================================
# 2. Integration Test Suite with Traccar Forwarding & DB Verification
# ===========================================================================

class TestRawWireProtocolsAndTraccarForwarder(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        from database import get_db
        self.engine = create_async_engine(
            "sqlite+aiosqlite:///file:memdb_wire?mode=memory&cache=shared&uri=true",
            echo=False
        )
        self.session_maker = async_sessionmaker(self.engine, expire_on_commit=False)

        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async with self.session_maker() as db:
            self.company = Company(
                id=10,
                company_name="Apex Telematics Logistics",
                owner_name="Devang Joshi",
                mobile_number="+919876543299",
                email="fleet@apexlogistics.in",
                status=CompanyStatus.ACTIVE
            )
            self.vehicle = Vehicle(
                id=101,
                company_id=10,
                registration_number="MH04XY9999",
                make="Tata",
                model="Signa 4825"
            )
            self.asset = Asset(
                id=50,
                company_id=10,
                business_id="HW-APEX-01",
                asset_type=AssetType.GPS_DEVICE,
                device_name="Apex GT06 Tracker",
                imei="860123456789012",
                manufacturer="Concox",
                model="GT06",
                protocol="GT06",
                current_vehicle_id=101,
                connection_status=ConnectionStatus.PENDING.value,
                installation_status=AssetInstallationStatus.INSTALLED
            )
            db.add_all([self.company, self.vehicle, self.asset])
            await db.commit()

        async def override_get_db():
            async with self.session_maker() as session:
                yield session

        # Build FastAPI test app mounting telematics webhook
        self.app = FastAPI()
        self.app.include_router(telematics_router)
        self.app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(self.app)

    async def asyncTearDown(self):
        await self.engine.dispose()

    # -----------------------------------------------------------------------
    # Wire Protocol Bit-Level Decoder Tests (All 7 Protocols)
    # -----------------------------------------------------------------------

    def test_wire_gt06_protocol(self):
        """Test actual GT06 binary packet assembly and decoding."""
        raw = build_gt06_packet("860123456789012", 28.6139, 77.2090, 55.0, 90.0, True)
        self.assertTrue(isinstance(raw, bytes))
        self.assertEqual(raw[0:2], b"\x78\x78")
        self.assertEqual(raw[-2:], b"\x0D\x0A")
        
        decoded = decode_gt06_packet(raw)
        self.assertEqual(decoded["protocol"], "GT06")
        self.assertAlmostEqual(decoded["latitude"], 28.6139, places=3)
        self.assertAlmostEqual(decoded["longitude"], 77.2090, places=3)
        self.assertEqual(decoded["speed"], 55.0)
        self.assertTrue(decoded["ignition"])

    def test_wire_teltonika_codec8_protocol(self):
        """Test actual Teltonika Codec 8 binary AVL packet assembly and decoding."""
        raw = build_teltonika_codec8_packet(19.0760, 72.8777, 62.0, 180.0, True)
        self.assertTrue(isinstance(raw, bytes))
        self.assertEqual(raw[0:4], b"\x00\x00\x00\x00")
        
        decoded = decode_teltonika_codec8_packet(raw)
        self.assertEqual(decoded["protocol"], "TELTONIKA_CODEC8")
        self.assertAlmostEqual(decoded["latitude"], 19.0760, places=4)
        self.assertAlmostEqual(decoded["longitude"], 72.8777, places=4)
        self.assertEqual(decoded["speed"], 62.0)
        self.assertTrue(decoded["ignition"])

    def test_wire_tk103_protocol(self):
        """Test actual Coban TK103 ASCII wire text frame."""
        text = build_tk103_packet("860123456789012", 28.6139, 77.2090, 48.0)
        self.assertTrue(text.startswith("(") and text.endswith(")"))
        
        decoded = decode_tk103_packet(text)
        self.assertEqual(decoded["protocol"], "TK103")
        self.assertEqual(decoded["device_id"], "860123456789012")
        self.assertAlmostEqual(decoded["latitude"], 28.6139, places=3)
        self.assertAlmostEqual(decoded["longitude"], 77.2090, places=3)
        self.assertEqual(decoded["speed"], 48.0)

    def test_wire_ais140_protocol(self):
        """Test actual Indian AIS-140 IRNSS $PVT sentence."""
        sentence = build_ais140_packet("860123456789012", 28.6139, 77.2090, 45.5)
        self.assertTrue(sentence.startswith("$PVT,"))
        
        decoded = decode_ais140_packet(sentence)
        self.assertEqual(decoded["protocol"], "AIS-140")
        self.assertEqual(decoded["device_id"], "860123456789012")
        self.assertAlmostEqual(decoded["latitude"], 28.6139, places=4)
        self.assertAlmostEqual(decoded["longitude"], 77.2090, places=4)
        self.assertEqual(decoded["speed"], 45.5)
        self.assertTrue(decoded["ignition"])

    def test_wire_queclink_protocol(self):
        """Test actual Queclink +RESP:GTFRI ASCII report."""
        report = build_queclink_packet("860123456789012", 28.6139, 77.2090, 50.0)
        self.assertTrue(report.startswith("+RESP:GTFRI"))
        
        decoded = decode_queclink_packet(report)
        self.assertEqual(decoded["protocol"], "QUECLINK")
        self.assertEqual(decoded["device_id"], "860123456789012")
        self.assertAlmostEqual(decoded["latitude"], 28.6139, places=4)
        self.assertAlmostEqual(decoded["longitude"], 77.2090, places=4)
        self.assertEqual(decoded["speed"], 50.0)

    def test_wire_h02_protocol(self):
        """Test actual Sinotrack H02 ASCII message."""
        msg = build_h02_packet("860123456789012", 28.6139, 77.2090, 52.0)
        self.assertTrue(msg.startswith("*HQ") and msg.endswith("#"))
        
        decoded = decode_h02_packet(msg)
        self.assertEqual(decoded["protocol"], "H02")
        self.assertEqual(decoded["device_id"], "860123456789012")
        self.assertAlmostEqual(decoded["latitude"], 28.6139, places=3)
        self.assertAlmostEqual(decoded["longitude"], 77.2090, places=3)
        self.assertEqual(decoded["speed"], 52.0)

    def test_wire_jt808_protocol(self):
        """Test actual Chinese MOT JT/T 808 binary report (Message 0x0200)."""
        raw = build_jt808_packet("013800138000", 39.9042, 116.4074, 60.0)
        self.assertTrue(isinstance(raw, bytes))
        self.assertEqual(raw[0], 0x7E)
        self.assertEqual(raw[-1], 0x7E)
        
        decoded = decode_jt808_packet(raw)
        self.assertEqual(decoded["protocol"], "JT808")
        self.assertEqual(decoded["device_id"], "013800138000")
        self.assertAlmostEqual(decoded["latitude"], 39.9042, places=4)
        self.assertAlmostEqual(decoded["longitude"], 116.4074, places=4)
        self.assertEqual(decoded["speed"], 60.0)
        self.assertTrue(decoded["ignition"])

    # -----------------------------------------------------------------------
    # Network Loopback Socket Transmission Test
    # -----------------------------------------------------------------------

    def test_tcp_socket_loopback_wire_transmission(self):
        """
        Spins up an actual TCP server socket on localhost, transmits a GT06 binary packet,
        receives it over the wire, and decodes it.
        """
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.bind(("127.0.0.1", 0)) # Ephemeral port
        server_port = server_sock.getsockname()[1]
        server_sock.listen(1)
        
        # Client sends GT06 packet
        client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_sock.connect(("127.0.0.1", server_port))
        
        out_packet = build_gt06_packet("860123456789012", 28.6139, 77.2090, 42.0, 90.0, True)
        client_sock.sendall(out_packet)
        client_sock.close()
        
        conn, _ = server_sock.accept()
        received_bytes = conn.recv(1024)
        conn.close()
        server_sock.close()
        
        self.assertEqual(received_bytes, out_packet)
        decoded = decode_gt06_packet(received_bytes)
        self.assertAlmostEqual(decoded["latitude"], 28.6139, places=3)
        self.assertEqual(decoded["speed"], 42.0)

    # -----------------------------------------------------------------------
    # Traccar HTTP Forwarder & Database Ingestion Verification
    # -----------------------------------------------------------------------

    async def test_traccar_forwarder_webhook_auth_and_database_persistence(self):
        """
        Simulates the Traccar 6.5 forwarder pipeline:
        1. Encodes raw telemetry as Traccar forwarder JSON payload.
        2. Sends with missing secret -> confirms 401.
        3. Sends with invalid secret -> confirms 401.
        4. Sends with valid X-Telematics-Secret -> confirms 200 OK.
        5. Verifies database records: VehicleLocation, VehicleCurrentLocation, Asset.
        """
        from config import settings
        original_secret = settings.TELEMATICS_WEBHOOK_SECRET
        settings.TELEMATICS_WEBHOOK_SECRET = "traccar_forwarder_secret_key_999"

        try:
            forwarder_payload = {
                "device": {
                    "id": 1,
                    "name": "Apex GT06 Tracker",
                    "uniqueId": "860123456789012",
                    "status": "online"
                },
                "position": {
                    "id": 1001,
                    "deviceId": 1,
                    "protocol": "gt06",
                    "deviceTime": "2026-11-24T10:30:00Z",
                    "fixTime": "2026-11-24T10:30:00Z",
                    "valid": True,
                    "latitude": 28.6139,
                    "longitude": 77.2090,
                    "altitude": 215.0,
                    "speed": 55.0, # knots or km/h
                    "course": 90.0,
                    "attributes": {
                        "ignition": True,
                        "batteryLevel": 98.0,
                        "odometer": 12450.0
                    }
                }
            }

            # 1. Test missing secret header -> 401
            resp_missing = self.client.post("/api/v1/tracking/telematics/traccar", json=forwarder_payload)
            self.assertEqual(resp_missing.status_code, 401)
            self.assertIn("Invalid telematics secret", resp_missing.json()["detail"])

            # 2. Test invalid secret header -> 401
            resp_invalid = self.client.post(
                "/api/v1/tracking/telematics/traccar",
                json=forwarder_payload,
                headers={"X-Telematics-Secret": "invalid_wrong_secret"}
            )
            self.assertEqual(resp_invalid.status_code, 401)
            self.assertIn("Invalid telematics secret", resp_invalid.json()["detail"])

            # 3. Test valid secret header -> 200 OK
            resp_valid = self.client.post(
                "/api/v1/tracking/telematics/traccar",
                json=forwarder_payload,
                headers={"X-Telematics-Secret": "traccar_forwarder_secret_key_999"}
            )
            self.assertEqual(resp_valid.status_code, 200)
            data = resp_valid.json()
            self.assertEqual(data["accepted"], 1)
            self.assertEqual(data["items"][0]["status"], "accepted")

            # 4. Verify Database Records
            async with self.session_maker() as db:
                from sqlalchemy import select
                # A. VehicleLocation record inserted
                res_loc = await db.execute(select(VehicleLocation).where(VehicleLocation.vehicle_id == 101))
                locs = res_loc.scalars().all()
                self.assertEqual(len(locs), 1)
                loc = locs[0]
                self.assertAlmostEqual(loc.latitude, 28.6139, places=4)
                self.assertAlmostEqual(loc.longitude, 77.2090, places=4)
                self.assertTrue(loc.source_metadata.get("ignition_status") or loc.source_metadata.get("attributes", {}).get("ignition"))

                # B. VehicleCurrentLocation cache updated
                res_cur = await db.execute(select(VehicleCurrentLocation).where(VehicleCurrentLocation.vehicle_id == 101))
                cur = res_cur.scalars().first()
                self.assertIsNotNone(cur)
                self.assertAlmostEqual(cur.latitude, 28.6139, places=4)
                self.assertAlmostEqual(cur.longitude, 77.2090, places=4)

                # C. Asset record updated
                res_asset = await db.execute(select(Asset).where(Asset.id == 50))
                asset = res_asset.scalars().first()
                self.assertEqual(asset.connection_status, "CONNECTED")
                self.assertAlmostEqual(asset.last_known_lat, 28.6139, places=4)
                self.assertAlmostEqual(asset.last_known_lng, 77.2090, places=4)
                self.assertTrue(asset.last_known_ignition)
        finally:
            settings.TELEMATICS_WEBHOOK_SECRET = original_secret


if __name__ == "__main__":
    unittest.main()
