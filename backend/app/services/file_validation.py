"""
Ember Backend — File Upload Validation (Phase 3.1)

Validates an uploaded file BEFORE it's stored or processed anywhere.
Never trusts the filename extension or a claimed Content-Type on their
own — both are trivially spoofable by a client. Instead, the extension
is treated as a CLAIM, and the actual byte content is checked against
what that claim implies (magic bytes, and for DOCX, internal ZIP
structure).

Supported types: pdf, txt, md, docx — matching the master plan's Phase 3
scope. Max size: 25 MB.
"""

import io
import zipfile

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md", ".docx"}
MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB

_PDF_MAGIC_BYTES = b"%PDF-"
_ZIP_MAGIC_BYTES = b"PK\x03\x04"
_DOCX_REQUIRED_ENTRY = "word/document.xml"


class FileValidationError(Exception):
    """Raised for any reason an uploaded file is rejected. Message is
    safe to show directly to the end user."""


def _extract_extension(filename: str) -> str:
    if "." not in filename:
        return ""
    return "." + filename.rsplit(".", 1)[-1].lower()


def _validate_size(content: bytes) -> None:
    if len(content) == 0:
        raise FileValidationError("File is empty.")
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise FileValidationError(
            f"File exceeds the maximum allowed size of {MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB."
        )


def _validate_pdf(content: bytes) -> None:
    if not content.startswith(_PDF_MAGIC_BYTES):
        raise FileValidationError(
            "File has a .pdf extension but its content is not a valid PDF."
        )


def _validate_docx(content: bytes) -> None:
    if not content.startswith(_ZIP_MAGIC_BYTES):
        raise FileValidationError(
            "File has a .docx extension but its content is not a valid ZIP/DOCX archive."
        )

    # Magic bytes alone only prove "this is SOME zip file" — DOCX, XLSX,
    # PPTX, and plain ZIPs are all indistinguishable at that level. Open
    # the archive and confirm the one entry that's specific to Word
    # documents is actually present.
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            if _DOCX_REQUIRED_ENTRY not in archive.namelist():
                raise FileValidationError(
                    "File has a .docx extension but is not a valid Word document "
                    "(missing internal word/document.xml)."
                )
    except zipfile.BadZipFile as exc:
        raise FileValidationError(
            "File has a .docx extension but is not a valid ZIP/DOCX archive."
        ) from exc


def _validate_text_like(content: bytes) -> None:
    if b"\x00" in content:
        raise FileValidationError(
            "File claims to be plain text but contains binary data (null bytes)."
        )
    try:
        content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise FileValidationError(
            "File claims to be plain text but is not valid UTF-8."
        ) from exc


def validate_upload(filename: str, content: bytes) -> str:
    """
    Validate an uploaded file's extension, size, and actual content
    against what its extension claims to be.

    Args:
        filename: The original filename as provided by the client
            (untrusted — used only to determine which checks to apply).
        content: The raw file bytes actually received.

    Returns:
        The validated file kind: "pdf", "txt", "md", or "docx" — for
        Phase 3.3's extractor selection to use, so it doesn't need to
        re-derive this from the filename itself.

    Raises:
        FileValidationError: with a message safe to show the end user,
        for any validation failure.
    """
    extension = _extract_extension(filename)
    if extension not in ALLOWED_EXTENSIONS:
        raise FileValidationError(
            f"File type '{extension or '(none)'}' is not supported. "
            f"Allowed types: {', '.join(sorted(ALLOWED_EXTENSIONS))}."
        )

    _validate_size(content)

    if extension == ".pdf":
        _validate_pdf(content)
    elif extension == ".docx":
        _validate_docx(content)
    else:  # .txt or .md
        _validate_text_like(content)

    return extension.lstrip(".")