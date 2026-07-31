"""
FleetGuard — Proof of Delivery Model
Captures delivery evidence: signatures, photos, invoices, and remarks.
"""

from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import Integer, String, Text, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

if TYPE_CHECKING:
    from models.trip_domain import Trip
    from models.driver_domain import Driver


class ProofOfDelivery(Base):
    """
    Proof of delivery record submitted by the driver upon trip completion.
    """
    __tablename__ = "proof_of_delivery"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    trip_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("trips.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )

    driver_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("drivers.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )

    company_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )

    signature_url: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True,
        comment="URL to customer signature image"
    )

    photos: Mapped[Optional[list]] = mapped_column(
        JSON, nullable=True, default=list,
        comment="List of delivery photo URLs"
    )

    invoice_url: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True,
        comment="URL to invoice/delivery receipt"
    )

    remarks: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="Delivery remarks or notes"
    )

    receiver_name: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # --- Relationships ---
    trip: Mapped["Trip"] = relationship("Trip", lazy="selectin")
    driver: Mapped["Driver"] = relationship("Driver", lazy="selectin")

    def __repr__(self) -> str:
        return f"<ProofOfDelivery(id={self.id}, trip_id={self.trip_id})>"
