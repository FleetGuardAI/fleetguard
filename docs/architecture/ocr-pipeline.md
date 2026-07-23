# OCR Processing Pipeline

## Overview
The OCR Processing Pipeline is an Infrastructure Service responsible for extracting text from physical and digital documents uploaded to FleetGuard. 
It operates strictly as a decoupled text extraction service. It does not validate data, execute business rules, or generate evidence—those responsibilities belong to the Validation Engine and Evidence Framework, respectively.

## Flow & Architecture
The OCR Pipeline follows FleetGuard's Event-Driven Architecture, relying heavily on the new Kafka Event Bus.

1. **Document Upload:** A client uploads a document. The Document Framework persists the file and publishes a `DOCUMENT_UPLOADED` Operational Event.
2. **Consumer:** The `OCRConsumer` (running within its own `ocr-group` Kafka Consumer) detects the event.
3. **Extraction:** The `OCRService` uses the `entity_id` from the event to look up the document's `storage_path`, then delegates to a replaceable `OCRProvider` interface to extract the text.
4. **Publishing:** The service constructs an `OCRResult` payload, creates a new `DOCUMENT_TEXT_EXTRACTED` Operational Event, and saves it via `OperationalEventService.create_event()`.
5. **Invariant Preserved:** By using `OperationalEventService`, the pipeline guarantees the core FleetGuard invariant: *Persist Event -> Publish Event*.

## Pluggable Providers
The pipeline defines an abstract `OCRProvider` interface:
```python
class OCRProvider(ABC):
    async def extract_text(self, file_path: str, mime_type: str) -> OCRResult:
        ...
```
This allows FleetGuard to seamlessly swap underlying text extraction technologies without modifying any upstream or downstream systems. Current/Future providers include:
- `MockOCRProvider` (Local development)
- Azure Document Intelligence
- Google Document AI
- AWS Textract
- OpenAI/Gemini Vision Models

## Event Metadata
The `OCRResult` schema includes extended operational metadata for downstream observability and provider performance comparison:
- `processing_time_ms`: Time taken by the provider to extract text.
- `provider_request_id`: External tracking ID for tracing.
- `metadata`: Arbitrary dictionary containing provider-specific contexts.
