"""
Ember Backend — Text Extractor Interface (Phase 3.3)

Each file type gets its own extractor implementing this interface.
Extraction's job ends at "produce clean plain text" — no lowercasing,
stopword removal, or tokenization here; that's search_engine.tokenizer /
normalizer's job (Phase 1), kept deliberately separate so linguistic
processing logic lives in exactly one place.
"""

from abc import ABC, abstractmethod


class TextExtractor(ABC):
    @abstractmethod
    def extract(self, content: bytes) -> str:
        """
        Extract plain text from raw file bytes.

        Raises:
            Exception: implementations may raise their underlying
            library's exceptions on corrupt/unreadable content — the
            dispatcher (extraction_service.py) wraps these uniformly
            into ExtractionError, so callers only need to handle one
            exception type regardless of file kind.
        """