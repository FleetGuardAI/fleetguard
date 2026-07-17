"""
FleetGuard — Company ORM Model

Represents a transport company (tenant) on the SaaS platform.
Each company is an isolated tenant — all future data belongs to one company.
"""

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from database import Base

if TYPE_CHECKING:
    from models.user import User


class CompanyStatus(str, enum.Enum):
    """Lifecycle status of a company account."""

    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    PENDING = "PENDING"


class Company(Base):
    """
    Tenant model. One Company = one isolated fleet organisation.

    - Created during public company registration.
    - Has exactly one COMPANY_ADMIN user (the registering owner).
    - All fleet data (vehicles, drivers, trips) will reference company_id.
    """

    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    company_name: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True, comment="Legal or trading name of the company"
    )
    owner_name: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Full name of the primary company owner"
    )
    mobile_number: Mapped[str] = mapped_column(
        String(20), nullable=False, unique=True, index=True,
        comment="Primary contact mobile number; must be globally unique"
    )
    email: Mapped[str | None] = mapped_column(
        String(255), nullable=True, unique=True, index=True,
        comment="Optional company contact email; must be globally unique if provided"
    )
    status: Mapped[CompanyStatus] = mapped_column(
        Enum(CompanyStatus, name="company_status"),
        nullable=False,
        default=CompanyStatus.ACTIVE,
        server_default=CompanyStatus.ACTIVE.value,
        comment="Account lifecycle status"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # --- Relationships ---
    users: Mapped[list["User"]] = relationship(
        "User", back_populates="company", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Company(id={self.id}, name='{self.company_name}', status={self.status})>"
