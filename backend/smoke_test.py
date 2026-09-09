import os
import io
import asyncio
from PIL import Image, ImageDraw, ImageFont

def generate_test_image(text_lines):
    img = Image.new('RGB', (800, 600), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    y = 50
    for line in text_lines:
        d.text((50, y), line, fill=(0,0,0))
        y += 40
    
    buf = io.BytesIO()
    img.save(buf, format='JPEG')
    return buf.getvalue()

async def run_tests():
    from dotenv import load_dotenv
    load_dotenv()
    from infrastructure.ocr.provider import get_ocr_provider
    import os
    os.environ["OCR_PROVIDER"] = "google"
    
    init_error = None
    try:
        provider = get_ocr_provider()
    except Exception as e:
        provider = None
        init_error = e
    
    docs = {
        "Receipt": [
            "Walmart",
            "Date: 2023-10-25",
            "Total Amount: $250.00",
            "Tax: $25.00"
        ],
        "Driving License": [
            "DRIVER LICENSE",
            "First Name: John",
            "Last Name: Doe",
            "DOB: 01/01/1980",
            "EXP: 12/31/2030",
            "DLN: D12345678"
        ],
        "Aadhaar/ID": [
            "Government of India",
            "First Name: Rahul",
            "Last Name: Sharma",
            "DOB: 15/08/1990",
            "Aadhaar No: 1234 5678 9012"
        ],
        "RC": [
            "CERTIFICATE OF REGISTRATION",
            "Registration No: MH 12 AB 1234",
            "Owner: Rajesh Kumar",
            "Valid Upto: 25/12/2035"
        ],
        "PUC": [
            "POLLUTION UNDER CONTROL CERTIFICATE",
            "Reg No: MH 12 AB 1234",
            "Valid Till: 30/06/2027"
        ],
        "Insurance": [
            "VEHICLE INSURANCE POLICY",
            "Policy No: POL987654321",
            "Valid To: 14/02/2025"
        ]
    }
    
    doc_types_map = {
        "Receipt": "receipt",
        "Driving License": "idDocument",
        "Aadhaar/ID": "idDocument",
        "RC": "idDocument",
        "PUC": "generic",
        "Insurance": "generic"
    }

    print(f"{'Document Type':<20} | {'Status':<12} | {'Fields Extracted':<30} | {'Expiry Found'}")
    print("-" * 80)
    
    for doc_name, lines in docs.items():
        image_bytes = generate_test_image(lines)
        doc_type_hint = doc_types_map[doc_name]
        
        status = "NOT TESTED"
        fields = "{}"
        expiry = "N/A"
        
        try:
            if init_error:
                raise init_error
                
            result = await provider.extract_text(image_bytes, "image/jpeg", doc_type_hint)
            if result and result.text:
                status = "PASS"
                fields_dict = result.extracted_fields
                fields = str(list(fields_dict.keys()))
                if not fields_dict:
                    status = "RAW TEXT ONLY"
                
                # Check for expiry fields specifically
                expiry_keys = ["DateOfExpiration", "Valid Upto", "Valid Till", "Valid To", "ExpirationDate", "ExpiryDate", "Expiration"]
                found_expiry = any(k in fields_dict for k in expiry_keys)
                if found_expiry:
                    expiry = "YES"
                else:
                    expiry = "NO"
            else:
                status = "FAIL"
        except Exception as e:
            status = f"FAIL"
            fields = str(e)[:30] + "..." if len(str(e)) > 30 else str(e)
            
        print(f"{doc_name:<20} | {status:<12} | {fields:<30} | {expiry}")

if __name__ == '__main__':
    asyncio.run(run_tests())
