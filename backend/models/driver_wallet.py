"""
FleetGuard — Driver Wallet Model
Tracks driver payments: salary, advances, incentives, deductions.
"""

import enum
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import Integer, Float, String, Enum, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

if TYPE_CHECKING:
    from models.driver_domain import Driver


class TransactionType(str, enum.Enum):
    SALARY = "SALARY"
    ADVANCE = "ADVANCE"
    INCENTIVE = "INCENTIVE"
    DEDUCTION = "DEDUCTION"
    REPAYMENT = "REPAYMENT"


class TransactionStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    COMPLETED = "COMPLETED"


class WalletTransaction(Base):
    """
    Individual financial transaction in a driver's wallet.
    """
    __tablename__ = "wallet_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    driver_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("drivers.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )

    company_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )

    transaction_type: Mapped[TransactionType] = mapped_column(
        Enum(TransactionType, native_enum=False, length=50),
        nullable=False, index=True,
    )

    amount: Mapped[float] = mapped_column(Float, nullable=False)

    status: Mapped[TransactionStatus] = mapped_column(
        Enum(TransactionStatus, native_enum=False, length=50),
        nullable=False, default=TransactionStatus.PENDING,
    )

    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reference_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    processed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # --- Relationships ---
    driver: Mapped["Driver"] = relationship("Driver", lazy="selectin")

    def __repr__(self) -> str:
        return f"<WalletTransaction(id={self.id}, type={self.transaction_type.value}, amount={self.amount})>"
