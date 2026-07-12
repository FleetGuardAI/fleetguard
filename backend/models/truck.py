"""
FleetGuard — Truck ORM Model
Represents a truck/vehicle in the fleet.
"""

from sqlalchemy import Integer, String, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, TYPE_CHECKING

from database import Base

if TYPE_CHECKING:
    from models.ticket import Ticket
    from models.fuel_log import FuelLog


class Truck(Base):
    __tablename__ = "trucks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    license_plate: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False, index=True
    )
    make: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tank_capacity: Mapped[float] = mapped_column(
        Float, nullable=False, default=400.0,
        comment="Fuel tank capacity in liters"
    )
    is_active: Mapped[bool] = mapped_column(default=True)

    # --- Relationships ---
    tickets: Mapped[list["Ticket"]] = relationship(
        "Ticket", back_populates="truck", lazy="selectin"
    )
    fuel_logs: Mapped[list["FuelLog"]] = relationship(
        "FuelLog", back_populates="truck", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Truck(id={self.id}, plate='{self.license_plate}', make='{self.make}')>"
