import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import sys

# Mock google.cloud before it gets imported by anything
mock_documentai = MagicMock()
sys.modules['google.cloud'] = MagicMock()
sys.modules['google.cloud.documentai'] = mock_documentai
sys.modules['google.api_core'] = MagicMock()
sys.modules['google.api_core.client_options'] = MagicMock()

from infrastructure.ocr.provider import MockOCRProvider, GoogleDocumentAIProvider, get_ocr_provider
from infrastructure.ocr.models import OCRResult

@pytest.mark.asyncio
async def test_mock_ocr_provider():
    provider = MockOCRProvider()
    result = await provider.extract_text(b"dummy", "image/jpeg")
    assert result.provider_name == "MockOCRProvider"
    assert "MockOCRProvider" in result.provider_name
    assert result.confidence == 0.95

@pytest.mark.asyncio
async def test_google_ocr_provider_init_fails_without_credentials():
    import os
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="GOOGLE_DOCUMENT_AI_PROJECT_ID must be set"):
            GoogleDocumentAIProvider()

@pytest.mark.asyncio
async def test_google_ocr_provider_extract_text():
    import os
    env_vars = {
        "GOOGLE_DOCUMENT_AI_PROJECT_ID": "test-project",
        "GOOGLE_DOCUMENT_AI_LOCATION": "us",
        "GOOGLE_DOCUMENT_AI_RECEIPT_PROCESSOR_ID": "receipt-processor"
    }
    with patch.dict(os.environ, env_vars):
        
        mock_client_instance = MagicMock()
        mock_documentai.DocumentProcessorServiceClient.return_value = mock_client_instance
        
        # Setup mock response
        mock_entity1 = MagicMock()
        type(mock_entity1).type_ = property(lambda self: "supplier_name")
        type(mock_entity1).mention_text = property(lambda self: "Test Vendor")
        type(mock_entity1).confidence = property(lambda self: 0.9)
        
        mock_entity2 = MagicMock()
        type(mock_entity2).type_ = property(lambda self: "total_amount")
        type(mock_entity2).mention_text = property(lambda self: "250.0")
        type(mock_entity2).confidence = property(lambda self: 0.9)
        
        mock_document = MagicMock()
        type(mock_document).text = property(lambda self: "extracted text")
        type(mock_document).entities = property(lambda self: [mock_entity1, mock_entity2])
        
        mock_result = MagicMock()
        type(mock_result).document = property(lambda self: mock_document)
        
        mock_client_instance.process_document.return_value = mock_result
        
        provider = GoogleDocumentAIProvider()
        
        result = await provider.extract_text(b"dummy_image", "image/jpeg", "receipt")
        
        assert result.provider_name == "GoogleDocumentAI"
        assert result.text is not None

def test_get_ocr_provider_mock():
    import os
    with patch.dict(os.environ, {"OCR_PROVIDER": "mock"}):
        provider = get_ocr_provider()
        assert isinstance(provider, MockOCRProvider)

def test_get_ocr_provider_google():
    import os
    with patch.dict(os.environ, {"OCR_PROVIDER": "google", "GOOGLE_DOCUMENT_AI_PROJECT_ID": "test"}):
        provider = get_ocr_provider()
        assert isinstance(provider, GoogleDocumentAIProvider)
