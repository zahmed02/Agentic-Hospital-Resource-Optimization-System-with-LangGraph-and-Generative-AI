"""
Redis + FAISS semantic cache for agent responses.
Handles older Redis versions (RESP2) and falls back gracefully.

CHANGE: now uses the shared embedder from app.core.embeddings instead of
loading its own SentenceTransformer instance (previously duplicated with
app/services/retriever.py).
"""

import json
import pickle
import hashlib
import logging
import numpy as np
import base64
from typing import Optional, Tuple
from datetime import datetime
import redis
import faiss
from app.core.config import settings
from app.core.embeddings import get_embedder, normalize as _normalize_vector

logger = logging.getLogger(__name__)

# Global FAISS index and metadata
_index = None
_index_keys = []  # list of Redis keys corresponding to each vector
_loaded = False
_redis_available = True


def _get_redis_client():
    """Return a Redis client with RESP2 protocol (compatible with Redis 3.x)."""
    try:
        # Force protocol=2 to avoid HELLO command
        return redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            protocol=2  # RESP2 – compatible with Redis 3.x
        )
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}. Cache will be in-memory only.")
        return None


def _hash_query(query: str) -> str:
    """MD5 hash of normalized query for exact match."""
    return hashlib.md5(query.strip().lower().encode()).hexdigest()


def _build_faiss_index():
    """Load cached embeddings from Redis and build FAISS index."""
    global _index, _index_keys, _loaded, _redis_available
    if _loaded:
        return

    redis_client = _get_redis_client()
    if redis_client is None:
        _redis_available = False
        _loaded = True
        return

    try:
        keys = redis_client.keys("cache:query:*")
        if not keys:
            _index = None
            _index_keys = []
            _loaded = True
            return

        embeddings = []
        keys_sorted = sorted(keys)
        for key in keys_sorted:
            emb_b64 = redis_client.hget(key, "embedding")
            if emb_b64:
                try:
                    emb_bytes = base64.b64decode(emb_b64)
                    emb = np.frombuffer(emb_bytes, dtype=np.float32)
                    embeddings.append(_normalize_vector(emb))
                    _index_keys.append(key)
                except Exception as e:
                    logger.warning(f"Skipping corrupt embedding for key {key}: {e}")
                    redis_client.delete(key)

        if not embeddings:
            _index = None
            _index_keys = []
            _loaded = True
            return

        dim = len(embeddings[0])
        index = faiss.IndexFlatIP(dim)
        index.add(np.array(embeddings, dtype=np.float32))
        _index = index
        _loaded = True
    except Exception as e:
        logger.error(f"Failed to build FAISS index from Redis: {e}")
        _redis_available = False
        _loaded = True


def _store_cache(query: str, response: str) -> None:
    redis_client = _get_redis_client()
    if redis_client is None:
        return

    try:
        key = f"cache:query:{_hash_query(query)}"
        emb = get_embedder().encode([query], convert_to_numpy=True)[0]
        emb_norm = _normalize_vector(emb)
        emb_base64 = base64.b64encode(emb_norm.tobytes()).decode('utf-8')

        pipe = redis_client.pipeline()
        pipe.hset(key, "response", response)
        pipe.hset(key, "embedding", emb_base64)
        pipe.hset(key, "timestamp", datetime.utcnow().isoformat())
        pipe.expire(key, settings.CACHE_TTL_SECONDS)
        pipe.execute()

        global _index, _index_keys
        if _index is None:
            dim = len(emb_norm)
            _index = faiss.IndexFlatIP(dim)
        _index.add(np.array([emb_norm], dtype=np.float32))
        _index_keys.append(key)
    except Exception as e:
        logger.warning(f"Failed to store cache in Redis: {e}")


def _get_exact(query: str) -> Optional[str]:
    redis_client = _get_redis_client()
    if redis_client is None:
        return None
    try:
        key = f"cache:query:{_hash_query(query)}"
        return redis_client.hget(key, "response")
    except Exception:
        return None


def _get_semantic(query: str) -> Optional[str]:
    global _index, _index_keys
    if _index is None or _index.ntotal == 0:
        return None

    emb = get_embedder().encode([query], convert_to_numpy=True)[0]
    emb_norm = _normalize_vector(emb)

    distances, indices = _index.search(np.array([emb_norm], dtype=np.float32), 1)
    best_dist = distances[0][0]
    best_idx = indices[0][0]

    if best_idx >= 0 and best_dist >= settings.SEMANTIC_SIMILARITY_THRESHOLD:
        redis_client = _get_redis_client()
        if redis_client is None:
            return None
        try:
            key = _index_keys[best_idx]
            return redis_client.hget(key, "response")
        except Exception:
            return None
    return None


def get_cached_response(query: str) -> Tuple[Optional[str], bool]:
    """
    Returns (cached_response, from_semantic).
    """
    exact = _get_exact(query)
    if exact:
        return exact, False

    if not _loaded:
        _build_faiss_index()

    semantic = _get_semantic(query)
    if semantic:
        return semantic, True

    return None, False


def set_cache(query: str, response: str) -> None:
    """Store a new cache entry."""
    _store_cache(query, response)


# Build index on module load
_build_faiss_index()
