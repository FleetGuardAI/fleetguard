from datetime import datetime, timezone
from sqlalchemy import Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

class TripStartSelfie(Base):
    __tablename__ = "trip_start_selfies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    trip_id: Mapped[int] = mapped_column(Integer, ForeignKey("trips.id", ondelete="CASCADE"), index=True, nullable=False)
    driver_id: Mapped[int] = mapped_column(Integer, ForeignKey("drivers.id", ondelete="CASCADE"), index=True, nullable=False)
    vehicle_id: Mapped[int] = mapped_column(Integer, ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), index=True, nullable=False)
    
    registration_number: Mapped[str] = mapped_column(String(20), nullable=False)
    selfie_url: Mapped[str] = mapped_column(String(500), nullable=False)
    verification_status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False)
    
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    trip = relationship("Trip", back_populates="start_selfies")
