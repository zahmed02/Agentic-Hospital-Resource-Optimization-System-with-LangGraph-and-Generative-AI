"""
Shared embedding client.

Previously, `app/core/cache.py` and `app/services/retriever.py` each loaded
their own SentenceTransformer('all-MiniLM-L6-v2') instance independently.
This module gives both a single shared client so the model is only loaded
once per process.
"""

from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer
from app.core.config import settings

_model: SentenceTransformer | None = None


def get_embedder() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(settings.EMBEDDING_MODEL)
    return _model


def embed_texts(texts: List[str]) -> np.ndarray:
    """Embed a batch of texts. Returns an (N, dim) float32 array."""
    return get_embedder().encode(texts, convert_to_numpy=True)


def embed_query(text: str) -> np.ndarray:
    """Embed a single query string. Returns a (dim,) float32 array."""
    return embed_texts([text])[0]


def normalize(vec: np.ndarray) -> np.ndarray:
    """L2-normalize a vector for cosine similarity via inner product."""
    norm = np.linalg.norm(vec)
    if norm == 0:
        return vec
    return vec / norm
