"""
FleetGuard — Tyre Domain ORM Models
Represents individual tyre assets and their lifecycle history.
"""

from sqlalchemy import Integer, String, Float, Enum, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON
from typing import Optional, Any, TYPE_CHECKING
import enum
from datetime import datetime

from database import Base

if TYPE_CHECKING:
    from models.vehicle_domain import Vehicle


class TyreStatus(str, enum.Enum):
    REGISTERED = "REGISTERED"
    INSTALLED = "INSTALLED"
    IN_STORAGE = "IN_STORAGE"
    IN_REPAIR = "IN_REPAIR"
    RETREADING = "RETREADING"
    RETIRED = "RETIRED"


class LifecycleEventCategory(str, enum.Enum):
    INSTALLED = "INSTALLED"
    REMOVED = "REMOVED"
    ROTATED = "ROTATED"
    REPAIRED = "REPAIRED"
    RETREADED = "RETREADED"
    RETIRED = "RETIRED"


class Tyre(Base):
    __tablename__ = "tyres"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # --- Multi-tenancy ---
    company_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False, default=1, index=True,
        comment="Tenant isolation boundary"
    )

    # --- Identity ---
    serial_number: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False,
        comment="Authoritative business ID (physical serial number) for the tyre"
    )
    
    # --- Specifications ---
    manufacturer: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    brand: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    model: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    size: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # --- Purchase & Acquisition Provenance ---
    purchase_cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="Known acquisition cost")
    purchase_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, comment="Procurement acquisition date")
    purchase_currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR", server_default="INR", comment="ISO 4217 currency code")
    purchase_invoice: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="Source invoice or receipt reference")
    purchase_vendor: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="Supplier or vendor name")
    purchase_information: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True, comment="Legacy / auxiliary purchase metadata")

    # --- Current State ---
    current_vehicle_id: Mapped[Optional[int]] = mapped_column(ForeignKey("vehicles.id"), nullable=True, index=True)
    current_vehicle: Mapped[Optional["Vehicle"]] = relationship("Vehicle", lazy="selectin")
    current_position: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    current_status: Mapped[TyreStatus] = mapped_column(
        Enum(TyreStatus, native_enum=False, length=50),
        nullable=False, default=TyreStatus.REGISTERED, index=True
    )

    # --- Lifecycle Metrics ---
    retread_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_lifetime_km: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    current_retread_km: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    current_installation_odometer: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    current_tread_depth_mm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # --- Traceability ---
    origin_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    origin_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # --- History ---
    lifecycle_records: Mapped[list["TyreLifecycleRecord"]] = relationship(
        "TyreLifecycleRecord", back_populates="tyre",
        lazy="selectin", cascade="all, delete-orphan",
        order_by="TyreLifecycleRecord.id.asc()"
    )

    def __repr__(self) -> str:
        return f"<Tyre(id={self.id}, serial='{self.serial_number}', status='{self.current_status.value}', company_id={self.company_id})>"


class TyreLifecycleRecord(Base):
    """
    Materialized history log of significant tyre state changes.
    Appended by the TyreService when parsing Operational Events or executing transitions.
    """
    __tablename__ = "tyre_lifecycle_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    company_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=True, index=True
    )

    tyre_id: Mapped[int] = mapped_column(
        ForeignKey("tyres.id"), nullable=False, index=True
    )
    tyre: Mapped["Tyre"] = relationship("Tyre", back_populates="lifecycle_records")

    event_category: Mapped[LifecycleEventCategory] = mapped_column(
        Enum(LifecycleEventCategory, native_enum=False, length=50),
        nullable=False
    )
    performed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    details: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON, nullable=True,
        comment="Event-specific metadata (e.g. tread_depth, repair_cost, workshop_name)"
    )
    
    # --- Traceability ---
    origin_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    origin_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    def __repr__(self) -> str:
        return f"<TyreLifecycleRecord(id={self.id}, event='{self.event_category.value}', tyre_id={self.tyre_id})>"

