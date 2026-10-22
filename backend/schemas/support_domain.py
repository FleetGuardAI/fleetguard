from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from models.support_domain import TicketCategory, TicketPriority, TicketStatus, RequesterType, MessageType

class SupportTicketCreate(BaseModel):
    title: str
    description: str
    category: TicketCategory
    priority: Optional[TicketPriority] = TicketPriority.MEDIUM
    
    # When created by Fleet Owner / Driver, these will be populated from auth context
    requester_type: Optional[RequesterType] = None
    requester_id: Optional[int] = None
    requester_name: Optional[str] = None
    requester_phone: Optional[str] = None
    requester_email: Optional[str] = None
    company_id: Optional[int] = None

    # Context IDs
    driver_id: Optional[int] = None
    vehicle_id: Optional[int] = None
    trip_id: Optional[int] = None

class SupportTicketUpdate(BaseModel):
    priority: Optional[TicketPriority] = None
    status: Optional[TicketStatus] = None
    assigned_agent_id: Optional[int] = None

class SupportTicketStatusUpdate(BaseModel):
    status: TicketStatus
    internal_note: Optional[str] = None

class SupportTicketAssign(BaseModel):
    assigned_agent_id: Optional[int] = None

class SupportTicketResponse(BaseModel):
    id: int
    ticket_id: str
    title: str
    description: str
    category: TicketCategory
    priority: TicketPriority
    status: TicketStatus
    requester_type: RequesterType
    requester_id: Optional[int] = None
    requester_name: Optional[str] = None
    requester_phone: Optional[str] = None
    requester_email: Optional[str] = None
    company_id: Optional[int] = None
    driver_id: Optional[int] = None
    vehicle_id: Optional[int] = None
    trip_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    assigned_agent_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)

class SupportTicketMessageCreate(BaseModel):
    content: str
    message_type: Optional[MessageType] = MessageType.PUBLIC

class SupportTicketMessageResponse(BaseModel):
    id: int
    ticket_id: int
    message_type: MessageType
    content: str
    sender_type: RequesterType
    sender_id: Optional[int] = None
    sender_name: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
