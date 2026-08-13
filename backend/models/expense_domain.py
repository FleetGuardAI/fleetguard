"""
FleetGuard — Expense Domain ORM Models
Represents the financial records projection of fleet operations.
"""

import enum
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import (
    Integer, String, Float, DateTime, Enum, Text
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from database import Base


class ExpenseCategory(str, enum.Enum):
    FUEL = "FUEL"
    MAINTENANCE = "MAINTENANCE"
    TYRE = "TYRE"
    TOLL = "TOLL"
    PARKING = "PARKING"
    SALARY = "SALARY"
    ALLOWANCE = "ALLOWANCE"
    PENALTY = "PENALTY"
    LOADING = "LOADING"
    UNLOADING = "UNLOADING"
    DRIVER_ADVANCE = "DRIVER_ADVANCE"
    DETENTION = "DETENTION"
    MISCELLANEOUS = "MISCELLANEOUS"


class ExpenseStatus(str, enum.Enum):
    RECORDED = "RECORDED"
    CANCELLED = "CANCELLED"


class Expense(Base):
    """
    Aggregate Root for the Expense Domain.
    A single financial record generated from a fleet operation.
    """
    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Financial fields
    category: Mapped[ExpenseCategory] = mapped_column(Enum(ExpenseCategory), nullable=False, index=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    status: Mapped[ExpenseStatus] = mapped_column(Enum(ExpenseStatus), nullable=False, default=ExpenseStatus.RECORDED, index=True)
    
    expense_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Optional Supporting Document Reference
    receipt_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Linked Business Entities (References only - no deep relationships for decoupling)
    business_id: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    vehicle_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    driver_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    trip_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    maintenance_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    
    # Traceability
    origin_type: Mapped[str] = mapped_column(String(100), nullable=False, default="verified_event")
    origin_id: Mapped[str] = mapped_column(String(255), nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<Expense(id={self.id}, category='{self.category.value}', amount={self.amount}, status='{self.status.value}')>"
