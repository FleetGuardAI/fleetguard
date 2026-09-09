import os
import asyncio
from dotenv import load_dotenv

async def run_minimal_test():
    load_dotenv()
    
    # 1. Verify environment variables
    project_id = os.environ.get("GOOGLE_DOCUMENT_AI_PROJECT_ID")
    location = os.environ.get("GOOGLE_DOCUMENT_AI_LOCATION")
    credentials_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    
    print("Verification:")
    print(f"GOOGLE_DOCUMENT_AI_PROJECT_ID: {'SET' if project_id else 'MISSING'}")
    print(f"GOOGLE_DOCUMENT_AI_LOCATION: {'SET' if location else 'MISSING'}")
    print(f"GOOGLE_APPLICATION_CREDENTIALS: {'SET' if credentials_path else 'MISSING'} ({credentials_path})")
    
    # Verify file exists
    if credentials_path:
        exists = os.path.exists(credentials_path)
        print(f"Credentials file exists: {exists}")
    
    # Check processor IDs
    processors = {
        "RECEIPT_PROCESSOR": os.environ.get("GOOGLE_DOCUMENT_AI_RECEIPT_PROCESSOR_ID"),
        "ID_PROCESSOR": os.environ.get("GOOGLE_DOCUMENT_AI_ID_PROCESSOR_ID"),
        "GENERIC_PROCESSOR": os.environ.get("GOOGLE_DOCUMENT_AI_GENERIC_PROCESSOR_ID")
    }
    
    missing = [k for k, v in processors.items() if not v]
    if missing:
        print(f"\nMissing Processor IDs: {', '.join(missing)}")
    else:
        print("\nAll Processor IDs configured.")
        
    print("\nRunning connectivity test...")
    os.environ["OCR_PROVIDER"] = "google"
    from infrastructure.ocr.provider import get_ocr_provider
    try:
        provider = get_ocr_provider()
        print("PASS: Provider initialized successfully (auth loaded).")
        # Attempt to run list_processors or similar? The provider doesn't expose it directly.
        # But if get_ocr_provider() doesn't fail, google.auth.default() succeeded!
    except Exception as e:
        print(f"FAIL: Connectivity/Auth test failed: {e}")

if __name__ == '__main__':
    asyncio.run(run_minimal_test())
