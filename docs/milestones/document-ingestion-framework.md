# Milestone 10 — Document Ingestion Framework

---

## Overview

This milestone introduces the **Document Ingestion Framework**, the foundational layer of the Document Intelligence Epic. 

It provides a unified entry point for all physical and digital documents (receipts, toll tickets, driver licenses, etc.) arriving at FleetGuard from various sources (WhatsApp, mobile apps, web portal, APIs). It securely accepts the file, tracks its processing status, and stores vital metadata, preparing the document for downstream enrichment and AI processing.

No OCR or AI logic is implemented in this milestone.

---

## Architecture

The framework is built using the standard layered architecture of FleetGuard:

1. **API Router** (`routers/documents.py`): Exposes `POST` and `GET` endpoints. Uses `fastapi.UploadFile` to securely stream incoming multipart form data.
2. **Service Layer** (`services/document_service.py`): Coordinates saving the physical file to storage and instructs the repository to create the database record. Generates UUIDs to prevent filename collisions.
3. **Repository Layer** (`repositories/document_repository.py`): Handles async SQLAlchemy operations (`create`, `get_by_id`, `list_documents`, `update`).
4. **Domain Model** (`models/document.py`): The source of truth for a document's lifecycle. 

---

## Processing States

The `DocumentProcessingStatus` enum tracks the lifecycle of every uploaded document:

- **UPLOADED**: Initial state. File is safely stored on disk and metadata recorded.
- **QUEUED**: Enqueued for background processing (future).
- **PROCESSING**: Currently being analyzed by OCR/AI (future).
- **PROCESSED**: Data successfully extracted (future).
- **FAILED**: Pipeline encountered an error.

---

## Files Created

| File | Purpose |
|---|---|
| `backend/models/document.py` | Defines the `Document` SQLAlchemy model and `DocumentProcessingStatus`. |
| `backend/schemas/document.py` | Pydantic schemas (`DocumentCreate`, `DocumentResponse`, `DocumentUpdate`). |
| `backend/repositories/document_repository.py` | CRUD operations for documents. |
| `backend/services/document_service.py` | File I/O (saving to `uploads/`) and business logic. |
| `backend/routers/documents.py` | FastAPI endpoints (`POST /api/v1/documents`, `GET /api/v1/documents`, `GET /api/v1/documents/{id}`). |

## Files Modified

- `backend/models/__init__.py`: Registered the `Document` model.
- `backend/schemas/__init__.py`: Exported document schemas.
- `backend/services/__init__.py`: Exported `DocumentService` and exceptions.
- `backend/main.py`: Registered `documents_router`.

---

## Current Limitations

- **Local Storage:** For this MVP, physical files are saved locally to an `uploads/` directory on the backend server. In a distributed, production environment, this will need to be refactored in `DocumentService.upload_document` to stream directly to an S3 bucket (or similar cloud storage).
- **Synchronous File I/O:** The `shutil.copyfileobj` call in the service is synchronous and could block the event loop for very large files. Moving to an async file writer (like `aiofiles`) or streaming directly to S3 would resolve this.
- **No Background Workers:** Documents currently remain in the `UPLOADED` state forever because there is no background queue consumer picking them up for processing.

---

## Future Enhancements

- Integrate AWS S3 / Google Cloud Storage for scalable document persistence.
- Add Celery (or similar) to automatically transition documents from `UPLOADED` to `QUEUED` and hand them off to the OCR pipeline.

---

## Next Milestone

**Document Classification**

Implement the logic to automatically categorize incoming documents (e.g., distinguishing a fuel receipt from a toll ticket or invoice).
