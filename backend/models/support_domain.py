import enum
from datetime import datetime
from typing import Optional, List

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, func, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

class TicketCategory(str, enum.Enum):
    ACCOUNT = "ACCOUNT"
    PASSWORD_RESET = "PASSWORD_RESET"
    DRIVER = "DRIVER"
    FLEET_OWNER = "FLEET_OWNER"
    VEHICLE = "VEHICLE"
    TRIP = "TRIP"
    EXPENSE = "EXPENSE"
    PAYMENT = "PAYMENT"
    DOCUMENT = "DOCUMENT"
    TECHNICAL = "TECHNICAL"
    APP_BUG = "APP_BUG"
    FEATURE_REQUEST = "FEATURE_REQUEST"
    COMPLAINT = "COMPLAINT"
    SECURITY = "SECURITY"
    OTHER = "OTHER"

class TicketPriority(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"

class TicketStatus(str, enum.Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    WAITING_FOR_USER = "WAITING_FOR_USER"
    WAITING_INTERNAL = "WAITING_INTERNAL"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    REOPENED = "REOPENED"

class RequesterType(str, enum.Enum):
    FLEET_OWNER = "FLEET_OWNER"
    DRIVER = "DRIVER"
    INTERNAL_USER = "INTERNAL_USER"

class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticket_id: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True) # e.g. VH-000123
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    category: Mapped[TicketCategory] = mapped_column(Enum(TicketCategory, native_enum=False, length=50), nullable=False)
    priority: Mapped[TicketPriority] = mapped_column(Enum(TicketPriority, native_enum=False, length=20), nullable=False, default=TicketPriority.MEDIUM)
    status: Mapped[TicketStatus] = mapped_column(Enum(TicketStatus, native_enum=False, length=50), nullable=False, default=TicketStatus.OPEN)
    
    requester_type: Mapped[RequesterType] = mapped_column(Enum(RequesterType, native_enum=False, length=50), nullable=False)
    requester_id: Mapped[int] = mapped_column(Integer, nullable=False) # e.g. User ID or Driver ID
    requester_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    requester_phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    requester_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    company_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("companies.id", ondelete="SET NULL"), nullable=True)
    driver_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("drivers.id", ondelete="SET NULL"), nullable=True)
    vehicle_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("vehicles.id", ondelete="SET NULL"), nullable=True)
    trip_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("trips.id", ondelete="SET NULL"), nullable=True)
    
    assigned_agent_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("admin_users.id", ondelete="SET NULL"), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

class MessageType(str, enum.Enum):
    PUBLIC = "PUBLIC"
    INTERNAL_NOTE = "INTERNAL_NOTE"
    SYSTEM_EVENT = "SYSTEM_EVENT"

class SupportTicketMessage(Base):
    __tablename__ = "support_ticket_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticket_id: Mapped[int] = mapped_column(Integer, ForeignKey("support_tickets.id", ondelete="CASCADE"), nullable=False)
    
    message_type: Mapped[MessageType] = mapped_column(Enum(MessageType, native_enum=False, length=50), nullable=False, default=MessageType.PUBLIC)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    sender_type: Mapped[RequesterType] = mapped_column(Enum(RequesterType, native_enum=False, length=50), nullable=False)
    sender_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    sender_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class SupportTicketAttachment(Base):
    __tablename__ = "support_ticket_attachments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticket_id: Mapped[int] = mapped_column(Integer, ForeignKey("support_tickets.id", ondelete="CASCADE"), nullable=False)
    message_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("support_ticket_messages.id", ondelete="CASCADE"), nullable=True)
    
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_url: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    uploaded_by_type: Mapped[RequesterType] = mapped_column(Enum(RequesterType, native_enum=False, length=50), nullable=False)
    uploaded_by_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class PasswordResetRequestAdmin(Base):
    __tablename__ = "admin_password_reset_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    requester_type: Mapped[RequesterType] = mapped_column(Enum(RequesterType, native_enum=False, length=50), nullable=False)
    requester_email_phone: Mapped[str] = mapped_column(String(255), nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="PENDING") # PENDING, APPROVED, REJECTED
    ticket_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("support_tickets.id", ondelete="SET NULL"), nullable=True)
    
    resolved_by_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("admin_users.id", ondelete="SET NULL"), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
