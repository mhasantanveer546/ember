"""
Ember Backend — Content Hashing (Phase 3.4)

SHA-256 over raw file bytes. Deterministic and collision-resistant
enough for deduplication at any realistic document-corpus scale — see
phase notes for why this isn't a cryptographic-security claim, just a
reliable "are these the same file?" check.
"""

import hashlib


def compute_content_hash(content: bytes) -> str:
    """Return the SHA-256 hex digest (64 characters) of `content`."""
    return hashlib.sha256(content).hexdigest()