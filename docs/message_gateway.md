# Communication Gateway Framework

## Architecture Overview
The Communication Gateway Framework serves as the unified entry point for all external, unstructured communication entering the FleetGuard platform. 

It provides a vendor-agnostic abstraction layer (e.g., WhatsApp, Email, SMS) designed to intercept inbound webhooks, normalize proprietary payloads into standard internal models, extract attachments, and maintain strict isolation from downstream business intelligence.

### Scope and Boundaries
**The Communication Gateway DOES:**
- Receive inbound messages via registered channel adapters.
- Validate payload integrity (e.g., verifying required fields, sender formats).
- Normalize disparate vendor timestamps and text fields into uniform structures.
- Extract file references into immutable `Attachment` objects (including metadata such as `checksum`, `file_size`, and `media_type`).
- Guarantee execution isolation across channels via the `CommunicationGatewayExecutor`.

**The Communication Gateway DOES NOT:**
- Parse, OCR, or classify the contents of documents/images. 
- Execute intelligence rules or update vehicle states.
- Emit Operational Events directly to the event bus (this occurs downstream).

## Execution Lifecycle
1. **Webhook Reception**: An external system (e.g., Twilio, WhatsApp Business) posts a webhook to the API boundary.
2. **Channel Resolution**: The API extracts the channel key and passes the raw payload to the `CommunicationGatewayExecutor` (`process_webhook(channel_key, payload)`).
3. **Validation**: The mapped channel adapter (e.g., `WhatsAppChannel`) executes `.validate()`. If validation fails, processing halts cleanly with a `VALIDATION_ERROR`.
4. **Extraction**: The adapter executes `.extract_attachments()`, retrieving any nested media data and constructing `Attachment` objects.
5. **Normalization**: The adapter executes `.normalize()`, mapping the raw JSON into the uniform `Communication` model.
6. **Return**: The executor returns a `CommunicationProcessingResult` which contains the final `message` and execution metadata.

## Core Models
- `Communication`: The immutable standard representation of a message.
- `Attachment`: An immutable descriptor for a file. Contains explicit fields for `storage_uri`, `checksum`, `media_type`, and `file_size` to assist downstream caching and processing engines.
- `CommunicationProcessingResult`: A wrapper conveying success/failure without throwing unhandled HTTP 500s back to external webhook providers.

## Extension Guide
To integrate a new vendor (e.g., Email):
1. Create `infrastructure/communication/channels/email.py`.
2. Inherit from `BaseCommunicationChannel`.
3. Implement `validate()`, `extract_attachments()`, and `normalize()`.
4. Register the new channel in the global `CommunicationChannelRegistry` during application startup.

## Anti-Patterns
- **Business Logic Leakage**: Do not attempt to read the text body to determine if a message is an "Invoice" or a "Maintenance Request" inside the adapter.
- **Attachment Downloading**: Do not download the physical bytes of the attachment in the gateway. Persist the `storage_uri` for a downstream Attachment Processing Framework.
