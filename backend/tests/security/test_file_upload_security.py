import pytest
import io
from PIL import Image
from pypdf import PdfWriter
from fastapi import UploadFile, HTTPException
from services.file_upload_service import storage_service, validate_pdf_structure, MAX_DIMENSION, MAX_PDF_PAGES


def make_valid_png() -> bytes:
    buf = io.BytesIO()
    img = Image.new("RGB", (50, 50), color="blue")
    img.save(buf, format="PNG")
    return buf.getvalue()


def make_valid_jpeg() -> bytes:
    buf = io.BytesIO()
    img = Image.new("RGB", (50, 50), color="red")
    img.save(buf, format="JPEG")
    return buf.getvalue()


def make_valid_pdf() -> bytes:
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


@pytest.mark.asyncio
async def test_valid_file_uploads_accepted():
    """FG-SEC-007: Structurally valid PNG, JPEG, and PDF files are accepted."""
    # PNG
    png_content = make_valid_png()
    png_file = UploadFile(filename="photo.png", file=io.BytesIO(png_content), headers={"content-type": "image/png"})
    path_png = await storage_service.upload_file(png_file, folder="test")
    assert path_png.endswith(".png")
    assert ".." not in path_png
    assert path_png.startswith("test/")

    # JPEG
    jpeg_content = make_valid_jpeg()
    jpeg_file = UploadFile(filename="photo.jpg", file=io.BytesIO(jpeg_content), headers={"content-type": "image/jpeg"})
    path_jpeg = await storage_service.upload_file(jpeg_file, folder="test")
    assert path_jpeg.endswith(".jpg")

    # PDF
    pdf_content = make_valid_pdf()
    pdf_file = UploadFile(filename="document.pdf", file=io.BytesIO(pdf_content), headers={"content-type": "application/pdf"})
    path_pdf = await storage_service.upload_file(pdf_file, folder="test")
    assert path_pdf.endswith(".pdf")


@pytest.mark.asyncio
async def test_html_disguised_as_image_rejected():
    """FG-SEC-007: HTML payload with image MIME type header is detected and rejected."""
    html_content = b"<!DOCTYPE html><html><body><script>alert('XSS')</script></body></html>"
    malicious_file = UploadFile(
        filename="exploit.jpg",
        file=io.BytesIO(html_content),
        headers={"content-type": "image/jpeg"}
    )
    with pytest.raises(HTTPException) as exc_info:
        await storage_service.upload_file(malicious_file, folder="avatars")
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_svg_payload_rejected():
    """FG-SEC-007: SVG files (common vector for stored XSS) are rejected."""
    svg_content = b"<svg xmlns='http://www.w3.org/2000/svg'><script>alert(1)</script></svg>"
    svg_file = UploadFile(
        filename="vector.svg",
        file=io.BytesIO(svg_content),
        headers={"content-type": "image/svg+xml"}
    )
    with pytest.raises(HTTPException) as exc_info:
        await storage_service.upload_file(svg_file, folder="logos")
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_empty_file_rejected():
    """FG-SEC-007: 0-byte empty file is rejected."""
    empty_file = UploadFile(
        filename="empty.png",
        file=io.BytesIO(b""),
        headers={"content-type": "image/png"}
    )
    with pytest.raises(HTTPException) as exc_info:
        await storage_service.upload_file(empty_file, folder="docs")
    assert exc_info.value.status_code == 400
    assert "empty" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_content_type_mismatch_rejected():
    """FG-SEC-007: Content-Type header that contradicts detected magic bytes is rejected."""
    png_content = make_valid_png()
    mismatched_file = UploadFile(
        filename="photo.pdf",
        file=io.BytesIO(png_content),
        headers={"content-type": "application/pdf"}  # Header says PDF, content is PNG
    )
    with pytest.raises(HTTPException) as exc_info:
        await storage_service.upload_file(mismatched_file, folder="docs")
    assert exc_info.value.status_code == 400
    assert "mismatch" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_path_traversal_sanitized():
    """FG-SEC-007: Path traversal in folder and filename is stripped and neutralized."""
    png_content = make_valid_png()
    traversal_file = UploadFile(
        filename="../../var/www/malicious.php",
        file=io.BytesIO(png_content),
        headers={"content-type": "image/png"}
    )
    path = await storage_service.upload_file(traversal_file, folder="../../../etc/passwd")
    assert ".." not in path
    assert not path.startswith("/")
    assert path.endswith(".png")


@pytest.mark.asyncio
async def test_pdf_active_content_rejected():
    """FG-SEC-007: PDF documents containing embedded JavaScript or launch actions are rejected."""
    malicious_pdf = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /OpenAction << /S /JavaScript /JS (app.alert('XSS')) >> >>\nendobj\ntrailer\n<< >>\n%%EOF"
    pdf_file = UploadFile(
        filename="invoice.pdf",
        file=io.BytesIO(malicious_pdf),
        headers={"content-type": "application/pdf"}
    )
    with pytest.raises(HTTPException) as exc_info:
        await storage_service.upload_file(pdf_file, folder="invoices")
    assert exc_info.value.status_code == 400
    assert "active features" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_pdf_truncated_eof_rejected():
    """FG-SEC-007: PDF without valid %%EOF trailer is rejected."""
    truncated_pdf = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n"
    pdf_file = UploadFile(
        filename="corrupted.pdf",
        file=io.BytesIO(truncated_pdf),
        headers={"content-type": "application/pdf"}
    )
    with pytest.raises(HTTPException) as exc_info:
        await storage_service.upload_file(pdf_file, folder="docs")
    assert exc_info.value.status_code == 400
    assert "eof" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_corrupted_image_rejected():
    """FG-SEC-007: Fake magic bytes with corrupted image data are rejected by Pillow."""
    corrupted_bytes = b"\xff\xd8\xff\xe0" + b"CORRUPTED_GARBAGE_PAYLOAD" * 10
    corrupt_file = UploadFile(
        filename="corrupt.jpg",
        file=io.BytesIO(corrupted_bytes),
        headers={"content-type": "image/jpeg"}
    )
    with pytest.raises(HTTPException) as exc_info:
        await storage_service.upload_file(corrupt_file, folder="avatars")
    assert exc_info.value.status_code == 400


def make_multipage_pdf(num_pages: int) -> bytes:
    writer = PdfWriter()
    for _ in range(num_pages):
        writer.add_blank_page(width=72, height=72)
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


def make_encrypted_pdf() -> bytes:
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    writer.encrypt("secure_password_123")
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


@pytest.mark.asyncio
async def test_pdf_page_limit_enforced():
    """FG-SEC-007 (Batch 1.2): PDF documents exceeding MAX_PDF_PAGES (50) are rejected."""
    excessive_pdf = make_multipage_pdf(51)
    file = UploadFile(
        filename="huge_manual.pdf",
        file=io.BytesIO(excessive_pdf),
        headers={"content-type": "application/pdf"}
    )
    with pytest.raises(HTTPException) as exc_info:
        await storage_service.upload_file(file, folder="manuals")
    assert exc_info.value.status_code == 400
    assert "maximum allowed page count" in exc_info.value.detail


@pytest.mark.asyncio
async def test_pdf_encrypted_rejected():
    """FG-SEC-007 (Batch 1.2): Encrypted or password-protected PDFs are rejected."""
    encrypted_pdf = make_encrypted_pdf()
    file = UploadFile(
        filename="secret.pdf",
        file=io.BytesIO(encrypted_pdf),
        headers={"content-type": "application/pdf"}
    )
    with pytest.raises(HTTPException) as exc_info:
        await storage_service.upload_file(file, folder="docs")
    assert exc_info.value.status_code == 400
    assert "encrypted or password-protected" in exc_info.value.detail.lower()


def test_pdf_malformed_structure_rejected():
    """FG-SEC-007 (Batch 1.2): Invalid or corrupt PDF internal structures raise 400."""
    corrupted_pdf = b"%PDF-1.4\n1 0 obj\nINVALID SYNTAX MISSING OBJECT BODY\n%%EOF"
    with pytest.raises(HTTPException) as exc_info:
        validate_pdf_structure(corrupted_pdf)
    assert exc_info.value.status_code == 400
    assert "malformed" in exc_info.value.detail.lower() or "invalid" in exc_info.value.detail.lower()


from pypdf.generic import DictionaryObject, NameObject, TextStringObject, ArrayObject, NumberObject

def test_signed_url_resource_type_policies(monkeypatch):
    """
    FG-SEC-007 (Batch 1.3): Signed URL delivery policies:
    1. Raster images (driver avatar, vehicle photo, trip selfie) deliver INLINE (download=False).
    2. Sensitive documents / PDFs ALWAYS force attachment download, even if download=False requested.
    3. Explicit helper methods produce intended behavior.
    """
    captured_options = {}

    class DummyBucket:
        def create_signed_url(self, path, expires_in, **kwargs):
            captured_options[path] = kwargs
            dl_flag = kwargs.get("download")
            dl_query = f"?download={dl_flag}" if dl_flag else ""
            return {"signedURL": f"https://storage.fleetguard.com/{path}{dl_query}"}

    class DummyStorage:
        def from_(self, bucket):
            return DummyBucket()

    class DummyClient:
        storage = DummyStorage()

    monkeypatch.setattr(storage_service, "_supabase", DummyClient())
    monkeypatch.setattr(storage_service, "bucket", "fleetguard-uploads")

    # 1. Driver avatar (JPG) -> Delivered inline for <img> tag preview
    url_avatar = storage_service.create_signed_url("drivers/24/avatar.jpg")
    assert url_avatar is not None
    assert "download" not in captured_options["drivers/24/avatar.jpg"]

    # 2. Vehicle photo (PNG) -> Delivered inline
    url_veh = storage_service.create_signed_url("vehicles/MH12AB1234/front.png")
    assert url_veh is not None
    assert "download" not in captured_options["vehicles/MH12AB1234/front.png"]

    # 3. Trip selfie (WEBP) -> Delivered inline
    url_selfie = storage_service.create_signed_url("trips/19/selfies/driver.webp")
    assert url_selfie is not None
    assert "download" not in captured_options["trips/19/selfies/driver.webp"]

    # 4. Driver KYC license (PDF) -> Forced attachment download (download=True)
    url_license = storage_service.create_signed_url("drivers/24/license.pdf")
    assert url_license is not None
    assert captured_options["drivers/24/license.pdf"].get("download") is True

    # 5. Untrusted PDF called with download=False -> Policy still forces download=True (anti-bypass)
    url_bypass_attempt = storage_service.create_signed_url("invoices/inv_99.pdf", download=False)
    assert url_bypass_attempt is not None
    assert captured_options["invoices/inv_99.pdf"].get("download") is True

    # 6. Explicit preview helper vs attachment helper
    storage_service.create_preview_signed_url("drivers/photo.png")
    assert "download" not in captured_options["drivers/photo.png"]

    storage_service.create_attachment_signed_url("reports/summary.pdf", filename="annual_summary.pdf")
    assert captured_options["reports/summary.pdf"].get("download") == "annual_summary.pdf"


def test_adversarial_pdf_catalog_additional_actions_rejected():
    """FG-SEC-007 (Batch 1.3): Catalog /AA (additional actions) rejected."""
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    aa_dict = DictionaryObject({
        NameObject("/O"): DictionaryObject({NameObject("/S"): NameObject("/JavaScript")})
    })
    writer._root_object[NameObject("/AA")] = aa_dict
    buf = io.BytesIO()
    writer.write(buf)

    with pytest.raises(HTTPException) as exc_info:
        validate_pdf_structure(buf.getvalue())
    assert exc_info.value.status_code == 400
    assert any(w in exc_info.value.detail.lower() for w in ["aa actions", "disallowed active features", "javascript"])


def test_adversarial_pdf_page_additional_actions_rejected():
    """FG-SEC-007 (Batch 1.3): Page-level /AA actions rejected."""
    writer = PdfWriter()
    page = writer.add_blank_page(width=72, height=72)
    page[NameObject("/AA")] = DictionaryObject({
        NameObject("/O"): DictionaryObject({NameObject("/S"): NameObject("/JavaScript")})
    })
    buf = io.BytesIO()
    writer.write(buf)

    with pytest.raises(HTTPException) as exc_info:
        validate_pdf_structure(buf.getvalue())
    assert exc_info.value.status_code == 400
    assert any(w in exc_info.value.detail.lower() for w in ["active page actions", "disallowed active features", "javascript"])


def test_adversarial_pdf_javascript_names_tree_rejected():
    """FG-SEC-007 (Batch 1.3): Catalog /Names -> /JavaScript tree rejected."""
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    writer._root_object[NameObject("/Names")] = DictionaryObject({
        NameObject("/JavaScript"): DictionaryObject()
    })
    buf = io.BytesIO()
    writer.write(buf)

    with pytest.raises(HTTPException) as exc_info:
        validate_pdf_structure(buf.getvalue())
    assert exc_info.value.status_code == 400
    assert any(w in exc_info.value.detail.lower() for w in ["names", "disallowed active features", "javascript"])


def test_adversarial_pdf_embedded_files_tree_rejected():
    """FG-SEC-007 (Batch 1.3): Catalog /Names -> /EmbeddedFiles tree rejected."""
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    writer._root_object[NameObject("/Names")] = DictionaryObject({
        NameObject("/EmbeddedFiles"): DictionaryObject()
    })
    buf = io.BytesIO()
    writer.write(buf)

    with pytest.raises(HTTPException) as exc_info:
        validate_pdf_structure(buf.getvalue())
    assert exc_info.value.status_code == 400
    assert any(w in exc_info.value.detail.lower() for w in ["embeddedfiles", "disallowed active features", "names"])


def test_adversarial_pdf_nested_next_action_rejected():
    """FG-SEC-007 (Batch 1.3): Nested /Next action chains (/URI -> /Next /Launch) rejected."""
    writer = PdfWriter()
    page = writer.add_blank_page(width=72, height=72)
    action1 = DictionaryObject({
        NameObject("/S"): NameObject("/URI"),
        NameObject("/URI"): TextStringObject("https://fleetguard.com")
    })
    action2 = DictionaryObject({
        NameObject("/S"): NameObject("/Launch"),
        NameObject("/F"): TextStringObject("payload.exe")
    })
    action1[NameObject("/Next")] = action2
    annot = DictionaryObject({
        NameObject("/Type"): NameObject("/Annot"),
        NameObject("/Subtype"): NameObject("/Link"),
        NameObject("/Rect"): ArrayObject([NumberObject(0), NumberObject(0), NumberObject(72), NumberObject(72)]),
        NameObject("/A"): action1
    })
    page[NameObject("/Annots")] = ArrayObject([annot])
    buf = io.BytesIO()
    writer.write(buf)

    with pytest.raises(HTTPException) as exc_info:
        validate_pdf_structure(buf.getvalue())
    assert exc_info.value.status_code == 400
    assert any(w in exc_info.value.detail.lower() for w in ["disallowed action", "launch", "disallowed active features"])


def test_adversarial_pdf_unsafe_uri_scheme_rejected():
    """FG-SEC-007 (Batch 1.3 & 1.4): Annotation /URI with javascript: scheme rejected."""
    writer = PdfWriter()
    page = writer.add_blank_page(width=72, height=72)
    annot = DictionaryObject({
        NameObject("/Type"): NameObject("/Annot"),
        NameObject("/Subtype"): NameObject("/Link"),
        NameObject("/Rect"): ArrayObject([NumberObject(0), NumberObject(0), NumberObject(72), NumberObject(72)]),
        NameObject("/A"): DictionaryObject({
            NameObject("/S"): NameObject("/URI"),
            NameObject("/URI"): TextStringObject("javascript:alert(document.cookie)")
        })
    })
    page[NameObject("/Annots")] = ArrayObject([annot])
    buf = io.BytesIO()
    writer.write(buf)

    with pytest.raises(HTTPException) as exc_info:
        validate_pdf_structure(buf.getvalue())
    assert exc_info.value.status_code == 400
    assert any(w in exc_info.value.detail.lower() for w in ["unsafe uri scheme", "disallowed uri scheme", "disallowed active features", "javascript"])


def test_adversarial_pdf_dynamic_xfa_form_rejected():
    """FG-SEC-007 (Batch 1.3): AcroForm /XFA dynamic XML form structure rejected."""
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    writer._root_object[NameObject("/AcroForm")] = DictionaryObject({
        NameObject("/XFA"): TextStringObject("<xdp>dynamic form</xdp>")
    })
    buf = io.BytesIO()
    writer.write(buf)

    with pytest.raises(HTTPException) as exc_info:
        validate_pdf_structure(buf.getvalue())
    assert exc_info.value.status_code == 400
    assert "xfa form" in exc_info.value.detail.lower()


def test_benign_pdf_with_safe_https_link_accepted():
    """
    FG-SEC-007 (Batch 1.4): Standard benign PDF with safe HTTPS hyperlinks
    must NOT be rejected. Legitimate invoice/documentation links remain functional.
    """
    writer = PdfWriter()
    page = writer.add_blank_page(width=72, height=72)
    annot = DictionaryObject({
        NameObject("/Type"): NameObject("/Annot"),
        NameObject("/Subtype"): NameObject("/Link"),
        NameObject("/Rect"): ArrayObject([NumberObject(0), NumberObject(0), NumberObject(72), NumberObject(72)]),
        NameObject("/A"): DictionaryObject({
            NameObject("/S"): NameObject("/URI"),
            NameObject("/URI"): TextStringObject("https://fleetguard.com/invoices/2026/01")
        })
    })
    page[NameObject("/Annots")] = ArrayObject([annot])
    buf = io.BytesIO()
    writer.write(buf)

    detected_mime = validate_pdf_structure(buf.getvalue())
    assert detected_mime == "application/pdf"


def test_adversarial_pdf_disallowed_schemes_rejected():
    """FG-SEC-007 (Batch 1.4): Schemes such as file:, data:, and blob: must be rejected."""
    for bad_scheme in ["file:///etc/passwd", "data:text/html;base64,PHNjcmlwdD5hbGVydCgxKTwvc2NyaXB0Pg==", "blob:https://evil.com/123"]:
        writer = PdfWriter()
        page = writer.add_blank_page(width=72, height=72)
        annot = DictionaryObject({
            NameObject("/Type"): NameObject("/Annot"),
            NameObject("/Subtype"): NameObject("/Link"),
            NameObject("/Rect"): ArrayObject([NumberObject(0), NumberObject(0), NumberObject(72), NumberObject(72)]),
            NameObject("/A"): DictionaryObject({
                NameObject("/S"): NameObject("/URI"),
                NameObject("/URI"): TextStringObject(bad_scheme)
            })
        })
        page[NameObject("/Annots")] = ArrayObject([annot])
        buf = io.BytesIO()
        writer.write(buf)

        with pytest.raises(HTTPException) as exc_info:
            validate_pdf_structure(buf.getvalue())
        assert exc_info.value.status_code == 400
        assert any(w in exc_info.value.detail.lower() for w in ["disallowed uri scheme", "unsafe uri scheme", "disallowed active features"])


def test_adversarial_pdf_circular_action_reference_rejected():
    """FG-SEC-007 (Batch 1.4): Circular action references must be caught by cycle detection."""
    from services.file_upload_service import _inspect_pdf_action
    action1 = {
        "/S": "/URI",
        "/URI": "https://example.com"
    }
    # Create circular reference
    action1["/Next"] = action1

    with pytest.raises(HTTPException) as exc_info:
        _inspect_pdf_action(action1, "test circular action")
    assert exc_info.value.status_code == 400
    assert "circular action reference" in exc_info.value.detail.lower()


def test_adversarial_pdf_recursion_depth_rejected():
    """FG-SEC-007 (Batch 1.4): Excessively deep action nesting must be rejected."""
    from services.file_upload_service import _inspect_pdf_action
    # Build deep chain of 15 /Next actions
    root_action = {"/S": "/URI", "/URI": "https://example.com"}
    curr = root_action
    for i in range(15):
        next_act = {"/S": "/URI", "/URI": f"https://example.com/step/{i}"}
        curr["/Next"] = next_act
        curr = next_act

    with pytest.raises(HTTPException) as exc_info:
        _inspect_pdf_action(root_action, "test deep action")
    assert exc_info.value.status_code == 400
    assert any(w in exc_info.value.detail.lower() for w in ["recursion depth", "maximum action"])
