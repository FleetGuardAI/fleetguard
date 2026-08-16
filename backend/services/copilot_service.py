"""
FleetGuard — Copilot Service
"""

import uuid
import json
import logging
from typing import Dict, Any, List

from infrastructure.uow import AbstractUnitOfWork
from infrastructure.llm.provider import LLMMessage
from infrastructure.llm.openai_provider import OpenAIProvider
from services.fleet_intelligence_service import FleetIntelligenceService
from services.trip_intelligence_service import TripIntelligenceService
from schemas.copilot import CopilotChatRequest, CopilotChatResponse
from models.operational_event import EntityType

logger = logging.getLogger("fleetguard.services.copilot")


# In-memory conversation store for V1 (controlled history mechanism)
# Format: conversation_id -> List[LLMMessage]
_conversation_history: Dict[str, List[LLMMessage]] = {}
MAX_HISTORY_MESSAGES = 20
MAX_TOOL_ITERATIONS = 5

SYSTEM_PROMPT = """You are FleetGuard's operational intelligence assistant.

Responsibilities:
- Answer fleet questions.
- Investigate vehicles and trips using available tools.
- Explain Fleet Intelligence findings.
- Explain Trip Intelligence results.
- Provide grounded recommendations based strictly on data.

Rules:
- Never fabricate or invent FleetGuard data.
- Use tools to fetch factual FleetGuard information.
- Do not calculate metrics that FleetGuard tools already provide (e.g., profitability, cost). Rely on the tool results.
- Distinguish facts (data returned by tools) from interpretations (what the data suggests).
- Use "most probable cause" or "the data suggests" when providing interpretations. Do not pretend certainty unless it is a definitive fact.
- Admit when information or data is unavailable.
- Respect fleet/company boundaries.
- Never claim an action was taken, you do not have action capabilities.
- Do not expose internal reasoning or chain-of-thought to users. Format your responses in clean, readable Markdown without explaining which tool you just used. Do not output raw JSON tool results to the user.
"""

TOOLS_DEFINITION = [
    {
        "type": "function",
        "function": {
            "name": "get_fleet_health",
            "description": "Retrieves the overall health, domain risks, findings, and signals for the authenticated user's fleet.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_trip_intelligence",
            "description": "Retrieves comprehensive deterministic trip intelligence for a given trip ID, including profitability, anomalies, efficiency scores, and cost breakdowns.",
            "parameters": {
                "type": "object",
                "properties": {
                    "trip_id": {
                        "type": "integer",
                        "description": "The unique ID of the trip to investigate."
                    }
                },
                "required": ["trip_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_vehicle_summary",
            "description": "Retrieves a controlled summary of a specific vehicle, including its recent trips and status.",
            "parameters": {
                "type": "object",
                "properties": {
                    "vehicle_id": {
                        "type": "integer",
                        "description": "The unique ID of the vehicle."
                    }
                },
                "required": ["vehicle_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_related_evidence",
            "description": "Retrieves evidence records associated with a specific entity (like a vehicle or trip) to support investigations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "entity_type": {
                        "type": "string",
                        "enum": ["TRIP", "VEHICLE", "DRIVER", "EXPENSE", "FUEL"],
                        "description": "The domain category of the entity."
                    },
                    "entity_id": {
                        "type": "string",
                        "description": "The identifier of the specific entity instance."
                    }
                },
                "required": ["entity_type", "entity_id"]
            }
        }
    }
]


class CopilotService:
    def __init__(self, uow: AbstractUnitOfWork, company_id: str):
        self.uow = uow
        self.company_id = company_id
        self.llm = OpenAIProvider()

    async def chat(self, request: CopilotChatRequest) -> CopilotChatResponse:
        conv_id = request.conversation_id or str(uuid.uuid4())
        
        # Load or initialize history
        messages = _conversation_history.get(conv_id, [])
        if not messages:
            messages.append(LLMMessage(role="system", content=SYSTEM_PROMPT))

        # Append Context if provided and it's a new turn
        user_message_content = request.message
        if request.context:
            context_str = f"[Context: Viewing {request.context.type} {request.context.id or ''}]\n"
            user_message_content = context_str + user_message_content

        messages.append(LLMMessage(role="user", content=user_message_content))

        # Tool calling loop
        iterations = 0
        tools_used = []

        while iterations < MAX_TOOL_ITERATIONS:
            iterations += 1
            response = await self.llm.chat(messages, tools=TOOLS_DEFINITION)
            
            ai_msg = response.message
            messages.append(ai_msg)

            if not ai_msg.tool_calls:
                # No more tools, this is the final answer
                break

            # Execute tools
            for tool_call in ai_msg.tool_calls:
                func_name = tool_call["function"]["name"]
                try:
                    args = json.loads(tool_call["function"]["arguments"])
                except json.JSONDecodeError:
                    args = {}

                tools_used.append(func_name)
                
                try:
                    tool_result_str = await self._execute_tool(func_name, args)
                except Exception as e:
                    logger.error(f"Error executing tool {func_name}: {e}")
                    tool_result_str = f"Error executing tool: {e}"

                # Append tool result
                messages.append(LLMMessage(
                    role="tool",
                    content=tool_result_str,
                    tool_call_id=tool_call["id"],
                    name=func_name
                ))

        # Save history (bounded)
        _conversation_history[conv_id] = messages[-MAX_HISTORY_MESSAGES:]

        return CopilotChatResponse(
            message=messages[-1].content,
            conversation_id=conv_id,
            metadata={"tools_used": tools_used}
        )

    async def _execute_tool(self, name: str, args: Dict[str, Any]) -> str:
        if name == "get_fleet_health":
            svc = FleetIntelligenceService(self.uow)
            report = await svc.get_fleet_health(self.company_id)
            return report.model_dump_json()

        elif name == "get_trip_intelligence":
            trip_id = args.get("trip_id")
            if not trip_id:
                return "Error: trip_id is required."
            try:
                trip_id = int(trip_id)
            except ValueError:
                return "Error: trip_id must be an integer."

            trip = await self.uow.repositories.trip.get_trip_by_id(trip_id)
            if not trip:
                return f"Error: Trip {trip_id} not found in this fleet."
            # Enforce scoping if trip has company_id. Assuming trip belongs to company.
            if hasattr(trip, "company_id") and str(trip.company_id) != str(self.company_id):
                return "Error: Unauthorized access to trip outside your fleet."

            svc = TripIntelligenceService(self.uow)
            intel = await svc.compute_intelligence(trip)
            return intel.model_dump_json()

        elif name == "get_vehicle_summary":
            vehicle_id = args.get("vehicle_id")
            if not vehicle_id:
                return "Error: vehicle_id is required."
            try:
                vehicle_id = int(vehicle_id)
            except ValueError:
                return "Error: vehicle_id must be an integer."

            vehicle = await self.uow.repositories.vehicle.get_vehicle_by_id(vehicle_id)
            if not vehicle:
                return f"Error: Vehicle {vehicle_id} not found."
            if hasattr(vehicle, "company_id") and str(vehicle.company_id) != str(self.company_id):
                return "Error: Unauthorized access to vehicle outside your fleet."

            trips = await self.uow.repositories.trip.get_trips_by_vehicle(vehicle_id, limit=5)
            
            summary = {
                "vehicle_id": vehicle.id,
                "registration_number": vehicle.registration_number,
                "status": vehicle.status.value if hasattr(vehicle.status, "value") else str(vehicle.status),
                "recent_trips": [
                    {
                        "trip_id": t.id,
                        "business_id": t.trip_id,
                        "status": t.status.value if hasattr(t.status, "value") else str(t.status),
                        "distance": t.actual_distance or t.planned_distance,
                    } for t in trips
                ]
            }
            return json.dumps(summary)

        elif name == "get_related_evidence":
            entity_type_str = args.get("entity_type")
            entity_id = args.get("entity_id")
            if not entity_type_str or not entity_id:
                return "Error: entity_type and entity_id are required."

            try:
                entity_type = EntityType(entity_type_str)
            except ValueError:
                return f"Error: Invalid entity_type {entity_type_str}."

            events = await self.uow.repositories.operational_event.list_events_by_entity(
                entity_type=entity_type,
                entity_id=str(entity_id),
                limit=10
            )

            all_evidence = []
            for ev in events:
                try:
                    evidence_list = await self.uow.repositories.evidence.get_for_event(ev.id)
                    for evidence in evidence_list:
                        all_evidence.append({
                            "evidence_id": str(evidence.id),
                            "event_id": str(evidence.event_id),
                            "type": evidence.evidence_type,
                            "summary": evidence.summary,
                            "status": evidence.status.value if hasattr(evidence.status, 'value') else str(evidence.status)
                        })
                except Exception as ex:
                    logger.warning(f"Failed to fetch evidence for event {ev.id}: {ex}")

            if not all_evidence:
                return "No evidence found for this entity."

            return json.dumps({"related_evidence": all_evidence})

        return f"Error: Unknown tool {name}"
