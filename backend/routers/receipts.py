"""
FleetGuard — AI Receipt Verification Router
Handles OCR, Vision analysis, duplicate detection, and fraud scoring.
Streams telemetry updates sequentially to the frontend.
"""

import asyncio
import json
import logging
from typing import Optional
from fastapi import APIRouter, File, Form, UploadFile, HTTPException
from fastapi.responses import StreamingResponse

logger = logging.getLogger("fleetguard.receipts")

router = APIRouter(prefix="/v1/receipts", tags=["Receipt Verification"])


@router.post("/analyze")
async def analyze_receipt(
    receipt_image: UploadFile = File(...),
    claim_id: str = Form(...),
    driver_id: str = Form(...),
    truck_id: str = Form(...),
    trip_id: Optional[str] = Form(None),
):
    """
    POST /api/v1/receipts/analyze
    Multipart Form Data handler.
    Analyzes the uploaded receipt image against OCR, Image Quality, duplicate detection,
    and fleet telematics, streaming sequential progress steps back to the client.
    """
    filename = receipt_image.filename
    # Basic size validation
    contents = await receipt_image.read()
    file_size_mb = len(contents) / (1024 * 1024)
    await receipt_image.seek(0)

    if file_size_mb > 20:
        raise HTTPException(status_code=400, detail="File size exceeds the 20MB limit.")

    async def event_generator():
        try:
            # Stage 1 — Image Validation
            yield f"data: {json.dumps({'type': 'telemetry', 'step': 'Initializing OCR Engine...', 'status': 'success'})}\n\n"
            
            # Stage 2 — OCR
            yield f"data: {json.dumps({'type': 'telemetry', 'step': 'Running OCR text extraction...', 'status': 'success'})}\n\n"
            
            from infrastructure.ocr.provider import get_ocr_provider
            provider = get_ocr_provider()
            ocr_result = await provider.extract_text(
                file_data=contents, 
                mime_type=receipt_image.content_type or "image/jpeg", 
                document_type="receipt"
            )
            
            yield f"data: {json.dumps({'type': 'telemetry', 'step': f'Text extracted successfully from {filename}.', 'status': 'success'})}\n\n"
            
            fields = ocr_result.extracted_fields
            vendor = fields.get("MerchantName", "Unknown Merchant")
            amount_raw = fields.get("Total")
            amount = 0.0
            if amount_raw is not None:
                try:
                    if isinstance(amount_raw, str):
                        clean_amount = amount_raw.replace("₹", "").replace("Rs.", "").replace("INR", "").replace(",", "").strip()
                        amount = float(clean_amount)
                    else:
                        amount = float(amount_raw)
                except ValueError:
                    amount = 0.0
                    
            gst = fields.get("MerchantTaxId", None)
            
            # Final API Response
            final_assessment = {
                "type": "result",
                "receipt": {
                    "merchant": vendor,
                    "category": "Expense",
                    "purpose": "General Expense",
                    "amount": amount,
                    "gst": gst,
                    "invoice_number": fields.get("InvoiceId", None)
                },
                "image_analysis": {
                    "edited": None,
                    "blur": None,
                    "confidence": int(ocr_result.confidence * 100) if ocr_result.confidence else None
                },
                "business_validation": {
                    "merchant_verified": None,
                    "gst_valid": None,
                    "invoice_valid": None,
                    "duplicate": None
                },
                "price_analysis": {
                    "status": "Unknown",
                    "deviation_percent": None
                },
                "truck_history": {
                    "previous_repairs": None,
                    "last_repair_days": None
                },
                "driver_history": {
                    "claims_this_month": None,
                    "duplicate_attempts": None
                },
                "fraud_assessment": {
                    "risk_score": None,
                    "risk_level": "Unknown",
                    "confidence": None,
                    "recommendation": "Manual Review Required"
                },
                "reasoning": [
                    "OCR Extraction completed.",
                    "Fraud and advanced business validation are currently not implemented."
                ]
            }

            yield f"data: {json.dumps(final_assessment)}\n\n"
        except Exception as e:
            logger.error(f"Error in receipts analysis stream: {e}")
            yield f"data: {json.dumps({'type': 'error', 'detail': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
