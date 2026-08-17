import logging
from typing import List, Dict, Any, Optional
import openai
from openai import AsyncOpenAI

from config import settings
from infrastructure.llm.provider import LLMProvider, LLMMessage, LLMResponse

logger = logging.getLogger("fleetguard.infrastructure.llm.openai")


class OpenAIProvider(LLMProvider):
    """Implementation of LLMProvider for OpenAI."""

    def __init__(self):
        # Prefer Gemini API key if present
        api_key = settings.GEMINI_API_KEY or settings.OPENAI_API_KEY
        if not api_key:
            logger.warning("API key is not set. LLMProvider will fail on calls.")
        
        base_url = None
        model = settings.OPENAI_MODEL
        
        if settings.GEMINI_API_KEY:
            # When using Gemini API key, we must hit the Gemini OpenAI-compatible endpoint
            base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
            # Use gemini model if we are using gemini endpoint. Default to gemini-2.5-flash
            model = "gemini-2.5-flash"
            
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    async def chat(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.0,
    ) -> LLMResponse:
        # Convert our LLMMessage format to OpenAI format
        oai_messages = []
        for msg in messages:
            m = {"role": msg.role, "content": msg.content}
            if msg.name:
                m["name"] = msg.name
            if msg.tool_call_id:
                m["tool_call_id"] = msg.tool_call_id
            if msg.tool_calls:
                m["tool_calls"] = msg.tool_calls
            oai_messages.append(m)

        kwargs = {
            "model": self.model,
            "messages": oai_messages,
            "temperature": temperature,
        }
        if tools:
            # We assume tools are passed exactly in the format OpenAI expects
            # e.g., [{"type": "function", "function": {"name": ..., "description": ..., "parameters": ...}}]
            kwargs["tools"] = tools

        try:
            response = await self.client.chat.completions.create(**kwargs)
            choice = response.choices[0]
            
            tool_calls_raw = choice.message.tool_calls
            tool_calls = None
            if tool_calls_raw:
                tool_calls = [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        }
                    }
                    for tc in tool_calls_raw
                ]

            llm_message = LLMMessage(
                role=choice.message.role,
                content=choice.message.content or "",
                tool_calls=tool_calls,
            )

            return LLMResponse(
                message=llm_message,
                finish_reason=choice.finish_reason,
            )
        except Exception as e:
            logger.error("OpenAI chat completion failed: %s", e)
            raise
