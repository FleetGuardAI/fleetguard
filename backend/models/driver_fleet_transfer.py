"""
FleetGuard — Driver Fleet Transfer Model
Represents a driver's request to transfer/switch from one fleet company to another.
Preserves historical records and isolates multi-tenant operational data.
"""

from datetime import datetime
from typing import Optional, TYPE_CHECKING
import enum

from sqlalchemy import Integer, String, DateTime, ForeignKey, Text, Enum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

if TYPE_CHECKING:
    from models.company import Company
    from models.driver_domain import Driver
    from models.user import User


class TransferStatus(str, enum.Enum):
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class DriverFleetTransfer(Base):
    """
    Fleet transfer record for a driver switching from one company to another.
    A transfer remains in PENDING_APPROVAL until reviewed and approved by the target company's admin.
    """
    __tablename__ = "driver_fleet_transfers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    driver_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("drivers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="The driver requesting the transfer"
    )

    from_company_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Source fleet company ID"
    )

    to_company_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Target fleet company ID"
    )

    invite_token: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="The QR invite token used to initiate the transfer"
    )

    status: Mapped[TransferStatus] = mapped_column(
        Enum(TransferStatus, native_enum=False, length=50),
        nullable=False,
        default=TransferStatus.PENDING_APPROVAL,
        index=True,
        comment="Status of the transfer request"
    )

    rejection_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Explanation if the transfer was rejected"
    )

    reviewed_by: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="Admin user who approved or rejected the transfer"
    )

    reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp of approval or rejection"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )

    # --- Relationships ---
    driver: Mapped["Driver"] = relationship("Driver", foreign_keys=[driver_id], lazy="selectin")
    from_company: Mapped["Company"] = relationship("Company", foreign_keys=[from_company_id], lazy="selectin")
    to_company: Mapped["Company"] = relationship("Company", foreign_keys=[to_company_id], lazy="selectin")
    reviewer: Mapped[Optional["User"]] = relationship("User", foreign_keys=[reviewed_by], lazy="selectin")

    def __repr__(self) -> str:
        return (
            f"<DriverFleetTransfer(id={self.id}, driver_id={self.driver_id}, "
            f"from={self.from_company_id}, to={self.to_company_id}, status='{self.status.value}')>"
        )
