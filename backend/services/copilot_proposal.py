"""
FleetGuard — Copilot Trip Proposal Manager
Handles server-side staging, security binding, expiration, idempotency,
and confirmation for trip scheduling actions executed via AI Co-Pilot.
"""

import uuid
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

logger = logging.getLogger("fleetguard.copilot.proposal")

PROPOSAL_TTL_MINUTES = 15


class TripProposal(BaseModel):
    proposal_id: str = Field(..., description="Unique proposal identifier")
    company_id: int = Field(..., description="Owner company ID enforcing tenant isolation")
    user_id: str = Field(..., description="Authenticated user who requested the proposal")
    vehicle_id: int = Field(..., description="Resolved vehicle database ID")
    vehicle_registration: str = Field(..., description="Resolved vehicle registration number")
    driver_id: Optional[int] = Field(None, description="Resolved driver database ID if assigned")
    driver_name: Optional[str] = Field(None, description="Driver full name")
    origin_location: str = Field(..., description="Departure city or location")
    destination_location: str = Field(..., description="Arrival city or destination")
    planned_start_time: str = Field(..., description="ISO 8601 planned departure date and time")
    planned_end_time: Optional[str] = Field(None, description="Optional estimated arrival")
    planned_distance_km: Optional[float] = Field(None, description="Estimated distance in km")
    revenue: Optional[float] = Field(None, description="Agreed freight revenue if specified")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc) + timedelta(minutes=PROPOSAL_TTL_MINUTES)
    )
    status: str = Field(
        default="PENDING_CONFIRMATION",
        description="PENDING_CONFIRMATION, EXECUTING, EXECUTED, CANCELLED, or EXPIRED"
    )
    created_trip_id: Optional[int] = Field(None, description="Database ID of created trip")
    created_trip_business_id: Optional[str] = Field(None, description="Business ID of created trip (e.g. TRP-XXX)")

    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.expires_at


class TripProposalManager:
    """
    Server-side in-memory registry of trip proposals with per-proposal serialization locks.
    Guarantees authorization boundaries, single-use idempotency, and TTL enforcement.

    DEPLOYMENT ARCHITECTURE & CONCURRENCY CONSTRAINTS:
    - Supported Deployment Mode: SINGLE_PROCESS (e.g. uvicorn main:app --host 0.0.0.0 --port $PORT).
    - Concurrency Guarantee: Thread/task-safe atomic confirmation within a single process via asyncio.Lock.
    - Limitation: Proposals do NOT persist across process restarts or horizontally distributed workers.
      For multi-worker clusters (uvicorn --workers > 1 or multi-pod Kubernetes/ECS), proposals must be
      persisted in shared distributed storage (Redis or Postgres trip_proposals table).
    """
    DEPLOYMENT_MODE: str = "SINGLE_PROCESS"
    MAX_WORKERS_SUPPORTED: int = 1

    _instance: Optional["TripProposalManager"] = None
    _proposals: Dict[str, TripProposal] = {}
    _locks: Dict[str, asyncio.Lock] = {}

    @classmethod
    def get_instance(cls) -> "TripProposalManager":
        if cls._instance is None:
            cls._instance = TripProposalManager()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Helper for test isolation."""
        cls._proposals.clear()
        cls._locks.clear()

    def get_lock(self, proposal_id: str) -> asyncio.Lock:
        """Returns or initializes a per-proposal serialization lock for atomic confirmation."""
        if proposal_id not in self._locks:
            self._locks[proposal_id] = asyncio.Lock()
        return self._locks[proposal_id]

    def create_proposal(
        self,
        company_id: int,
        user_id: str,
        vehicle_id: int,
        vehicle_registration: str,
        origin_location: str,
        destination_location: str,
        planned_start_time: str,
        driver_id: Optional[int] = None,
        driver_name: Optional[str] = None,
        planned_distance_km: Optional[float] = None,
        revenue: Optional[float] = None,
    ) -> TripProposal:
        proposal_id = f"PROP-{uuid.uuid4().hex[:10].upper()}"
        proposal = TripProposal(
            proposal_id=proposal_id,
            company_id=company_id,
            user_id=str(user_id),
            vehicle_id=vehicle_id,
            vehicle_registration=vehicle_registration,
            driver_id=driver_id,
            driver_name=driver_name,
            origin_location=origin_location,
            destination_location=destination_location,
            planned_start_time=planned_start_time,
            planned_distance_km=planned_distance_km,
            revenue=revenue,
            status="PENDING_CONFIRMATION"
        )
        self._proposals[proposal_id] = proposal
        logger.info(
            f"AUDIT: Prepared trip proposal {proposal_id} for company={company_id}, "
            f"vehicle={vehicle_registration}, route={origin_location}->{destination_location}"
        )
        return proposal

    def get_proposal(self, proposal_id: str, company_id: int) -> TripProposal:
        proposal = self._proposals.get(proposal_id)
        if not proposal:
            raise ValueError(f"Proposal '{proposal_id}' not found or invalid.")

        # Strict Multi-Tenancy Boundary Check
        if proposal.company_id != company_id:
            logger.warning(
                f"SECURITY: Attempted unauthorized access to proposal {proposal_id} "
                f"by company {company_id} (owner: {proposal.company_id})"
            )
            raise PermissionError("Unauthorized access to trip proposal outside your fleet.")

        # Check Expiration
        if proposal.is_expired():
            proposal.status = "EXPIRED"
            raise ValueError(f"Proposal '{proposal_id}' has expired. Please stage a new trip proposal.")

        return proposal

    def mark_executed(
        self,
        proposal_id: str,
        trip_id: int,
        trip_business_id: str
    ) -> TripProposal:
        proposal = self._proposals.get(proposal_id)
        if not proposal:
            raise ValueError(f"Proposal '{proposal_id}' not found.")

        proposal.status = "EXECUTED"
        proposal.created_trip_id = trip_id
        proposal.created_trip_business_id = trip_business_id
        logger.info(
            f"AUDIT: Confirmed and executed trip proposal {proposal_id} -> "
            f"Trip ID={trip_id} ({trip_business_id})"
        )
        return proposal

    def rollback_executing(self, proposal_id: str) -> Optional[TripProposal]:
        """Rolls back an in-flight EXECUTING status to PENDING_CONFIRMATION upon transaction failure."""
        proposal = self._proposals.get(proposal_id)
        if proposal and proposal.status == "EXECUTING":
            proposal.status = "PENDING_CONFIRMATION"
            logger.warning(
                f"ROLLBACK: Reverted proposal {proposal_id} status from EXECUTING to PENDING_CONFIRMATION"
            )
            return proposal
        return proposal

    def cancel_proposal(self, proposal_id: str, company_id: int) -> TripProposal:
        proposal = self.get_proposal(proposal_id, company_id)
        if proposal.status == "EXECUTED":
            raise ValueError(f"Proposal '{proposal_id}' has already been executed and cannot be cancelled.")

        proposal.status = "CANCELLED"
        logger.info(f"AUDIT: Cancelled trip proposal {proposal_id} for company={company_id}")
        return proposal
