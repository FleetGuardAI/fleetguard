"""
FleetGuard — Ticket (Expense) ORM Model
Represents an expense claim submitted by a driver via WhatsApp.
"""

import enum
from datetime import datetime

from sqlalchemy import (
    Integer, String, Float, DateTime, Enum, ForeignKey, Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from typing import Optional, TYPE_CHECKING

from database import Base

if TYPE_CHECKING:
    from models.vehicle_domain import Vehicle
    from models.driver_domain import Driver


class TicketStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class RiskLevel(str, enum.Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # --- Foreign Keys ---
    vehicle_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("vehicles.id"), nullable=True, index=True
    )
    driver_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("drivers.id"), nullable=False, index=True
    )

    # --- Expense Details ---
    issue_type: Mapped[str] = mapped_column(
        String(100), nullable=False,
        comment="Category: Tire Puncture, Fuel, Engine Repair, Food, Toll, etc."
    )
    vendor_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    amount: Mapped[float] = mapped_column(
        Float, nullable=False,
        comment="Claimed amount in INR"
    )
    fair_price: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True,
        comment="Regional average price for this issue_type"
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # --- Location ---
    location_lat: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    location_lng: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    location_name: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)

    # --- Receipt ---
    receipt_url: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True,
        comment="URL to the uploaded receipt image"
    )
    ocr_raw_response: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="Raw JSON response from OpenAI Vision OCR"
    )

    # --- Status & Risk ---
    status: Mapped[TicketStatus] = mapped_column(
        Enum(TicketStatus, native_enum=False, length=50), nullable=False, default=TicketStatus.PENDING, index=True
    )
    risk_level: Mapped[RiskLevel] = mapped_column(
        Enum(RiskLevel, native_enum=False, length=50), nullable=False, default=RiskLevel.LOW
    )
    risk_reasons: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="JSON array of reasons for the risk flag"
    )
    is_duplicate: Mapped[bool] = mapped_column(default=False)

    # --- Timestamps ---
    expense_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="Date extracted from receipt or reported by driver"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # --- Payout ---
    payout_reference: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True,
        comment="UPI transaction ID after approval payout"
    )

    # --- Relationships ---
    vehicle: Mapped[Optional["Vehicle"]] = relationship("Vehicle", back_populates="tickets")
    driver: Mapped["Driver"] = relationship("Driver", back_populates="tickets")

    def __repr__(self) -> str:
        return (
            f"<Ticket(id={self.id}, type='{self.issue_type}', "
            f"amount=₹{self.amount}, status={self.status.value})>"
        )
