"""
FleetGuard / Vahan — Asset & Hardware Domain ORM Models
Represents independent hardware assets, telematics devices, GPS provider integrations,
and their operational lifecycle history with multi-tenant company isolation.
"""

from sqlalchemy import Integer, String, Enum, DateTime, ForeignKey, Text, Float, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON
from typing import Optional, Any, TYPE_CHECKING
import enum
from datetime import datetime

from database import Base

if TYPE_CHECKING:
    from models.vehicle_domain import Vehicle
    from models.user import Company


class AssetType(str, enum.Enum):
    GPS_DEVICE = "GPS_DEVICE"
    FUEL_SENSOR = "FUEL_SENSOR"
    DASH_CAMERA = "DASH_CAMERA"
    RFID_READER = "RFID_READER"
    IOT_GATEWAY = "IOT_GATEWAY"
    TEMPERATURE_SENSOR = "TEMPERATURE_SENSOR"
    TPMS_GATEWAY = "TPMS_GATEWAY"
    OTHER = "OTHER"


class AssetInstallationStatus(str, enum.Enum):
    REGISTERED = "REGISTERED"
    INSTALLED = "INSTALLED"
    IN_STORAGE = "IN_STORAGE"
    IN_REPAIR = "IN_REPAIR"
    RETIRED = "RETIRED"


class AssetOperationalStatus(str, enum.Enum):
    OK = "OK"
    WARNING = "WARNING"
    ERROR = "ERROR"
    MAINTENANCE = "MAINTENANCE"


class ConnectionStatus(str, enum.Enum):
    CONNECTED = "CONNECTED"
    DISCONNECTED = "DISCONNECTED"
    PENDING = "PENDING"
    ERROR = "ERROR"
    MAINTENANCE = "MAINTENANCE"


class ConnectionType(str, enum.Enum):
    GPS_PROVIDER_API = "GPS_PROVIDER_API"
    DIRECT_HARDWARE = "DIRECT_HARDWARE"
    TCP_DEVICE = "TCP_DEVICE"
    MQTT_DEVICE = "MQTT_DEVICE"
    WEBHOOK = "WEBHOOK"
    OTHER = "OTHER"


class AssetHistoryCategory(str, enum.Enum):
    REGISTERED = "REGISTERED"
    INSTALLED = "INSTALLED"
    REMOVED = "REMOVED"
    CALIBRATED = "CALIBRATED"
    REPAIRED = "REPAIRED"
    REPLACED = "REPLACED"
    RETIRED = "RETIRED"


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # --- Tenant Isolation ---
    company_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False, index=True,
        comment="Company tenant ownership"
    )

    # --- Identity ---
    business_id: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False,
        comment="Authoritative business ID for the asset (e.g. AST-XXXX or HW-XXXX)"
    )
    asset_type: Mapped[AssetType] = mapped_column(
        Enum(AssetType, native_enum=False, length=50),
        nullable=False, default=AssetType.GPS_DEVICE, index=True
    )
    device_name: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True,
        comment="Human-friendly label (e.g. Tata Prima GPS Unit #1)"
    )
    imei: Mapped[Optional[str]] = mapped_column(
        String(100), index=True, nullable=True,
        comment="Hardware IMEI / unique electronic identifier"
    )
    serial_number: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, index=True,
        comment="Manufacturer serial number or fallback identifier"
    )
    
    # --- Specifications ---
    manufacturer: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    model: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    firmware_version: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # --- Universal GPS Telematics Attributes ---
    connection_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default=ConnectionType.DIRECT_HARDWARE.value,
        comment="GPS_PROVIDER_API, DIRECT_HARDWARE, TCP_DEVICE, MQTT_DEVICE, WEBHOOK, OTHER"
    )
    connection_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=ConnectionStatus.PENDING.value, index=True,
        comment="CONNECTED, DISCONNECTED, PENDING, ERROR, MAINTENANCE"
    )
    protocol: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True,
        comment="GPS protocol e.g. GT06, Teltonika Codec 8, TK103, H02, AIS140, MQTT, HTTP"
    )
    gps_provider: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True,
        comment="Integration provider (traccar, teltonika, queclink, generic, webhook)"
    )
    encrypted_credentials: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="Server-side Fernet-encrypted API key, device password, or webhook secret"
    )
    connection_config: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON, nullable=True,
        comment="Connection parameters e.g. host, port, topic, endpoint, account ID"
    )

    # --- Live State & Telemetry Cache ---
    last_communication_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    last_known_lat: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    last_known_lng: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    last_known_speed: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    last_known_heading: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    last_known_ignition: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    last_known_battery: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    last_known_address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    installation_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    offline_threshold_minutes: Mapped[int] = mapped_column(Integer, default=15, nullable=False)

    # --- Purchase & Warranty ---
    purchase_information: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    warranty_information: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # --- Vehicle Assignment ---
    current_vehicle_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("vehicles.id", ondelete="SET NULL"), nullable=True, index=True
    )
    current_vehicle: Mapped[Optional["Vehicle"]] = relationship("Vehicle", lazy="selectin")
    
    installation_status: Mapped[AssetInstallationStatus] = mapped_column(
        Enum(AssetInstallationStatus, native_enum=False, length=50),
        nullable=False, default=AssetInstallationStatus.REGISTERED, index=True
    )
    operational_status: Mapped[AssetOperationalStatus] = mapped_column(
        Enum(AssetOperationalStatus, native_enum=False, length=50),
        nullable=False, default=AssetOperationalStatus.OK, index=True
    )

    # --- Traceability ---
    origin_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    origin_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # --- History Records ---
    history_records: Mapped[list["AssetHistory"]] = relationship(
        "AssetHistory", back_populates="asset",
        lazy="selectin", cascade="all, delete-orphan",
        order_by="desc(AssetHistory.performed_at)"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<Asset(id={self.id}, name='{self.device_name}', imei='{self.imei}', status='{self.connection_status}')>"


class AssetHistory(Base):
    """
    Materialized history log of significant asset state changes.
    Tracks registration, installation, reassignment, removal, and maintenance.
    """
    __tablename__ = "asset_history_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    asset_id: Mapped[int] = mapped_column(
        ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    asset: Mapped["Asset"] = relationship("Asset", back_populates="history_records")

    event_category: Mapped[AssetHistoryCategory] = mapped_column(
        Enum(AssetHistoryCategory, native_enum=False, length=50),
        nullable=False
    )
    performed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    details: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON, nullable=True,
        comment="Event-specific metadata (e.g. previous vehicle, target vehicle, performed by user)"
    )
    
    # --- Traceability ---
    origin_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    origin_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    def __repr__(self) -> str:
        return f"<AssetHistory(id={self.id}, event='{self.event_category.value}', at={self.performed_at})>"


class GPSProviderAccount(Base):
    """
    Connected third-party GPS provider or telematics gateway account (Traccar, Teltonika Cloud, Queclink, etc.).
    Maintains provider connectivity credentials, synchronization state, and health.
    """
    __tablename__ = "gps_provider_accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    provider_type: Mapped[str] = mapped_column(
        String(50), nullable=False,
        comment="traccar, teltonika, queclink, generic_webhook, custom"
    )
    name: Mapped[str] = mapped_column(
        String(100), nullable=False,
        comment="Display name e.g. 'Main Traccar Server'"
    )
    server_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    account_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    encrypted_credentials: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sync_status: Mapped[str] = mapped_column(String(50), default="CONNECTED", nullable=False)
    last_sync_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    sync_error: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    device_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    config: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<GPSProviderAccount(id={self.id}, name='{self.name}', provider='{self.provider_type}', status='{self.sync_status}')>"
