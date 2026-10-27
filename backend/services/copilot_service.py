"""
FleetGuard — Copilot Service
Orchestrates natural language conversations, entity resolution, multi-tool execution,
safe two-step operational task execution (e.g. Trip Scheduling),
full database conversation persistence, and bounded short-term memory with rolling summarization.
"""

import uuid
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple, Sequence

from config import settings
from infrastructure.uow import AbstractUnitOfWork
from infrastructure.llm.provider import LLMMessage
from infrastructure.llm.openai_provider import OpenAIProvider
from models.conversation import Conversation, ConversationMessage
from schemas.copilot import (
    CopilotChatRequest,
    CopilotChatResponse,
    ConversationOut,
    ConversationListResponse,
    ConversationDetailResponse,
    ConversationMessageOut,
)
from services.copilot_tools import COPILOT_TOOLS_DEFINITION, CopilotToolExecutor

logger = logging.getLogger("fleetguard.services.copilot")

MAX_TOOL_ITERATIONS = 6

SYSTEM_PROMPT = """You are FleetGuard's intelligent fleet operations assistant.

Core Responsibilities:
- Retrieve real-time and historical fleet information grounded strictly in FleetGuard database records.
- Investigate vehicles, driver availability, trips, telemetry, maintenance, and expenses.
- Resolve informal entity names (e.g., "Truck 02", "Tata Signa", "0089", "Joginder") using available tools.
- Assist users in scheduling trips via a safe two-step proposal and confirmation workflow.

Operational Rules & Grounding Constraints:
1. Grounding in Real Data & Tool Calling:
   - Never fabricate or assume vehicle IDs, registration numbers, GPS coordinates, timestamps, drivers, diagnostics, expenses, or trip IDs.
   - Always fetch factual data via tools before answering.
   - When calling tools with optional parameters (e.g. `search`, `is_active`, `status`, `limit`), omit them, pass valid defaults, or pass null if you do not wish to filter by that field.

2. Fleet Telemetry & Location Inquiries (Operational Freshness Standard):
   - When asked where a truck is or about vehicle locations, call `get_vehicle_location(query=...)` or `get_vehicle_location(query="all")`.
   - Authoritative freshness standards:
     * FRESH (Live GPS, age <= 15 minutes): Can be described as the truck's current position.
     * STALE (age > 15 minutes and <= 24 hours): Describe strictly as a LAST-KNOWN LOCATION, NOT current position. Report the recorded time and source.
     * VERY STALE (age > 24 hours): Describe strictly as an outdated last-known position.
     * UNAVAILABLE (no coordinates recorded): Clearly state that no GPS record exists in the database. Distinguish this from delayed telemetry.
     * FUTURE TIMESTAMP (> 60s in future): Flag as invalid telemetry timestamp.
   - Never invent coordinates, timestamps, or fake signals.

3. Driver Availability & Privacy:
   - When asked "Which drivers are available?" or "Tell me driver availability", call `list_drivers`.
   - Present: Driver Name, Availability Status (Available / Busy on Trip / Inactive), and active trip route if busy.
   - Privacy & Data Minimization: Do NOT expose driver phone numbers by default in availability responses unless the user explicitly asks for contact numbers.

4. Vehicle Diagnostics & "What is wrong with this vehicle?":
   - When asked "What is wrong with this vehicle?" or about vehicle health, call `get_vehicle_details` (or `get_vehicle_summary`).
   - Inspect the returned `diagnostic_assessment`, maintenance records, and repair tickets.
   - If the vehicle is in MAINTENANCE status but no diagnostic work orders or tickets exist, state clearly that the status is marked as Maintenance, but available database records are insufficient to determine the specific cause. NEVER speculate or fabricate engine issues or part failures.

5. Expenses:
   - When asked "Show me the latest fuel expenses", call `list_expenses(category="FUEL")`. Report the actual expense records (date, amount, currency, vehicle, status).

6. Controlled Trip Scheduling Workflow:
   - You CAN schedule trips, but you MUST follow the safe two-step process:
     Step 1: Validate required details (vehicle, origin, destination, planned departure date/time). If any detail is missing, ask the user.
     Step 2: If the user says "Assign the available driver to this trip", pass `driver_query="available"` to `prepare_trip_proposal`.
     Step 3: Call `prepare_trip_proposal`. Present the returned proposal summary and Proposal ID to the user and request their explicit confirmation. Do NOT call `confirm_trip_execution` until the user explicitly confirms (e.g., "yes", "confirm", "proceed").
     Step 4: When the user confirms, call `confirm_trip_execution` with the `proposal_id`.
   - Never claim a trip has been scheduled or created until `confirm_trip_execution` has successfully executed and returned the verified trip record.

7. Entity Resolution:
   - Pass informal names (e.g. "Truck 02", "Tata", "0089", "driver Joginder") in the `query` or `driver_query` parameters.
   - If a tool returns AMBIGUOUS, present the matching choices to the user and ask for clarification.
   - If a tool returns NOT_FOUND, inform the user honestly and present available fleet options.

8. Presentation & Anti-Duplication:
   - Format responses in clean, professional Markdown (bullet points, bold labels, readable text).
   - The UI automatically renders interactive cards for structured data (such as vehicle location cards and trip proposals).
   - Do NOT repeat an identical full Markdown table if interactive location or proposal cards are already returned. Instead, provide a concise explanatory summary/bullet list.
   - Do not output raw JSON data, tool schemas, or internal reasoning to the user.
"""


class CopilotService:
    def __init__(
        self,
        uow: AbstractUnitOfWork,
        company_id: Any,
        user_id: Any,
        user_name: str = "Fleet Manager"
    ):
        self.uow = uow
        self.company_id = int(company_id)
        self.user_id = int(user_id) if str(user_id).isdigit() else 1
        self.user_name = user_name
        self.llm = OpenAIProvider()
        self.executor = CopilotToolExecutor(
            uow=self.uow,
            company_id=self.company_id,
            user_id=str(self.user_id),
            user_name=self.user_name
        )

    # --------------------------------------------------------------------------
    # CONVERSATION MANAGEMENT API
    # --------------------------------------------------------------------------

    async def list_conversations(
        self,
        limit: int = 20,
        offset: int = 0
    ) -> ConversationListResponse:
        """Lists active conversations for the authenticated user and company."""
        convs, total = await self.uow.repositories.conversation.list_conversations(
            user_id=self.user_id,
            company_id=self.company_id,
            limit=limit,
            offset=offset
        )

        outs = []
        for c in convs:
            # Fetch message count and preview
            msgs = await self.uow.repositories.conversation.get_messages(c.id, limit=1)
            preview = msgs[0].content[:60] if msgs else None
            all_msgs = await self.uow.repositories.conversation.get_messages(c.id)
            user_visible_count = sum(1 for m in all_msgs if m.role in ("user", "assistant"))
            outs.append(
                ConversationOut(
                    id=c.id,
                    title=c.title,
                    summary=c.summary,
                    created_at=c.created_at,
                    updated_at=c.updated_at,
                    message_count=user_visible_count,
                    last_message_preview=preview
                )
            )

        return ConversationListResponse(
            conversations=outs,
            total_count=total,
            limit=limit,
            offset=offset
        )

    async def get_conversation_detail(
        self,
        conversation_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> ConversationDetailResponse:
        """Retrieves conversation and its messages. Enforces strict company and user scoping."""
        conv = await self.uow.repositories.conversation.get_conversation(
            conversation_id=conversation_id,
            user_id=self.user_id,
            company_id=self.company_id
        )
        if not conv:
            raise PermissionError("Conversation not found or unauthorized access.")

        db_msgs = await self.uow.repositories.conversation.get_messages(
            conversation_id=conversation_id,
            limit=limit,
            offset=offset
        )

        # Only return user and assistant messages for UI presentation
        msg_outs = [
            ConversationMessageOut(
                id=m.id,
                conversation_id=m.conversation_id,
                sequence_number=m.sequence_number,
                role=m.role,
                content=m.content,
                name=m.name,
                tool_call_id=m.tool_call_id,
                tool_calls=m.tool_calls,
                message_metadata=m.message_metadata,
                created_at=m.created_at
            )
            for m in db_msgs
            if m.role in ("user", "assistant")
        ]

        conv_out = ConversationOut(
            id=conv.id,
            title=conv.title,
            summary=conv.summary,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
            message_count=len(msg_outs)
        )

        return ConversationDetailResponse(
            conversation=conv_out,
            messages=msg_outs
        )

    async def create_conversation(
        self,
        title: Optional[str] = None
    ) -> ConversationOut:
        """Explicitly starts a fresh conversation."""
        conv_id = str(uuid.uuid4())
        conv = await self.uow.repositories.conversation.create_conversation(
            conversation_id=conv_id,
            user_id=self.user_id,
            company_id=self.company_id,
            title=title or "New Conversation"
        )
        await self.uow.commit()

        return ConversationOut(
            id=conv.id,
            title=conv.title,
            summary=conv.summary,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
            message_count=0
        )

    async def update_conversation_title(
        self,
        conversation_id: str,
        title: str
    ) -> ConversationOut:
        """Renames a conversation."""
        conv = await self.uow.repositories.conversation.update_title(
            conversation_id=conversation_id,
            user_id=self.user_id,
            company_id=self.company_id,
            new_title=title
        )
        if not conv:
            raise PermissionError("Conversation not found or unauthorized access.")
        await self.uow.commit()

        return ConversationOut(
            id=conv.id,
            title=conv.title,
            summary=conv.summary,
            created_at=conv.created_at,
            updated_at=conv.updated_at
        )

    async def delete_conversation(
        self,
        conversation_id: str
    ) -> bool:
        """Soft-deletes a conversation."""
        ok = await self.uow.repositories.conversation.delete_conversation(
            conversation_id=conversation_id,
            user_id=self.user_id,
            company_id=self.company_id
        )
        if not ok:
            raise PermissionError("Conversation not found or unauthorized access.")
        await self.uow.commit()
        return True

    async def clear_all_conversations(self) -> int:
        """Clears all conversations for the authenticated user and company."""
        count = await self.uow.repositories.conversation.clear_all_conversations(
            user_id=self.user_id,
            company_id=self.company_id
        )
        await self.uow.commit()
        return count

    # --------------------------------------------------------------------------
    # SHORT-TERM CONTEXT & SUMMARIZATION LOGIC
    # --------------------------------------------------------------------------

    @staticmethod
    def _slice_safe_context_window(
        messages: Sequence[Any],
        max_window: int = 20,
        max_messages: Optional[int] = None
    ) -> Tuple[List[Any], List[Any]]:
        """
        Splits messages into (older, recent) such that the recent window does not exceed
        max_window while guaranteeing that no tool-result message is separated from its
        originating assistant tool_calls message.
        """
        limit = max_messages if max_messages is not None else max_window
        msg_list = list(messages)
        if len(msg_list) <= limit:
            return [], msg_list

        split_idx = len(msg_list) - limit

        # Never start recent window with a 'tool' role message; shift backward to include assistant caller
        while split_idx > 0 and msg_list[split_idx].role == "tool":
            split_idx -= 1

        # If the message directly preceding split_idx was an assistant tool call, include it
        if split_idx > 0 and msg_list[split_idx - 1].tool_calls:
            split_idx -= 1

        return msg_list[:split_idx], msg_list[split_idx:]

    async def _summarize_older_messages(
        self,
        existing_summary: Optional[str],
        older_messages: List[ConversationMessage]
    ) -> Optional[str]:
        """
        Creates or updates a compact rolling summary of older conversational context
        without asserting real-time facts. Bounded to COPILOT_MAX_SUMMARY_TOKENS.
        """
        if not older_messages:
            return existing_summary

        # Format transcript of older messages for summarization
        transcript_lines = []
        for m in older_messages:
            if m.role in ("user", "assistant"):
                preview = m.content[:300].replace("\n", " ")
                transcript_lines.append(f"{m.role.capitalize()}: {preview}")

        if not transcript_lines:
            return existing_summary

        transcript = "\n".join(transcript_lines)
        base_prompt = (
            "Summarize the key operational context from this earlier conversation thread in 2-3 concise bullet points. "
            "Focus strictly on entities discussed (specific vehicle registrations, drivers, trip routes), user preferences, "
            "and unresolved requests. Do NOT state current locations or telemetry as permanent facts. Keep under 100 words.\n\n"
        )
        if existing_summary:
            base_prompt += f"Previous context summary:\n{existing_summary}\n\nNew messages to incorporate:\n{transcript}"
        else:
            base_prompt += f"Messages to summarize:\n{transcript}"

        try:
            summary_msgs = [
                LLMMessage(role="system", content="You are a concise conversation summarizer."),
                LLMMessage(role="user", content=base_prompt)
            ]
            res = await self.llm.chat(summary_msgs, temperature=0.0)
            summary_text = res.message.content.strip() if res.message.content else None
            return summary_text or existing_summary
        except Exception as e:
            logger.warning(f"Failed to generate rolling summary: {e}")
            return existing_summary

    @staticmethod
    def _to_llm_message(m: ConversationMessage) -> LLMMessage:
        return LLMMessage(
            role=m.role,
            content=m.content or "",
            name=m.name,
            tool_call_id=m.tool_call_id,
            tool_calls=m.tool_calls
        )

    # --------------------------------------------------------------------------
    # CHAT EXECUTION
    # --------------------------------------------------------------------------

    async def chat(self, request: CopilotChatRequest) -> CopilotChatResponse:
        """
        Processes a chat request:
        1. Resolves or initializes persistent conversation.
        2. Persists the user's message immediately.
        3. Constructs bounded LLM context with rolling summary of older context.
        4. Executes tool calls via CopilotToolExecutor.
        5. Persists assistant response and structured metadata.
        """
        conv_id = request.conversation_id or str(uuid.uuid4())

        # 1. Resolve or Create Conversation
        conv = await self.uow.repositories.conversation.get_conversation(
            conversation_id=conv_id,
            user_id=self.user_id,
            company_id=self.company_id
        )

        if not conv:
            if request.conversation_id:
                # Client passed conversation_id that does not exist or belongs to another user/company
                raise PermissionError("Conversation not found or unauthorized access.")
            
            # Derive human-readable title from user message
            title = request.message.strip().split("\n")[0][:45] or "New Conversation"
            conv = await self.uow.repositories.conversation.create_conversation(
                conversation_id=conv_id,
                user_id=self.user_id,
                company_id=self.company_id,
                title=title
            )
        elif conv.title == "New Conversation" and request.message.strip():
            # Update default title with first actual message
            derived = request.message.strip().split("\n")[0][:45]
            await self.uow.repositories.conversation.update_title(
                conv_id, self.user_id, self.company_id, derived
            )

        # 2. Secure Context Injection
        user_message_content = request.message
        if request.context and request.context.entity_id:
            context_str = f"[Context: Viewing {request.context.entity_type} {request.context.entity_id} on screen {request.context.screen}]\n"
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

        # 3. Persist User Message Immediately
        user_msg_record = await self.uow.repositories.conversation.add_message(
            conversation_id=conv_id,
            role="user",
            content=user_message_content,
            message_metadata={
                "raw_message": request.message,
                "context": request.context.model_dump() if request.context else None
            }
        )
        # Commit user message immediately to guarantee persistence even if downstream LLM fails
        if hasattr(self.uow, "commit") and callable(self.uow.commit):
            await self.uow.commit()
        elif hasattr(self.uow, "session") and hasattr(self.uow.session, "commit") and callable(self.uow.session.commit):
            await self.uow.session.commit()

        # 4. Fetch Full Persisted Transcripts and Construct Bounded Model Context
        all_db_msgs = await self.uow.repositories.conversation.get_messages(conv_id)

        max_window = getattr(settings, "COPILOT_MAX_CONTEXT_MESSAGES", 20)
        older_msgs, recent_msgs = self._slice_safe_context_window(all_db_msgs, max_window)

        # 5. Rolling Summarization for older context
        active_summary = conv.summary
        if older_msgs and getattr(settings, "COPILOT_ENABLE_SUMMARIZATION", True):
            new_summary = await self._summarize_older_messages(active_summary, older_msgs)
            if new_summary != active_summary:
                active_summary = new_summary
                await self.uow.repositories.conversation.update_summary(
                    conv_id, self.user_id, self.company_id, active_summary
                )
                await self.uow.commit()

        # 6. Assemble LLM Messages
        llm_messages: List[LLMMessage] = []
        language_instruction = (
            f"\nIMPORTANT: You MUST respond in the language code '{request.language}'. "
            f"If '{request.language}' is 'hi', respond entirely in Hindi (Devanagari script). "
            f"If 'en', respond in English."
        )
        system_content = SYSTEM_PROMPT + language_instruction
        if active_summary:
            system_content += f"\n\n[Summary of earlier conversation context]:\n{active_summary}\n"

        llm_messages.append(LLMMessage(role="system", content=system_content))

        for db_m in recent_msgs:
            llm_messages.append(self._to_llm_message(db_m))

        # 7. Multi-turn Tool Calling Loop
        iterations = 0
        tools_used = []
        structured_metadata: Dict[str, Any] = {
            "proposals": [],
            "locations": [],
            "action_executed": False
        }

        while iterations < MAX_TOOL_ITERATIONS:
            iterations += 1
            response = await self.llm.chat(llm_messages, tools=COPILOT_TOOLS_DEFINITION)

            ai_msg = response.message
            llm_messages.append(ai_msg)

            if not ai_msg.tool_calls:
                # Final response reached
                break

            # Persist intermediate assistant tool call to database
            await self.uow.repositories.conversation.add_message(
                conversation_id=conv_id,
                role="assistant",
                content=ai_msg.content or "",
                tool_calls=ai_msg.tool_calls
            )

            # Execute each requested tool
            for tool_call in ai_msg.tool_calls:
                func_name = tool_call["function"]["name"]
                try:
                    args = json.loads(tool_call["function"]["arguments"])
                except (json.JSONDecodeError, TypeError):
                    args = {}

                tools_used.append(func_name)

                try:
                    tool_result_str = await self.executor.execute(func_name, args)

                    # Extract structured cards for UI presentation
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

                # Persist tool execution result
                await self.uow.repositories.conversation.add_message(
                    conversation_id=conv_id,
                    role="tool",
                    content=tool_result_str,
                    tool_call_id=tool_call["id"],
                    name=func_name
                )

                # Append tool result to working LLM message queue
                llm_messages.append(LLMMessage(
                    role="tool",
                    content=tool_result_str,
                    tool_call_id=tool_call["id"],
                    name=func_name
                ))

        # 8. Persist Final Assistant Response
        final_answer = llm_messages[-1].content or ""
        metadata = {
            "tools_used": tools_used,
            **structured_metadata
        }

        await self.uow.repositories.conversation.add_message(
            conversation_id=conv_id,
            role="assistant",
            content=final_answer,
            message_metadata=metadata
        )
        if hasattr(self.uow, "commit") and callable(self.uow.commit):
            await self.uow.commit()
        elif hasattr(self.uow, "session") and hasattr(self.uow.session, "commit") and callable(self.uow.session.commit):
            await self.uow.session.commit()

        return CopilotChatResponse(
            message=final_answer,
            conversation_id=conv_id,
            metadata=metadata
        )
