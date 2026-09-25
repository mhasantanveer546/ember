"""Ember Backend — PDF Text Extraction (pypdf)"""

import io

from pypdf import PdfReader

from app.services.extraction.base import TextExtractor


class PdfTextExtractor(TextExtractor):
    def extract(self, content: bytes) -> str:
        reader = PdfReader(io.BytesIO(content))
        page_texts = [page.extract_text() or "" for page in reader.pages]
        return "\n\n".join(page_texts).strip()