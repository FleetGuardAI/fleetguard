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

def test_get_ocr_provider_ocr_space():
    import os
    with patch.dict(os.environ, {"OCR_PROVIDER": "ocr_space", "OCR_SPACE_API_KEY": "test-key"}):
        from infrastructure.ocr.provider import OCRSpaceProvider
        provider = get_ocr_provider()
        assert isinstance(provider, OCRSpaceProvider)
        assert provider.api_key == "test-key"

def test_ocr_space_provider_missing_key():
    import os
    from infrastructure.ocr.provider import OCRSpaceProvider
    with patch.dict(os.environ, {"OCR_PROVIDER": "ocr_space"}, clear=True):
        with pytest.raises(ValueError, match="OCR_SPACE_API_KEY must be set"):
            OCRSpaceProvider(api_key="")

@pytest.mark.asyncio
async def test_ocr_space_provider_success():
    from infrastructure.ocr.provider import OCRSpaceProvider
    import httpx
    provider = OCRSpaceProvider(api_key="test-key")
    
    # Mock httpx.AsyncClient.post
    mock_post = AsyncMock()
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "IsErroredOnProcessing": False,
        "ParsedResults": [
            {"ParsedText": "Line 1"},
            {"ParsedText": "Line 2"}
        ],
        "SearchablePDFURL": "https://test.url"
    }
    mock_post.return_value = mock_response

    with patch("httpx.AsyncClient.post", mock_post):
        result = await provider.extract_text(b"test_image", "image/jpeg", "receipt")
        
        assert result.provider_name == "ocr_space"
        assert result.text == "Line 1\nLine 2"
        assert result.provider_request_id == "https://test.url"
        
        # Verify API key is sent via header
        mock_post.assert_called_once()
        kwargs = mock_post.call_args.kwargs
        assert "headers" in kwargs
        assert kwargs["headers"]["apikey"] == "test-key"
        
        # Verify file is not logged or in URL
        assert "test_image" not in kwargs.get("params", {})

@pytest.mark.asyncio
async def test_ocr_space_provider_api_error():
    from infrastructure.ocr.provider import OCRSpaceProvider
    import httpx
    provider = OCRSpaceProvider(api_key="test-key")
    
    mock_post = AsyncMock()
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "IsErroredOnProcessing": True,
        "ErrorMessage": ["File too large"]
    }
    mock_post.return_value = mock_response

    with patch("httpx.AsyncClient.post", mock_post):
        with pytest.raises(RuntimeError, match="OCR Space processing failed"):
            await provider.extract_text(b"test_image", "image/jpeg", "receipt")

@pytest.mark.asyncio
async def test_ocr_space_provider_timeout():
    from infrastructure.ocr.provider import OCRSpaceProvider
    import httpx
    provider = OCRSpaceProvider(api_key="test-key")
    
    mock_post = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))

    with patch("httpx.AsyncClient.post", mock_post):
        with pytest.raises(RuntimeError, match="OCR Space API request timed out"):
            await provider.extract_text(b"test_image", "image/jpeg", "receipt")

@pytest.mark.asyncio
async def test_ocr_space_provider_malformed_json():
    from infrastructure.ocr.provider import OCRSpaceProvider
    import httpx
    provider = OCRSpaceProvider(api_key="test-key")
    
    mock_post = AsyncMock()
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.side_effect = ValueError("Invalid JSON")
    mock_post.return_value = mock_response

    with patch("httpx.AsyncClient.post", mock_post):
        with pytest.raises(RuntimeError, match="OCR Space returned malformed JSON"):
            await provider.extract_text(b"test_image", "image/jpeg", "receipt")

@pytest.mark.asyncio
async def test_ocr_space_provider_empty_result():
    from infrastructure.ocr.provider import OCRSpaceProvider
    import httpx
    provider = OCRSpaceProvider(api_key="test-key")
    
    mock_post = AsyncMock()
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "IsErroredOnProcessing": False,
        "ParsedResults": []
    }
    mock_post.return_value = mock_response

    with patch("httpx.AsyncClient.post", mock_post):
        result = await provider.extract_text(b"test_image", "image/jpeg", "receipt")
        assert result.provider_name == "ocr_space"
        assert result.text == ""
        assert "No ParsedResults" in result.metadata["info"]
