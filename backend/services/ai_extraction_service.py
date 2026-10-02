import json
import logging
from typing import Optional, Dict, Any
from config import settings

try:
    from openai import AsyncOpenAI
except ImportError:
    AsyncOpenAI = None

logger = logging.getLogger("fleetguard.ai_extraction")

class AIExtractionService:
    def __init__(self):
        self.client = None
        if AsyncOpenAI and settings.OPENAI_API_KEY:
            self.client = AsyncOpenAI(
                api_key=settings.OPENAI_API_KEY,
                base_url=settings.LLM_BASE_URL if settings.LLM_BASE_URL else None
            )
            self.model = settings.OPENAI_MODEL or "gpt-4o-mini"

    @property
    def is_available(self) -> bool:
        return self.client is not None

    async def extract_rc_data(self, raw_text: str) -> Dict[str, Any]:
        if not self.is_available:
            raise RuntimeError("OpenAI client not configured.")

        prompt = f"""
You are an expert Indian Vehicle Registration Certificate (RC) parser.
Extract the following fields from the raw text below.
If a field is completely missing, return null. 
Return ONLY valid JSON matching this schema exactly. Do not wrap in markdown blocks.

Schema:
{{
  "registration_number": "string (e.g. RJ19UF0089, with no spaces)",
  "manufacturer": "string (e.g. MAHINDRA & MAHINDRA LIMITED)",
  "model": "string (e.g. SCORPIO-N D MT 2WD Z8 S 7S, or NT, or MOTOR CYCLE)",
  "fuel_type": "string (e.g. DIESEL, PETROL, CNG, ELECTRIC, BATTERY)",
  "gvw": "string (digits only representing Gross Vehicle Weight or Unladen Weight, e.g. 2020 or 195)"
}}

Raw Text:
{raw_text}
"""
        return await self._call_llm(prompt)

    async def extract_license_data(self, raw_text: str) -> Dict[str, Any]:
        if not self.is_available:
            raise RuntimeError("OpenAI client not configured.")

        prompt = f"""
You are an expert Indian Driving License parser.
Extract the following fields from the raw text below.
If a field is completely missing, return null. 
Return ONLY valid JSON matching this schema exactly.

Schema:
{{
  "name": "string (Full name of the driver)",
  "license_number": "string (e.g. DL-0420110012345)",
  "date_of_birth": "string (YYYY-MM-DD format if possible)",
  "valid_until": "string (YYYY-MM-DD format if possible)",
  "vehicle_class": "string (e.g. MCWG, LMV)"
}}

Raw Text:
{raw_text}
"""
        return await self._call_llm(prompt)

    async def extract_expense_data(self, raw_text: str) -> Dict[str, Any]:
        if not self.is_available:
            raise RuntimeError("OpenAI client not configured.")

        prompt = f"""
You are an expert Fuel Receipt and Expense parser for a fleet management system.
Extract the following fields from the raw text below.
If a field is completely missing, return null. 
Return ONLY valid JSON matching this schema exactly.

Schema:
{{
  "vendor": "string (Name of the fuel station or merchant)",
  "date": "string (YYYY-MM-DD format if possible)",
  "amount": float (Total amount of the receipt as a number),
  "gst_number": "string (if present)"
}}

Raw Text:
{raw_text}
"""
        return await self._call_llm(prompt)

    async def _call_llm(self, prompt: str) -> Dict[str, Any]:
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=1024
            )
            content = response.choices[0].message.content
            
            # Clean up potential markdown code blocks returned by the model
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            elif content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
                
            return json.loads(content.strip())
        except Exception as e:
            logger.error(f"AI Extraction failed: {e}")
            raise RuntimeError(f"AI extraction failed: {str(e)}")

ai_extractor = AIExtractionService()
