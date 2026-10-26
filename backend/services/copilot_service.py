"""
FleetGuard — Copilot Service
Orchestrates natural language conversations, entity resolution, multi-tool execution,
and safe two-step operational task execution (e.g. Trip Scheduling).
"""

import uuid
import json
import logging
from typing import Dict, Any, List, Optional

from infrastructure.uow import AbstractUnitOfWork
from infrastructure.llm.provider import LLMMessage
from infrastructure.llm.openai_provider import OpenAIProvider
from schemas.copilot import CopilotChatRequest, CopilotChatResponse
from services.copilot_tools import COPILOT_TOOLS_DEFINITION, CopilotToolExecutor

logger = logging.getLogger("fleetguard.services.copilot")


# In-memory conversation store for session history
# Format: conversation_id -> List[LLMMessage]
_conversation_history: Dict[str, List[LLMMessage]] = {}
MAX_HISTORY_MESSAGES = 20
MAX_TOOL_ITERATIONS = 6

SYSTEM_PROMPT = """You are FleetGuard's intelligent fleet operations assistant.

Core Responsibilities:
- Retrieve real-time and historical fleet information grounded strictly in FleetGuard database records.
- Investigate vehicles, driver availability, trips, telemetry, maintenance, and expenses.
- Resolve informal entity names (e.g., "Truck 02", "Tata Signa", "0089", "Joginder") using available tools.
- Assist users in scheduling trips via a safe two-step proposal and confirmation workflow.

Operational Rules & Grounding Constraints:
1. Grounding in Real Data:
   - Never fabricate or assume vehicle IDs, registration numbers, GPS coordinates, timestamps, drivers, diagnostics, expenses, or trip IDs.
   - Always fetch factual data via tools before answering.

2. Fleet Telemetry & Location Inquiries:
   - When asked "Where is Truck 02, and when was its location last updated?", call `get_vehicle_location(query="Truck 02")`. Report the exact timestamp, freshness (Live GPS, Stale GPS, or Unavailable), source, and coordinates.
   - When asked "Tell me the locations of both trucks", "Where are my trucks?", or similar fleet-wide queries, call `get_vehicle_location(query="all")` or `list_vehicles` followed by `get_vehicle_location`.
   - Distinguish whether each vehicle's location is LIVE (recent update), STALE (delayed telemetry), or UNAVAILABLE.
   - If a truck has no telemetry recorded, clearly state that its location is unavailable. NEVER invent coordinates or fake locations.

3. Driver Availability:
   - When asked "Which drivers are available?", call `list_drivers`.
   - Report drivers who are AVAILABLE (active status and not currently on an active trip) versus those who are BUSY_ON_TRIP or INACTIVE.

4. Vehicle Diagnostics & "What is wrong with this vehicle?":
   - When asked "What is wrong with this vehicle?" or about vehicle health, call `get_vehicle_details` (or `get_vehicle_summary`).
   - Inspect the returned `diagnostic_assessment`, maintenance records, and repair tickets.
   - If the vehicle is in MAINTENANCE status but no diagnostic work orders or tickets exist, state clearly that the status is marked as Maintenance, but available database records are insufficient to determine the specific cause. NEVER speculate or fabricate engine issues, part failures, or reasons not recorded in the database.

5. Expenses:
   - When asked "Show me the latest fuel expenses", call `list_expenses(category="FUEL")`. Report the actual expense records (date, amount, currency, vehicle, status).

6. Controlled Trip Scheduling Workflow:
   - You CAN schedule trips, but you MUST follow the safe two-step process:
     Step 1: Validate required details (vehicle, origin, destination, planned departure date/time). If any detail is missing (e.g. user says "Schedule a trip for Truck 02 tomorrow" without origin or destination), ask the user for the missing details.
     Step 2: If the user says "Assign the available driver to this trip", pass `driver_query="available"` to `prepare_trip_proposal`.
     Step 3: Call `prepare_trip_proposal`. Present the returned proposal summary and Proposal ID to the user and request their explicit confirmation. Do NOT call `confirm_trip_execution` until the user explicitly confirms (e.g., "yes", "confirm", "proceed").
     Step 4: When the user confirms, call `confirm_trip_execution` with the `proposal_id`.
   - Never claim a trip has been scheduled or created until `confirm_trip_execution` has successfully executed and returned the verified trip record.

7. Entity Resolution:
   - Pass informal names (e.g. "Truck 02", "Tata", "0089", "driver Joginder") in the `query` or `driver_query` parameters.
   - If a tool returns AMBIGUOUS, present the matching choices to the user and ask for clarification.
   - If a tool returns NOT_FOUND, inform the user honestly and present available fleet options.

8. Presentation:
   - Format responses in clean, professional Markdown.
   - Use clear bullet points, bold labels, and status badges (e.g., 🟢 Live, 🟡 Stale, ⚪ Unavailable).
   - Do not output raw JSON data or internal reasoning to the user.
"""


class CopilotService:
    def __init__(
        self,
        uow: AbstractUnitOfWork,
        company_id: Any,
        user_id: str = "system",
        user_name: str = "Fleet Manager"
    ):
        self.uow = uow
        self.company_id = int(company_id)
        self.user_id = str(user_id)
        self.user_name = user_name
        self.llm = OpenAIProvider()
        self.executor = CopilotToolExecutor(
            uow=self.uow,
            company_id=self.company_id,
            user_id=self.user_id,
            user_name=self.user_name
        )

    async def chat(self, request: CopilotChatRequest) -> CopilotChatResponse:
        conv_id = request.conversation_id or str(uuid.uuid4())

        # Load or initialize history
        messages = _conversation_history.get(conv_id, [])
        if not messages:
            language_instruction = (
                f"\nIMPORTANT: You MUST respond in the language code '{request.language}'. "
                f"If '{request.language}' is 'hi', respond entirely in Hindi (Devanagari script). "
                f"If 'en', respond in English."
            )
            messages.append(LLMMessage(role="system", content=SYSTEM_PROMPT + language_instruction))

        # Append Context if provided and it's a new turn
        user_message_content = request.message
        if request.context and request.context.entity_id:
            context_str = f"[Context: Viewing {request.context.entity_type} {request.context.entity_id} on screen {request.context.screen}]\n"

            # Secure Context Injection: Validate ownership before providing detailed context
            try:
                entity_id = int(request.context.entity_id)
                if request.context.entity_type == "vehicle":
                    vehicle = await self.uow.repositories.vehicle.get_vehicle_by_id(entity_id, self.company_id)
                    if vehicle and str(vehicle.company_id) == str(self.company_id):
                        st = vehicle.status.value if hasattr(vehicle.status, 'value') else vehicle.status
                        context_str += f"[Vehicle Verified: {vehicle.registration_number}, Status: {st}]\n"
                elif request.context.entity_type == "trip":
                    trip = await self.uow.repositories.trip.get_trip_by_id(entity_id)
                    if trip and str(trip.company_id) == str(self.company_id):
                        context_str += f"[Trip Verified: {trip.trip_id}, Route: {trip.origin_location} -> {trip.destination_location}]\n"
            except Exception as e:
                logger.warning(f"Failed to securely resolve context entity: {e}")

            user_message_content = context_str + user_message_content

        messages.append(LLMMessage(role="user", content=user_message_content))

        # Tool calling loop
        iterations = 0
        tools_used = []
        structured_metadata: Dict[str, Any] = {
            "proposals": [],
            "locations": [],
            "action_executed": False
        }

        while iterations < MAX_TOOL_ITERATIONS:
            iterations += 1
            response = await self.llm.chat(messages, tools=COPILOT_TOOLS_DEFINITION)

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
                except (json.JSONDecodeError, TypeError):
                    args = {}

                tools_used.append(func_name)

                try:
                    tool_result_str = await self.executor.execute(func_name, args)

                    # Capture structured payloads for frontend metadata
                    try:
                        parsed_res = json.loads(tool_result_str)
                        if func_name == "prepare_trip_proposal" and parsed_res.get("proposal_id"):
                            structured_metadata["proposals"].append(parsed_res)
                        elif func_name == "confirm_trip_execution" and parsed_res.get("verified"):
                            structured_metadata["action_executed"] = True
                            structured_metadata["verified_trip"] = parsed_res
                        elif func_name == "get_vehicle_location":
                            if parsed_res.get("locations"):
                                structured_metadata["locations"].extend(parsed_res["locations"])
                            else:
                                structured_metadata["locations"].append(parsed_res)
                    except Exception:
                        pass

                except Exception as e:
                    logger.error(f"Error executing tool {func_name}: {e}", exc_info=True)
                    tool_result_str = json.dumps({"error": f"Failed to execute tool {func_name}: {str(e)}"})

                # Append tool result
                messages.append(LLMMessage(
                    role="tool",
                    content=tool_result_str,
                    tool_call_id=tool_call["id"],
                    name=func_name
                ))

        # Save history (bounded)
        _conversation_history[conv_id] = messages[-MAX_HISTORY_MESSAGES:]

        metadata = {
            "tools_used": tools_used,
            **structured_metadata
        }

        return CopilotChatResponse(
            message=messages[-1].content,
            conversation_id=conv_id,
            metadata=metadata
        )
