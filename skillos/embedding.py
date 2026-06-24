"""Embedding helper.

G-Memory / MemoryOS both use ``sentence-transformers/all-MiniLM-L6-v2``
(``GMemory/mas/utils.py:54 EmbeddingFunc``). For a reproducible, offline, dependency-light
default we ship a deterministic hashing embedder; the real ST backend is opt-in via
``Embedder(backend="st")`` so a real-LLM run matches the references exactly.
"""

from __future__ import annotations

import hashlib
import math
import re

_TOKEN = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> list[str]:
    return _TOKEN.findall(text.lower())


class Embedder:
    def __init__(self, backend: str = "hash", dim: int = 256, model: str = "all-MiniLM-L6-v2"):
        self.backend = backend
        self.dim = dim
        self._st = None
        if backend == "st":
            from sentence_transformers import SentenceTransformer  # lazy

            self._st = SentenceTransformer(model)
            self.dim = self._st.get_sentence_embedding_dimension()

    def embed(self, text: str) -> list[float]:
        if self._st is not None:
            return self._st.encode(text, normalize_embeddings=True).tolist()
        return self._hash_embed(text)

    def _hash_embed(self, text: str) -> list[float]:
        """Deterministic bag-of-hashed-tokens, L2-normalized (cosine-ready)."""
        vec = [0.0] * self.dim
        for tok in _tokens(text):
            hv = int(hashlib.md5(tok.encode()).hexdigest(), 16)
            vec[hv % self.dim] += 1.0
        norm = math.sqrt(sum(v * v for v in vec))
        return [v / norm for v in vec] if norm else vec


def cosine(a: list[float], b: list[float]) -> float:
    """Cosine similarity (vectors are produced L2-normalized, so this is a dot product)."""
    return sum(x * y for x, y in zip(a, b))
