"""
FleetGuard — User ORM Model

Represents a platform user belonging to a specific company (tenant).
Users are NOT self-registered — only the COMPANY_ADMIN is created during
company registration. All other users are created by the admin later.
"""

import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, TYPE_CHECKING

from database import Base

if TYPE_CHECKING:
    from models.company import Company


class UserRole(str, enum.Enum):
    """
    Role hierarchy within FleetGuard.

    - SUPER_ADMIN   : Platform-level admin (FleetGuard internal team only).
    - COMPANY_ADMIN : Primary admin of a single company; created at registration.
    - FLEET_MANAGER : Operational user; manages day-to-day fleet activities.
    - DRIVER        : Driver using the mobile app; limited access.
    """

    SUPER_ADMIN = "SUPER_ADMIN"
    COMPANY_ADMIN = "COMPANY_ADMIN"
    FLEET_MANAGER = "FLEET_MANAGER"
    ADMIN = "ADMIN"
    DRIVER = "DRIVER"


class User(Base):
    """
    Platform user model. Every user belongs to exactly one company.

    Login is via mobile_number OR email + password.
    Password is stored as a bcrypt hash — never in plain text.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    company_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="The company (tenant) this user belongs to"
    )

    full_name: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="User's full display name"
    )
    mobile_number: Mapped[str] = mapped_column(
        String(20), nullable=False, unique=True, index=True,
        comment="Mobile number used for login; globally unique across all tenants"
    )
    email: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, unique=True, index=True,
        comment="Optional email for login; globally unique if provided"
    )

    password_hash: Mapped[str] = mapped_column(
        String(255), nullable=False,
        comment="bcrypt hash of the user's password — NEVER expose in API responses"
    )

    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, native_enum=False, length=20),
        nullable=False,
        default=UserRole.COMPANY_ADMIN,
        comment="Access level / permission role"
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True,
        comment="Soft-disable a user without deleting them"
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
    company: Mapped["Company"] = relationship(
        "Company", back_populates="users", lazy="selectin"
    )

    def __repr__(self) -> str:
        return (
            f"<User(id={self.id}, mobile='{self.mobile_number}', "
            f"role={self.role}, active={self.is_active})>"
        )
