"""
FleetGuard — Driver ORM Model
Represents a driver in the fleet, linked to WhatsApp for expense submissions.
"""

from sqlalchemy import Integer, String, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, TYPE_CHECKING

from database import Base

if TYPE_CHECKING:
    from models.ticket import Ticket
    from models.company import Company


class Driver(Base):
    __tablename__ = "drivers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="The company this driver belongs to"
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    phone_number: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False, index=True,
        comment="WhatsApp phone number in E.164 format (e.g. +919876543210)"
    )
    risk_score: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0,
        comment="Driver risk score 0-100. Higher = more suspicious."
    )
    rating: Mapped[float] = mapped_column(
        Float, nullable=False, default=5.0,
        comment="Driver performance rating 0-5 stars."
    )
    total_trips: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_expenses: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0,
        comment="Cumulative approved expenses in INR."
    )
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)

    # --- Relationships ---
    tickets: Mapped[list["Ticket"]] = relationship(
        "Ticket", back_populates="driver", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Driver(id={self.id}, name='{self.name}', risk={self.risk_score})>"
