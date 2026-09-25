"""Ember Backend — DOCX Text Extraction (python-docx)"""

import io

import docx

from app.services.extraction.base import TextExtractor


class DocxTextExtractor(TextExtractor):
    def extract(self, content: bytes) -> str:
        document = docx.Document(io.BytesIO(content))
        paragraphs = [paragraph.text for paragraph in document.paragraphs]
        return "\n".join(paragraphs).strip()