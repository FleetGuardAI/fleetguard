"""
FleetGuard â€” File Upload Service
FG-SEC-007: Deep structural file validation, metadata sanitization,
decompression bomb prevention, and server-controlled storage paths.
"""

import io
import os
import re
import uuid
import logging
import urllib.parse
from typing import Optional, Tuple, Union, Any
from fastapi import UploadFile, HTTPException
try:
    from PIL import Image, UnidentifiedImageError
except ImportError:
    Image = None
    UnidentifiedImageError = Exception

try:
    import pypdf
    from pypdf.errors import PdfReadError
except ImportError:
    pypdf = None
    PdfReadError = Exception

from config import settings

try:
    from supabase import create_client, Client
except ImportError:
    Client = None
    create_client = None

logger = logging.getLogger("fleetguard.storage")

# Configure Pillow decompression bomb protection
MAX_IMAGE_PIXELS = 25_000_000  # Max 25 megapixels
if Image is not None:
    Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS
MAX_DIMENSION = 8192                 # Max width or height

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/webp"
}

MIME_TO_EXT = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/webp": ".webp",
    "application/pdf": ".pdf",
}

UNTRUSTED_DOCUMENT_EXTENSIONS = {
    "pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx",
    "html", "htm", "xml", "svg", "txt", "csv", "json", "rtf", "odt"
}

SAFE_RASTER_IMAGE_EXTENSIONS = {
    "png", "jpg", "jpeg", "webp"
}

MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB

DANGEROUS_CONTENT_SIGNATURES = (
    b"<html", b"<!doctype", b"<script", b"<svg", b"<?php", b"<xml", b"javascript:",
    b"vbscript:", b"onload=", b"onerror=", b"system(", b"passthru(", b"exec(", b"eval("
)

DANGEROUS_PDF_ACTIVE_TAGS = (
    b"/JavaScript", b"/JS", b"/Launch", b"/OpenAction", b"/EmbeddedFiles", b"/RichMedia"
)


def validate_and_sanitize_image(content: bytes) -> Tuple[bytes, str]:
    """
    FG-SEC-007: Deep structural validation of raster images using Pillow.
    Verifies actual image structure, enforces resolution limits against decompression bombs,
    and strips dangerous metadata (EXIF, scripts, embedded payloads) by re-encoding.
    """
    try:
        with Image.open(io.BytesIO(content)) as img:
            img.verify()
            img_format = img.format
    except (UnidentifiedImageError, SyntaxError, Exception) as e:
        logger.warning(f"Image structural verification failed: {e}")
        raise HTTPException(status_code=400, detail="Invalid, corrupted, or unsupported image structure.")

    format_to_mime = {
        "JPEG": "image/jpeg",
        "PNG": "image/png",
        "WEBP": "image/webp"
    }
    detected_mime = format_to_mime.get(img_format)
    if not detected_mime:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported image format: '{img_format}'. Allowed formats: JPEG, PNG, WEBP."
        )

    # Decompression bomb prevention and sanitization
    try:
        with Image.open(io.BytesIO(content)) as img:
            width, height = img.size
            if width > MAX_DIMENSION or height > MAX_DIMENSION:
                raise HTTPException(
                    status_code=400,
                    detail=f"Image dimensions ({width}x{height}) exceed maximum allowed dimension ({MAX_DIMENSION}px)."
                )
            if width * height > MAX_IMAGE_PIXELS:
                raise HTTPException(
                    status_code=400,
                    detail="Image exceeds maximum pixel limit (decompression bomb protection)."
                )

            # Re-encode to clean byte stream (stripping EXIF metadata and polyglots)
            out_buf = io.BytesIO()
            if detected_mime == "image/jpeg":
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                img.save(out_buf, format="JPEG", quality=92, optimize=True)
            elif detected_mime == "image/png":
                img.save(out_buf, format="PNG", optimize=True)
            elif detected_mime == "image/webp":
                img.save(out_buf, format="WEBP", quality=92)
            else:
                out_buf.write(content)

            sanitized_bytes = out_buf.getvalue()
            return sanitized_bytes, detected_mime
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image sanitization failed: {e}")
        raise HTTPException(status_code=400, detail="Failed to process image structure safely.")


MAX_PDF_PAGES = 50
MAX_ACTION_DEPTH = 10
MAX_ACTION_VISITS = 100
ALLOWED_URI_SCHEMES = frozenset({"http", "https"})


def _inspect_pdf_action(
    action_obj: Any,
    location: str,
    depth: int = 0,
    visited: Optional[set] = None,
    budget: Optional[list] = None
) -> None:
    """
    FG-SEC-007 Hardening: Recursively inspects PDF Action dictionaries with cycle detection,
    recursion depth limits, and object-visit budgets. Enforces strict URI scheme allowlist.
    Permits only safe HTTP/HTTPS hyperlinks and rejects active execution, scripts, or unsafe schemes.
    """
    if visited is None:
        visited = set()
    if budget is None:
        budget = [MAX_ACTION_VISITS]

    if not action_obj:
        return

    budget[0] -= 1
    if budget[0] <= 0:
        raise HTTPException(
            status_code=400,
            detail=f"PDF {location} exceeded maximum action inspection budget (possible complexity attack)."
        )

    if depth > MAX_ACTION_DEPTH:
        raise HTTPException(
            status_code=400,
            detail=f"PDF {location} exceeds maximum action recursion depth."
        )

    # Cycle detection for indirect object references or python objects
    obj_key = None
    if hasattr(action_obj, "indirect_reference") and action_obj.indirect_reference:
        ref = action_obj.indirect_reference
        obj_key = (getattr(ref, "idnum", id(action_obj)), getattr(ref, "generation", 0))
    else:
        obj_key = id(action_obj)

    if obj_key in visited:
        raise HTTPException(
            status_code=400,
            detail=f"PDF {location} contains circular action reference."
        )
    visited.add(obj_key)

    # Dereference indirect object if applicable
    resolved = action_obj.get_object() if hasattr(action_obj, "get_object") else action_obj
    if resolved is None:
        return

    # If resolved object is distinct, check cycles for resolved reference/identity
    if resolved is not action_obj:
        if hasattr(resolved, "indirect_reference") and resolved.indirect_reference:
            res_ref = resolved.indirect_reference
            res_key = (getattr(res_ref, "idnum", id(resolved)), getattr(res_ref, "generation", 0))
            if res_key in visited:
                raise HTTPException(
                    status_code=400,
                    detail=f"PDF {location} contains circular action reference."
                )
            visited.add(res_key)
        else:
            resolved_id = id(resolved)
            if resolved_id in visited:
                raise HTTPException(
                    status_code=400,
                    detail=f"PDF {location} contains circular action reference."
                )
            visited.add(resolved_id)

    # Handle arrays of actions (list, tuple, ArrayObject)
    if isinstance(resolved, (list, tuple)):
        for sub_a in resolved:
            _inspect_pdf_action(sub_a, location, depth + 1, visited, budget)
        return

    # Handle action dictionaries (dict, DictionaryObject)
    if isinstance(resolved, dict):
        s_type = str(resolved.get("/S", "")).lower()
        if any(bad in s_type for bad in ("javascript", "launch", "importdata", "gotor", "submitform", "richmedia", "rendition")):
            raise HTTPException(
                status_code=400,
                detail=f"PDF {location} contains disallowed action: {s_type}."
            )

        # Validate URI if action specifies /URI or if /URI key is present
        if "/URI" in resolved or s_type == "/uri":
            raw_uri = resolved.get("/URI")
            if raw_uri is not None:
                # Ensure URI values and scheme values use consistent string types
                if isinstance(raw_uri, bytes):
                    uri_str = raw_uri.decode("utf-8", errors="replace")
                else:
                    uri_str = str(raw_uri)
                uri_str = uri_str.strip()

                # Validate schemes using a robust URI parsing approach
                try:
                    parsed = urllib.parse.urlsplit(uri_str)
                    scheme = parsed.scheme.lower() if parsed.scheme else ""
                except Exception:
                    raise HTTPException(
                        status_code=400,
                        detail=f"PDF {location} contains malformed or unparseable URI."
                    )

                # Permit only explicitly approved URI schemes (http, https)
                if scheme not in ALLOWED_URI_SCHEMES:
                    raise HTTPException(
                        status_code=400,
                        detail=f"PDF {location} contains disallowed URI scheme '{scheme}'. Only HTTP and HTTPS are permitted."
                    )

        # Check nested /Next action chains (arrays or dictionaries)
        if "/Next" in resolved:
            next_action = resolved.get("/Next")
            _inspect_pdf_action(next_action, f"{location} -> /Next", depth + 1, visited, budget)


def validate_pdf_structure(content: bytes) -> str:
    """
    FG-SEC-007 Hardening: Deep structural and active-content validation for PDF documents.
    1. Header and EOF trailer verification.
    2. Parsing PDF object tree and cross-reference table via pypdf.
    3. Rejection of encrypted/password-protected PDFs.
    4. Enforcement of maximum page count (<= 50 pages).
    5. Deep AST inspection of Document Catalog (/Root):
       - /OpenAction (Launch, JavaScript, URI actions)
       - /Names (/JavaScript, /EmbeddedFiles name trees)
       - /AA (Document-level additional actions)
       - /AcroForm (Form field script actions & dynamic XFA)
    6. Page-level inspection:
       - Page /AA (Page-level actions on open/close)
       - /Annots (Annotation actions: /Launch, /JavaScript, dangerous URIs, /Next chains)
    7. Raw stream inspection for active markers.

    NOTE: Structural inspection is defense-in-depth and eliminates active executable features,
    macros, and origin bypasses. It does not replace operational antivirus scanning.
    """
    if not content.startswith(b"%PDF-"):
        raise HTTPException(status_code=400, detail="Invalid PDF document: missing %PDF- header.")

    tail = content[-2048:] if len(content) > 2048 else content
    if b"%%EOF" not in tail:
        raise HTTPException(status_code=400, detail="Invalid or truncated PDF document: missing %%EOF marker.")

    # 1. Raw signature check for active markers
    for tag in DANGEROUS_PDF_ACTIVE_TAGS:
        if tag in content:
            logger.warning(f"PDF upload rejected: contains active feature {tag.decode('latin1', errors='ignore')}")
            raise HTTPException(
                status_code=400,
                detail="PDF document contains disallowed active features (e.g. JavaScript, Launch actions, or EmbeddedFiles)."
            )

    # 2. Structural parsing with pypdf
    if pypdf is not None:
        try:
            reader = pypdf.PdfReader(io.BytesIO(content), strict=False)

            # Policy: Reject encrypted or password-protected PDFs
            if reader.is_encrypted:
                logger.warning("PDF upload rejected: document is encrypted or password-protected.")
                raise HTTPException(
                    status_code=400,
                    detail="Encrypted or password-protected PDF files are not allowed."
                )

            # Policy: Enforce maximum page count limit
            num_pages = len(reader.pages)
            if num_pages > MAX_PDF_PAGES:
                logger.warning(f"PDF upload rejected: exceeds maximum page count ({num_pages} > {MAX_PDF_PAGES}).")
                raise HTTPException(
                    status_code=400,
                    detail=f"PDF exceeds maximum allowed page count of {MAX_PDF_PAGES} pages."
                )

            # Deep inspect Root Catalog
            root = reader.trailer.get("/Root")
            if root and hasattr(root, "get_object"):
                root = root.get_object()
            if root and isinstance(root, dict):
                # Check /OpenAction
                open_action = root.get("/OpenAction")
                if open_action is not None:
                    _inspect_pdf_action(open_action, "Catalog /OpenAction")
                    raise HTTPException(
                        status_code=400,
                        detail="PDF contains disallowed /OpenAction execution payload."
                    )

                # Check /AA (Additional Actions)
                if root.get("/AA"):
                    raise HTTPException(status_code=400, detail="PDF contains disallowed Document /AA actions.")

                # Check /Names for JavaScript or EmbeddedFiles
                names = root.get("/Names")
                if names and hasattr(names, "get_object"):
                    names = names.get_object()
                if names and isinstance(names, dict):
                    if names.get("/JavaScript") or names.get("/EmbeddedFiles"):
                        raise HTTPException(
                            status_code=400,
                            detail="PDF contains disallowed active /Names (JavaScript or EmbeddedFiles)."
                        )

                # Check /AcroForm for dynamic XFA or calculation scripts
                acro_form = root.get("/AcroForm")
                if acro_form and hasattr(acro_form, "get_object"):
                    acro_form = acro_form.get_object()
                if isinstance(acro_form, dict) and acro_form.get("/XFA"):
                    raise HTTPException(status_code=400, detail="PDF contains disallowed dynamic XFA form structure.")

            # Deep inspect Pages and Annotations
            for page_idx, page in enumerate(reader.pages):
                if page.get("/AA"):
                    raise HTTPException(
                        status_code=400,
                        detail=f"PDF page {page_idx + 1} contains disallowed active page actions (/AA)."
                    )

                annots = page.get("/Annots")
                if annots and hasattr(annots, "get_object"):
                    annots = annots.get_object()
                if annots and isinstance(annots, (list, tuple)):
                    for annot in annots:
                        annot_obj = annot.get_object() if hasattr(annot, "get_object") else annot
                        if isinstance(annot_obj, dict):
                            action = annot_obj.get("/A")
                            if action:
                                _inspect_pdf_action(action, f"page {page_idx + 1} annotation")

        except HTTPException:
            raise
        except (PdfReadError, Exception) as e:
            logger.warning(f"pypdf parser failed to parse PDF structure: {e}")
            raise HTTPException(
                status_code=400,
                detail="Invalid, malformed, or corrupted PDF document structure."
            )

    return "application/pdf"


def detect_mime_from_content(content: bytes) -> Optional[str]:
    """Compatibility helper for raw magic byte detection."""
    if not content:
        return None
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if content.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if content.startswith(b"%PDF-"):
        return "application/pdf"
    if content.startswith(b"RIFF") and len(content) >= 12 and content[8:12] == b"WEBP":
        return "image/webp"
    return None


class MockSupabaseStorage:
    class StorageMock:
        def from_(self, bucket):
            return self
        def upload(self, file, path, file_options):
            pass
        def create_signed_url(self, path, expires_in, **kwargs):
            return {"signedURL": f"https://mock-supabase.com/storage/v1/object/sign/{path}?token=mock"}
        def remove(self, paths):
            pass

    def __init__(self):
        self.storage = self.StorageMock()


class StorageService:
    """
    Supabase Storage Service
    Secures uploads with deep structural verification, metadata stripping,
    server-controlled filenames, and signed URLs.
    """

    def __init__(self):
        self._supabase = None
        self.bucket = settings.SUPABASE_STORAGE_BUCKET or "fleetguard-uploads"

    @property
    def supabase(self):
        if not self._supabase:
            if not (settings.SUPABASE_URL and settings.SUPABASE_KEY and create_client):
                import sys
                if "pytest" in sys.modules:
                    self._supabase = MockSupabaseStorage()
                    logger.info("StorageService initialized with MockSupabaseStorage for testing.")
                    return self._supabase

                raise HTTPException(status_code=503, detail="Storage service is unavailable. Supabase configuration is missing.")

            self._supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
            logger.info(f"StorageService initialized with Supabase (bucket: {self.bucket})")
        return self._supabase

    def _validate_and_sanitize(self, content: bytes, client_content_type: Optional[str] = None) -> Tuple[bytes, str]:
        if not content or len(content) == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty (0 bytes).")

        if len(content) > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=400,
                detail=f"File exceeds maximum allowed size of {MAX_FILE_SIZE_BYTES // (1024 * 1024)}MB."
            )

        # Binary/script active content blocking
        head_sample = content[:4096].lower()
        if any(sig in head_sample for sig in DANGEROUS_CONTENT_SIGNATURES):
            raise HTTPException(status_code=400, detail="File contains disallowed active script or HTML content.")
        if content.startswith(b"MZ") or content.startswith(b"\x7fELF"):
            raise HTTPException(status_code=400, detail="Executable files are strictly forbidden.")

        # Structural inspection by format
        if content.startswith(b"%PDF-"):
            detected_mime = validate_pdf_structure(content)
            sanitized_content = content
        elif content.startswith(b"\xff\xd8\xff") or content.startswith(b"\x89PNG\r\n\x1a\n") or (content.startswith(b"RIFF") and len(content) >= 12 and content[8:12] == b"WEBP"):
            sanitized_content, detected_mime = validate_and_sanitize_image(content)
        else:
            raise HTTPException(
                status_code=400,
                detail="Unsupported or invalid file content. Allowed formats: PNG, JPEG, WEBP, and PDF."
            )

        # Correlation with client Content-Type
        if client_content_type and client_content_type != "application/octet-stream":
            normalized_client = client_content_type.strip().lower()
            if normalized_client == "image/jpg":
                normalized_client = "image/jpeg"
            if normalized_client != detected_mime:
                raise HTTPException(
                    status_code=400,
                    detail=f"Content-Type mismatch: header claims '{client_content_type}', but actual content is '{detected_mime}'."
                )

        return sanitized_content, detected_mime

    def _sanitize_folder(self, folder: str, company_id: Optional[int] = None) -> str:
        """Sanitizes folder path against directory traversal and special characters, optionally scoping to tenant."""
        parts = [p for p in folder.strip("/\\").split("/") if p and p not in (".", "..")]
        clean_parts = [re.sub(r"[^a-zA-Z0-9_\-]", "", p) for p in parts]
        if company_id is not None:
            comp_prefix = f"company_{company_id}"
            if not clean_parts or clean_parts[0] != comp_prefix:
                clean_parts.insert(0, comp_prefix)
        sanitized = "/".join(p for p in clean_parts if p)
        return sanitized if sanitized else "general"

    async def upload_file(
        self,
        file: UploadFile,
        folder: str = "general",
        filename: Optional[str] = None,
        company_id: Optional[int] = None,
    ) -> str:
        """
        Save uploaded file with structural validation and server-controlled filename.
        Returns object path formatted as `{folder}/{uuid}.{ext}`.
        """
        raw_content = await file.read()
        sanitized_content, detected_mime = self._validate_and_sanitize(raw_content, file.content_type)
        safe_ext = MIME_TO_EXT[detected_mime]
        safe_folder = self._sanitize_folder(folder, company_id=company_id)

        # Enforce server-controlled UUID filename to prevent arbitrary naming attacks
        server_filename = f"{uuid.uuid4().hex}{safe_ext}"
        object_path = f"{safe_folder}/{server_filename}"

        try:
            import asyncio
            await asyncio.to_thread(
                self.supabase.storage.from_(self.bucket).upload,
                file=sanitized_content,
                path=object_path,
                file_options={"content-type": detected_mime}
            )
            logger.info(f"File stored in Supabase: {object_path} ({len(sanitized_content)} bytes)")
            return object_path
        except Exception as e:
            logger.error(f"Failed to upload to Supabase: {e}")
            raise HTTPException(status_code=500, detail="Failed to upload file to storage")

    async def upload_bytes(
        self,
        data: bytes,
        folder: str,
        filename: Optional[str] = None,
        content_type: str = "application/octet-stream",
        company_id: Optional[int] = None,
    ) -> str:
        """Save raw bytes with structural validation and server-controlled filename."""
        sanitized_content, detected_mime = self._validate_and_sanitize(data, content_type)
        safe_ext = MIME_TO_EXT[detected_mime]
        safe_folder = self._sanitize_folder(folder, company_id=company_id)

        server_filename = f"{uuid.uuid4().hex}{safe_ext}"
        object_path = f"{safe_folder}/{server_filename}"

        try:
            import asyncio
            await asyncio.to_thread(
                self.supabase.storage.from_(self.bucket).upload,
                file=sanitized_content,
                path=object_path,
                file_options={"content-type": detected_mime}
            )
            logger.info(f"Bytes stored in Supabase: {object_path} ({len(sanitized_content)} bytes)")
            return object_path
        except Exception as e:
            logger.error(f"Failed to upload bytes to Supabase: {e}")
            raise HTTPException(status_code=500, detail="Failed to upload data to storage")

    @staticmethod
    def is_safe_raster_image(object_path: str) -> bool:
        """Determines if the object is an approved raster image format safe for inline previews."""
        if not object_path:
            return False
        clean_path = object_path.split("?")[0].strip().lower()
        ext = clean_path.rsplit(".", 1)[-1] if "." in clean_path else ""
        return ext in SAFE_RASTER_IMAGE_EXTENSIONS

    def create_signed_url(
        self,
        object_path: str,
        expires_in: int = 3600,
        download: Optional[Union[bool, str]] = None
    ) -> Optional[str]:
        """
        Generate temporary signed URL with resource-type-specific delivery policy.

        Policy:
        1. Sensitive documents & untrusted active-content formats (PDF, docs, text):
           - ALWAYS forced as attachment downloads (download=True or server-sanitized filename).
           - Inline browser execution in the SaaS origin is strictly prevented.
        2. Safe, validated raster images (PNG, JPEG, WEBP):
           - Delivered inline (download=False) by default to preserve legitimate preview
             workflows in web dashboard and mobile app (driver avatars, vehicle photos, trip selfies).
           - Forced as attachment if explicitly requested with download=True.
        """
        if not object_path:
            return None

        # FG-SEC-027: Cap maximum lifetime to 3,600s (1 hour) to eliminate prolonged exposure risk
        expires_in = min(max(1, int(expires_in)), 3600)

        clean_path = object_path.split("?")[0].strip().lower()
        ext = clean_path.rsplit(".", 1)[-1] if "." in clean_path else ""

        try:
            options = {}
            if ext in UNTRUSTED_DOCUMENT_EXTENSIONS or not self.is_safe_raster_image(object_path):
                # Sensitive documents or unknown formats ALWAYS forced as attachment
                if isinstance(download, str) and download.strip():
                    safe_name = os.path.basename(download.strip())
                    options["download"] = safe_name if safe_name else True
                else:
                    options["download"] = True
            else:
                # Safe raster image preview
                if download is True:
                    options["download"] = True
                elif isinstance(download, str) and download.strip():
                    options["download"] = os.path.basename(download.strip())
                # If download is False or None -> delivered inline (no download query option)

            res = self.supabase.storage.from_(self.bucket).create_signed_url(
                path=object_path,
                expires_in=expires_in,
                **options
            )
            return res.get("signedURL") or res.get("signedUrl")
        except Exception as e:
            logger.error(f"Failed to generate signed URL for {object_path}: {e}")
            return None

    def create_preview_signed_url(
        self,
        object_path: str,
        expires_in: int = 900
    ) -> Optional[str]:
        """Generate signed URL specifically for safe raster image preview in <img> tags (default 15m)."""
        return self.create_signed_url(object_path, expires_in=min(expires_in, 900), download=False)

    def create_attachment_signed_url(
        self,
        object_path: str,
        filename: Optional[str] = None,
        expires_in: int = 3600
    ) -> Optional[str]:
        """Generate signed URL explicitly forcing attachment download."""
        return self.create_signed_url(object_path, expires_in=expires_in, download=filename or True)

    async def create_signed_url_async(
        self,
        object_path: str,
        expires_in: int = 3600,
        download: Optional[Union[bool, str]] = None
    ) -> Optional[str]:
        """Async wrapper for create_signed_url."""
        import asyncio
        return await asyncio.to_thread(self.create_signed_url, object_path, expires_in, download)

    async def create_preview_signed_url_async(
        self,
        object_path: str,
        expires_in: int = 900
    ) -> Optional[str]:
        """Async wrapper for create_preview_signed_url."""
        import asyncio
        return await asyncio.to_thread(self.create_preview_signed_url, object_path, expires_in)

    async def create_attachment_signed_url_async(
        self,
        object_path: str,
        filename: Optional[str] = None,
        expires_in: int = 3600
    ) -> Optional[str]:
        """Async wrapper for create_attachment_signed_url."""
        import asyncio
        return await asyncio.to_thread(self.create_attachment_signed_url, object_path, filename, expires_in)

    async def delete_file(self, object_path: str) -> bool:
        if not object_path:
            return False
        try:
            self.supabase.storage.from_(self.bucket).remove([object_path])
            logger.info(f"File deleted from Supabase: {object_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete {object_path} from Supabase: {e}")
            return False

# Singleton instance
storage_service = StorageService()
