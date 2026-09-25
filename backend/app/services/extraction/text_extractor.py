"""
Ember Backend — Plain Text Extraction (TXT / Markdown)

No parsing needed — Phase 3.1's validation already confirmed the content
decodes as valid UTF-8. Markdown syntax (#, *, etc.) is left as-is
rather than stripped: it's still meaningful, readable text, and search
should be able to match words regardless of whether they're inside
Markdown formatting.
"""

from app.services.extraction.base import TextExtractor


class PlainTextExtractor(TextExtractor):
    def extract(self, content: bytes) -> str:
        return content.decode("utf-8").strip()