"""
Tests for app.services.extraction — one extractor per file type, plus
the extract_text() dispatcher.

Uses REAL generated fixtures (a real PDF via reportlab, a real DOCX via
python-docx's own writer) rather than hand-crafted byte strings, so
these tests exercise the actual parsing libraries against real files,
not just our own assumptions about their format.
"""

import io

import docx
import pytest
from reportlab.pdfgen import canvas

from app.services.extraction.extraction_service import ExtractionError, extract_text


def _make_pdf_with_text(text: str) -> bytes:
    buffer = io.BytesIO()
    pdf_canvas = canvas.Canvas(buffer)
    pdf_canvas.drawString(100, 750, text)
    pdf_canvas.save()
    return buffer.getvalue()


def _make_empty_pdf() -> bytes:
    buffer = io.BytesIO()
    pdf_canvas = canvas.Canvas(buffer)
    pdf_canvas.showPage()  # a blank page, no text drawn at all
    pdf_canvas.save()
    return buffer.getvalue()


def _make_docx_with_paragraphs(paragraphs: list[str]) -> bytes:
    document = docx.Document()
    for paragraph_text in paragraphs:
        document.add_paragraph(paragraph_text)
    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()


# --- PDF extraction ---


def test_extracts_text_from_real_pdf():
    pdf_bytes = _make_pdf_with_text("Congestion control notes for networking class")
    text = extract_text("pdf", pdf_bytes)
    assert "Congestion control notes" in text


def test_pdf_with_no_text_layer_raises_extraction_error():
    empty_pdf = _make_empty_pdf()
    with pytest.raises(ExtractionError, match="No extractable text"):
        extract_text("pdf", empty_pdf)


def test_corrupt_pdf_raises_extraction_error():
    with pytest.raises(ExtractionError, match="Failed to extract text"):
        extract_text("pdf", b"%PDF-1.4\nthis is not actually a valid pdf structure")


# --- DOCX extraction ---


def test_extracts_text_from_real_docx():
    docx_bytes = _make_docx_with_paragraphs(
        ["Database Normalization", "Reduces redundancy in relational schemas."]
    )
    text = extract_text("docx", docx_bytes)
    assert "Database Normalization" in text
    assert "Reduces redundancy" in text


def test_docx_preserves_paragraph_order():
    docx_bytes = _make_docx_with_paragraphs(["First paragraph", "Second paragraph"])
    text = extract_text("docx", docx_bytes)
    assert text.index("First paragraph") < text.index("Second paragraph")


def test_docx_with_no_paragraphs_raises_extraction_error():
    empty_docx = _make_docx_with_paragraphs([])
    with pytest.raises(ExtractionError, match="No extractable text"):
        extract_text("docx", empty_docx)


def test_corrupt_docx_raises_extraction_error():
    with pytest.raises(ExtractionError, match="Failed to extract text"):
        extract_text("docx", b"not a valid docx file at all")


# --- TXT / MD extraction ---


def test_extracts_text_from_txt():
    text = extract_text("txt", "Plain text notes on TCP".encode("utf-8"))
    assert text == "Plain text notes on TCP"


def test_extracts_text_from_md_preserves_markdown_syntax():
    content = "# Heading\n\nSome **bold** notes.".encode("utf-8")
    text = extract_text("md", content)
    assert text == "# Heading\n\nSome **bold** notes."


def test_txt_strips_leading_trailing_whitespace():
    text = extract_text("txt", b"   \n  content with padding  \n   ")
    assert text == "content with padding"


def test_empty_txt_raises_extraction_error():
    with pytest.raises(ExtractionError, match="No extractable text"):
        extract_text("txt", b"   \n\n   ")  # whitespace only


# --- Dispatcher behavior ---


def test_unsupported_kind_raises_extraction_error():
    with pytest.raises(ExtractionError, match="No extractor available"):
        extract_text("exe", b"anything")