import logging
from typing import List, Dict, Any, Optional
import openai
from openai import AsyncOpenAI

from config import settings
from infrastructure.llm.provider import (
    LLMProvider,
    LLMMessage,
    LLMResponse,
    LLMValidationError,
    LLMServiceUnavailableError,
)

logger = logging.getLogger("fleetguard.infrastructure.llm.openai")



class OpenAIProvider(LLMProvider):
    """Implementation of LLMProvider for OpenAI."""

    def __init__(self):
        # Prefer Gemini API key if present
        api_key = settings.GEMINI_API_KEY or settings.OPENAI_API_KEY
        if not api_key:
            logger.warning("API key is not set. LLMProvider will fail on calls.")
        
        base_url = settings.LLM_BASE_URL
        model = settings.OPENAI_MODEL
        
        if settings.GEMINI_API_KEY:
            # When using Gemini API key, we must hit the Gemini OpenAI-compatible endpoint if no custom base_url is set
            if not base_url:
                base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
            # Use gemini model if we are using gemini endpoint. Default to gemini-3.6-flash
            if model == "gpt-4o": # Only override if it wasn't explicitly changed from the default
                model = "gemini-3.6-flash"
            
        masked_key = f"{api_key[:8]}...{api_key[-4:]}" if api_key else "None"
        logger.info(f"Initializing AsyncOpenAI: base_url={base_url}, model={model}, key={masked_key}")
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url, timeout=30.0)
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
        except openai.BadRequestError as e:
            logger.error("OpenAI/Groq chat completion bad request (tool schema or argument validation failure): %s", e)
            raise LLMValidationError(
                "The AI provider could not process the tool parameters for this request. Please try rephrasing your inquiry."
            ) from e
        except (openai.APIConnectionError, openai.APITimeoutError) as e:
            logger.error("OpenAI/Groq API connection or timeout error: %s", e)
            raise LLMServiceUnavailableError("AI provider service temporarily unavailable due to connection timeout.") from e
        except openai.RateLimitError as e:
            logger.error("OpenAI/Groq rate limit exceeded: %s", e)
            raise LLMServiceUnavailableError("AI service rate limit exceeded. Please try again shortly.") from e
        except Exception as e:
            logger.error("OpenAI/Groq chat completion unexpected failure: %s", e)
            raise LLMServiceUnavailableError("AI service temporarily unavailable. Please try again later.") from e
