"""
FleetGuard — Asset Domain ORM Models
Represents independent hardware assets and their lifecycle history.
"""

from sqlalchemy import Integer, String, Enum, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON
from typing import Optional, Any, TYPE_CHECKING
import enum
from datetime import datetime

from database import Base

if TYPE_CHECKING:
    from models.vehicle_domain import Vehicle


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


class AssetHistoryCategory(str, enum.Enum):
    INSTALLED = "INSTALLED"
    REMOVED = "REMOVED"
    CALIBRATED = "CALIBRATED"
    REPAIRED = "REPAIRED"
    REPLACED = "REPLACED"
    RETIRED = "RETIRED"


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # --- Identity ---
    business_id: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False,
        comment="Authoritative business ID for the asset (e.g. internal tracking ID)"
    )
    asset_type: Mapped[AssetType] = mapped_column(
        Enum(AssetType, name="asset_type"),
        nullable=False, index=True
    )
    
    # --- Specifications ---
    manufacturer: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    model: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    serial_number: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    firmware_version: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    purchase_information: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    warranty_information: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # --- Current State ---
    current_vehicle_id: Mapped[Optional[int]] = mapped_column(ForeignKey("vehicles.id"), nullable=True, index=True)
    current_vehicle: Mapped[Optional["Vehicle"]] = relationship("Vehicle", lazy="selectin")
    
    installation_status: Mapped[AssetInstallationStatus] = mapped_column(
        Enum(AssetInstallationStatus, name="asset_installation_status"),
        nullable=False, default=AssetInstallationStatus.REGISTERED, index=True
    )
    operational_status: Mapped[AssetOperationalStatus] = mapped_column(
        Enum(AssetOperationalStatus, name="asset_operational_status"),
        nullable=False, default=AssetOperationalStatus.OK, index=True
    )

    # --- Traceability ---
    origin_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    origin_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # --- History ---
    history_records: Mapped[list["AssetHistory"]] = relationship(
        "AssetHistory", back_populates="asset",
        lazy="selectin", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Asset(id={self.id}, type='{self.asset_type.value}', status='{self.installation_status.value}')>"


class AssetHistory(Base):
    """
    Materialized history log of significant asset state changes.
    Appended by the AssetService when parsing Operational Events.
    """
    __tablename__ = "asset_history_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    asset_id: Mapped[int] = mapped_column(
        ForeignKey("assets.id"), nullable=False, index=True
    )
    asset: Mapped["Asset"] = relationship("Asset", back_populates="history_records")

    event_category: Mapped[AssetHistoryCategory] = mapped_column(
        Enum(AssetHistoryCategory, name="asset_history_category"),
        nullable=False
    )
    performed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    details: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON, nullable=True,
        comment="Event-specific metadata"
    )
    
    # --- Traceability ---
    origin_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    origin_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    def __repr__(self) -> str:
        return f"<AssetHistory(id={self.id}, event='{self.event_category.value}')>"
