"""
Ember Backend — Extraction Dispatcher (Phase 3.3)

Single entry point for the document pipeline: extract_text(kind, content)
picks the right extractor and wraps ANY underlying failure (a corrupt
PDF, a malformed DOCX, pypdf/python-docx raising their own internal
exception types) into one consistent ExtractionError — callers upstream
(the worker in Phase 3.5) only need to handle one exception type,
regardless of which file format actually failed.
"""

from app.services.extraction.base import TextExtractor
from app.services.extraction.docx_extractor import DocxTextExtractor
from app.services.extraction.pdf_extractor import PdfTextExtractor
from app.services.extraction.text_extractor import PlainTextExtractor


class ExtractionError(Exception):
    """Raised for any extraction failure, regardless of underlying cause."""


_EXTRACTORS: dict[str, TextExtractor] = {
    "pdf": PdfTextExtractor(),
    "docx": DocxTextExtractor(),
    "txt": PlainTextExtractor(),
    "md": PlainTextExtractor(),
}


def extract_text(kind: str, content: bytes) -> str:
    """
    Extract plain text from raw file bytes.

    Args:
        kind: One of "pdf", "docx", "txt", "md" — as returned by
            file_validation.validate_upload() (Phase 3.1).
        content: The raw, already-validated file bytes.

    Returns:
        Extracted plain text, non-empty.

    Raises:
        ExtractionError: for an unsupported kind, any underlying
        extraction failure, or a file that yields no extractable text
        at all (e.g. a scanned/image-only PDF with no text layer —
        OCR is out of scope for Ember's MVP).
    """
    extractor = _EXTRACTORS.get(kind)
    if extractor is None:
        raise ExtractionError(f"No extractor available for file kind: {kind!r}")

    try:
        text = extractor.extract(content)
    except Exception as exc:
        raise ExtractionError(f"Failed to extract text from {kind} file: {exc}") from exc

    if not text.strip():
        raise ExtractionError(
            f"No extractable text found in {kind} file "
            "(it may be empty, or an image-only/scanned document with no text layer)."
        )

    return text