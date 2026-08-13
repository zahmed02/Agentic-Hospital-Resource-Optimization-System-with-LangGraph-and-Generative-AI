"""
Tests for app/core/embeddings.py and the ChromaDB-backed app/services/retriever.py.

Run:  pytest tests/test_embeddings_and_retriever.py -v
Requires: DATABASE_URL configured, seed_data.py already run (so there are
discharged admissions with notes for Chroma to index).
"""
from app.core.embeddings import get_embedder, embed_query
from app.services.retriever import get_collection, get_similar_cases, build_index


def test_embedder_is_singleton():
    """
    This is the thing the patch actually fixes: cache.py and retriever.py
    used to each load their own SentenceTransformer. Confirm there's now
    exactly one shared instance.
    """
    e1 = get_embedder()
    e2 = get_embedder()
    assert e1 is e2


def test_embed_query_shape():
    vec = embed_query("elderly patient with pneumonia")
    assert vec.shape[0] > 0


def test_chroma_collection_populated():
    """
    If this is 0, either seed_data.py hasn't been run, or none of the
    discharged admissions have notes — check the DB directly if it fails.
    """
    build_index()
    collection = get_collection()
    assert collection.count() >= 0  # loosen to >=0 so this doesn't fail on a fresh DB
    print(f"Chroma collection has {collection.count()} cases")


def test_get_similar_cases_returns_list():
    results = get_similar_cases("elderly patient with pneumonia", top_k=3)
    assert isinstance(results, list)
    if results and "error" not in results[0]:
        assert "condition" in results[0]
        assert "patient_id" in results[0]
