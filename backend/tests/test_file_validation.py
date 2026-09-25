"""Tests for app.services.file_validation"""

import io
import zipfile

import pytest

from app.services.file_validation import (
    MAX_FILE_SIZE_BYTES,
    FileValidationError,
    validate_upload,
)


def _make_minimal_docx_bytes() -> bytes:
    """
    A minimal but STRUCTURALLY VALID docx: a real ZIP archive containing
    the one entry our validator specifically checks for. Not a fully
    spec-compliant Word document (missing several other required parts
    a real docx has), but enough to prove our validator is actually
    inspecting ZIP contents, not just checking magic bytes.
    """
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("word/document.xml", "<xml>fake but present</xml>")
        archive.writestr("[Content_Types].xml", "<Types/>")
    return buffer.getvalue()


def _make_plain_zip_bytes() -> bytes:
    """A real ZIP file, but with no docx-specific internal structure."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("readme.txt", "just a normal zip, not a docx")
    return buffer.getvalue()


def _make_minimal_pdf_bytes() -> bytes:
    return b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n1 0 obj\n<< >>\nendobj\ntrailer\n<< >>\n%%EOF"


# --- Extension checks ---


def test_rejects_unsupported_extension():
    with pytest.raises(FileValidationError, match="not supported"):
        validate_upload("malware.exe", b"anything")


def test_rejects_filename_with_no_extension():
    with pytest.raises(FileValidationError, match="not supported"):
        validate_upload("noextension", b"anything")


def test_extension_check_is_case_insensitive():
    content = _make_minimal_pdf_bytes()
    assert validate_upload("Document.PDF", content) == "pdf"


# --- Size checks ---


def test_rejects_empty_file():
    with pytest.raises(FileValidationError, match="empty"):
        validate_upload("notes.txt", b"")


def test_rejects_oversized_file():
    oversized_content = b"a" * (MAX_FILE_SIZE_BYTES + 1)
    with pytest.raises(FileValidationError, match="exceeds the maximum"):
        validate_upload("notes.txt", oversized_content)


def test_accepts_file_at_exact_size_limit():
    content = b"a" * MAX_FILE_SIZE_BYTES
    assert validate_upload("notes.txt", content) == "txt"


# --- PDF validation ---


def test_accepts_valid_pdf():
    assert validate_upload("notes.pdf", _make_minimal_pdf_bytes()) == "pdf"


def test_rejects_spoofed_pdf_extension():
    # The actual attack this whole phase exists to prevent: a non-PDF
    # file renamed to claim it's a PDF.
    fake_pdf = b"This is just plain text, not a real PDF."
    with pytest.raises(FileValidationError, match="not a valid PDF"):
        validate_upload("fake.pdf", fake_pdf)


# --- DOCX validation ---


def test_accepts_valid_docx():
    assert validate_upload("report.docx", _make_minimal_docx_bytes()) == "docx"


def test_rejects_plain_zip_renamed_to_docx():
    # A real ZIP file (valid magic bytes!) but with no Word-specific
    # internal structure — proves we check INSIDE the archive, not just
    # its magic bytes.
    with pytest.raises(FileValidationError, match="not a valid Word document"):
        validate_upload("fake.docx", _make_plain_zip_bytes())


def test_rejects_non_zip_content_claiming_to_be_docx():
    with pytest.raises(FileValidationError, match="not a valid ZIP/DOCX"):
        validate_upload("fake.docx", b"not a zip file at all")


def test_rejects_corrupted_zip_claiming_to_be_docx():
    # Starts with valid ZIP magic bytes but is truncated/corrupted.
    corrupted = b"PK\x03\x04" + b"garbage" * 5
    with pytest.raises(FileValidationError, match="not a valid ZIP/DOCX"):
        validate_upload("fake.docx", corrupted)


# --- TXT / MD validation ---


def test_accepts_valid_utf8_txt():
    assert validate_upload("notes.txt", "Congestion control notes".encode("utf-8")) == "txt"


def test_accepts_valid_utf8_md():
    assert validate_upload("notes.md", "# Heading\n\nSome notes.".encode("utf-8")) == "md"


def test_accepts_unicode_text_content():
    content = "Café notes on résumés — normalisation".encode("utf-8")
    assert validate_upload("notes.txt", content) == "txt"


def test_rejects_binary_content_disguised_as_txt():
    binary_content = b"\x00\x01\x02\xff\xfe\xfd"
    with pytest.raises(FileValidationError, match="binary data"):
        validate_upload("fake.txt", binary_content)


def test_rejects_invalid_utf8_disguised_as_txt():
    # \xff is never a valid UTF-8 leading byte. Deliberately no null
    # bytes here, so this actually exercises the UTF-8 decode check
    # specifically, not the null-byte check above it.
    invalid_utf8 = b"\xff\xfe invalid utf8 text with no null bytes"
    with pytest.raises(FileValidationError, match="not valid UTF-8"):
        validate_upload("fake.txt", invalid_utf8)


def test_returns_correct_kind_for_each_type():
    assert validate_upload("a.pdf", _make_minimal_pdf_bytes()) == "pdf"
    assert validate_upload("a.docx", _make_minimal_docx_bytes()) == "docx"
    assert validate_upload("a.txt", b"hello") == "txt"
    assert validate_upload("a.md", b"# hello") == "md"