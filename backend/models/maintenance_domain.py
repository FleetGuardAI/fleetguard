"""
FleetGuard — Maintenance Domain ORM Models
Represents maintenance records and tasks.
"""

from sqlalchemy import Integer, String, Enum, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, TYPE_CHECKING
import enum
from datetime import datetime

from database import Base

if TYPE_CHECKING:
    from models.vehicle_domain import Vehicle


class MaintenanceStatus(str, enum.Enum):
    CREATED = "CREATED"
    SCHEDULED = "SCHEDULED"
    STARTED = "STARTED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class MaintenanceCategory(str, enum.Enum):
    PREVENTIVE = "PREVENTIVE"
    CORRECTIVE = "CORRECTIVE"
    EMERGENCY = "EMERGENCY"
    INSPECTION = "INSPECTION"


class TaskStatus(str, enum.Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    SKIPPED = "SKIPPED"


class TaskType(str, enum.Enum):
    OIL_CHANGE = "OIL_CHANGE"
    TYRE_ROTATION = "TYRE_ROTATION"
    BRAKE_INSPECTION = "BRAKE_INSPECTION"
    ENGINE_DIAGNOSTIC = "ENGINE_DIAGNOSTIC"
    FILTER_REPLACEMENT = "FILTER_REPLACEMENT"
    GENERAL_INSPECTION = "GENERAL_INSPECTION"
    OTHER = "OTHER"


class MaintenanceRecord(Base):
    __tablename__ = "maintenance_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # --- Identity & Status ---
    business_id: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False,
        comment="Business identifier for the maintenance event"
    )
    status: Mapped[MaintenanceStatus] = mapped_column(
        Enum(MaintenanceStatus, native_enum=False, length=50),
        nullable=False, default=MaintenanceStatus.CREATED, index=True
    )
    category: Mapped[MaintenanceCategory] = mapped_column(
        Enum(MaintenanceCategory, native_enum=False, length=50),
        nullable=False, default=MaintenanceCategory.PREVENTIVE, index=True
    )

    # --- Vehicle Association ---
    vehicle_id: Mapped[Optional[int]] = mapped_column(ForeignKey("vehicles.id"), nullable=True, index=True)
    vehicle: Mapped[Optional["Vehicle"]] = relationship("Vehicle", lazy="selectin")

    # --- Location & Provider ---
    # Stored as string for now, conceptually designed for future foreign key relationships
    workshop: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    service_provider: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # --- Timing ---
    scheduled_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # --- Traceability ---
    origin_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    origin_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # --- Aggregate Child Entities ---
    tasks: Mapped[list["MaintenanceTask"]] = relationship(
        "MaintenanceTask", back_populates="maintenance_record",
        lazy="selectin", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<MaintenanceRecord(id={self.id}, business_id='{self.business_id}', status='{self.status.value}')>"


class MaintenanceTask(Base):
    __tablename__ = "maintenance_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    maintenance_record_id: Mapped[int] = mapped_column(
        ForeignKey("maintenance_records.id"), nullable=False, index=True
    )
    maintenance_record: Mapped["MaintenanceRecord"] = relationship(
        "MaintenanceRecord", back_populates="tasks"
    )

    task_type: Mapped[TaskType] = mapped_column(
        Enum(TaskType, native_enum=False, length=50),
        nullable=False, default=TaskType.OTHER
    )
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus, native_enum=False, length=50),
        nullable=False, default=TaskStatus.PENDING
    )
    
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    performed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # --- Traceability ---
    origin_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    origin_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    def __repr__(self) -> str:
        return f"<MaintenanceTask(id={self.id}, type='{self.task_type.value}', status='{self.status.value}')>"
