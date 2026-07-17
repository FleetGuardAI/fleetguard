# Milestone — Document Module Refactor

---

## Overview

This milestone refactors the Document module, pivoting it from a pipeline-centric
business object into a pure **infrastructure component**.

Previously, the Document module was designed to hold business intelligence such as OCR output (`extracted_data`) and to track its own processing lifecycle (`DocumentProcessingStatus`). 

Under the revised architecture, a `Document` strictly represents a physical file resting in storage. It is unaware of AI, OCR, or validation logic.

---

## Why the Responsibilities Changed

In FleetGuard's Event-Driven Architecture, **Operational Events** are the single source of truth for business activity. 

If a Document held its own validation state and business data, it would violate this principle, creating a secondary source of truth. By demoting the Document to an infrastructure resource, we maintain a clean separation of concerns:
- **Documents** store bytes and metadata.
- **Operational Events** store business facts.
- **Evidence Providers (Future)** will fetch the Document, run OCR/AI, and attach the results to the Operational Event, *not* the Document.

---

## What Was Removed

The following concepts have been completely stripped from the Document module:

- `extracted_data` column and schema fields.
- `DocumentProcessingStatus` enum (which contained `QUEUED`, `PROCESSING`, and `PROCESSED`).
- Any downstream processing references in the `DocumentRepository` and `DocumentService`.

---

## New Infrastructure Status

The processing lifecycle has been replaced by the `DocumentStorageStatus` enum, reflecting only the physical state of the file:

- **UPLOADED**: File received, sitting in a temporary buffer.
- **STORED**: File successfully saved to persistent physical storage.
- **AVAILABLE**: File is indexed and safely accessible to other modules.
- **FAILED**: Storage pipeline encountered an I/O or network error.

---

## How Future Modules Will Use Documents

1. **Client Upload**: A driver uploads a receipt via the mobile app. The `DocumentService` returns a `DocumentResponse` with a UUID.
2. **Event Creation**: The mobile app submits an `OperationalEventCreate` payload (e.g., `FUEL_FILLED`) and includes the `document_id` in the payload as an evidence reference.
3. **Evidence Framework**: The Validation Engine sees the `document_id`, fetches the physical file via the Document API, passes it to the OCR engine, and stores the OCR output directly on the `OperationalEvent` metadata.

The Document itself never changes during this process; it remains purely an immutable infrastructure resource.
