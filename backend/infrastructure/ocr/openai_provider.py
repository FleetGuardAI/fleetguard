import json
import base64
import time
import uuid
import logging
from typing import Dict, Any

from openai import AsyncOpenAI
from config import settings
from infrastructure.ocr.models import OCRResult
from infrastructure.ocr.provider import OCRProvider

logger = logging.getLogger("fleetguard.infrastructure.ocr.openai")

class OpenAIOCRProvider(OCRProvider):
    """
    OpenAI Vision based OCR Provider.
    Extracts structured receipt data from images.
    """
    
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY or settings.OPENAI_API_KEY
        self.base_url = settings.LLM_BASE_URL
        self.model = settings.OPENAI_MODEL
        
        if settings.GEMINI_API_KEY and not self.base_url:
            self.base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
            if self.model == "gpt-4o":
                self.model = "gemini-3.6-flash"
                
        # Do not initialize AsyncOpenAI if key is missing, handle in extract_text
        self.client = None
        if self.api_key:
            self.client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)

    def _encode_image(self, file_path: str) -> str:
        with open(file_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    async def extract_text(self, file_path: str, mime_type: str) -> OCRResult:
        if not self.client:
            raise RuntimeError("OPENAI_API_KEY is not configured.")

        start_time = time.monotonic()
        
        try:
            base64_image = self._encode_image(file_path)
            
            prompt = """
            Extract the following details from this receipt and return ONLY a valid JSON object:
            - vendor (string)
            - gst_number (string or null)
            - date (YYYY-MM-DD string)
            - amount (float)
            - category (string: FUEL, TOLL, MAINTENANCE, PARKING, FOOD, REPAIR, MISCELLANEOUS)
            - fraud_risk_score (float 0.0 to 1.0)
            - is_suspicious (boolean)
            - fraud_flags (list of strings)
            
            Do not include markdown blocks like ```json. Just the raw JSON.
            """

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{base64_image}"
                                },
                            },
                        ],
                    }
                ],
                max_tokens=500,
                temperature=0.0,
            )
            
            extracted_text = response.choices[0].message.content.strip()
            
            # Clean up markdown if the LLM didn't follow instructions
            if extracted_text.startswith("```json"):
                extracted_text = extracted_text[7:]
            if extracted_text.endswith("```"):
                extracted_text = extracted_text[:-3]
            extracted_text = extracted_text.strip()
            
            end_time = time.monotonic()
            processing_time_ms = int((end_time - start_time) * 1000)

            return OCRResult(
                text=extracted_text,
                confidence=0.9,
                provider_name="OpenAIVisionOCRProvider",
                processing_time_ms=processing_time_ms,
                provider_request_id=str(uuid.uuid4()),
                metadata={"mime_type": mime_type}
            )
        except Exception as e:
            logger.error(f"OpenAI OCR processing failed: {e}")
            raise
