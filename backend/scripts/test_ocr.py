import asyncio
import os
import sys

# Setup python path to include backend root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from infrastructure.ocr.provider import OCRSpaceProvider
from config import settings

async def test_ocr():
    print(f"Testing OCR with provider: OCR_SPACE")
    print(f"API Key: {settings.OCR_SPACE_API_KEY}")
    
    provider = OCRSpaceProvider(api_key=settings.OCR_SPACE_API_KEY)
    
    image_path = r"C:\Users\Suryansh Chaudhary\.gemini\antigravity-ide\brain\79018e0d-9139-4c08-8539-fc0ed4437b6d\.user_uploaded\media_1790369893198.png"
    
    if not os.path.exists(image_path):
        print(f"Image not found at {image_path}")
        return
        
    print(f"Reading image: {image_path}")
    with open(image_path, "rb") as f:
        image_bytes = f.read()
        
    print(f"Image size: {len(image_bytes) / 1024:.2f} KB")
        
    print("Calling OCR Provider...")
    try:
        result = await provider.extract_text(image_bytes, "image/png", "receipt")
        
        print("\n=== OCR RESULTS ===")
        print(f"Vendor: {result.extracted_fields.get('MerchantName')}")
        print(f"Amount: {result.extracted_fields.get('Total')}")
        print(f"Date: {result.extracted_fields.get('TransactionDate')}")
        print(f"GST Number: {result.extracted_fields.get('MerchantTaxId')}")
        print(f"Fraud Risk Score: N/A")
        print(f"Confidence: {result.confidence}")
        
        print("\n--- Raw Extracted Text ---")
        print(result.text)
        print("--------------------------")
        
    except Exception as e:
        print(f"OCR failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_ocr())
