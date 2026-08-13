"""
ChromaDB-based RAG retriever for similar discharge cases.

CHANGE: get_similar_cases() now accepts optional condition / min_age / max_age
filters. Age range is applied as a hard Chroma metadata filter (not left to
embedding similarity, which was letting a 34-year-old rank near a "50s"
query just because the surrounding text was phrased similarly). Condition is
applied as a case-insensitive substring filter on the pre-ranked candidate
set, since Chroma's `where` doesn't support partial string matches.
"""

import os
from typing import List, Dict, Any, Optional
import chromadb
from app.core.database import SessionLocal
from app.models.database import Admission, Patient
from app.core.embeddings import embed_texts, embed_query

_client = None
_collection = None
COLLECTION_NAME = "discharge_cases"
PERSIST_DIR = "./data/processed/chroma_db"


def get_client():
    global _client
    if _client is None:
        os.makedirs(PERSIST_DIR, exist_ok=True)
        _client = chromadb.PersistentClient(path=PERSIST_DIR)
    return _client


def get_collection():
    global _collection
    if _collection is None:
        _collection = get_client().get_or_create_collection(COLLECTION_NAME)
    return _collection


def build_index(force_rebuild: bool = False) -> None:
    """
    Build (or rebuild) the Chroma collection from discharged admissions
    that have notes. Safe to call repeatedly — if the collection already
    has data and force_rebuild is False, this is a no-op.
    """
    global _collection
    collection = get_collection()

    if force_rebuild:
        get_client().delete_collection(COLLECTION_NAME)
        _collection = get_client().get_or_create_collection(COLLECTION_NAME)
        collection = _collection
    elif collection.count() > 0:
        return

    with SessionLocal() as db:
        admissions = db.query(Admission).filter(
            Admission.is_discharged == True,
            Admission.notes.isnot(None)
        ).all()

        if not admissions:
            print("No discharged admissions with notes found. Index empty.")
            return

        ids, texts, metadatas = [], [], []
        for adm in admissions:
            patient = db.query(Patient).filter(Patient.id == adm.patient_id).first()
            if not patient:
                continue
            text = f"Condition: {patient.condition}\nAge: {patient.age}\nNotes: {adm.notes or ''}"
            ids.append(str(adm.id))
            texts.append(text)
            metadatas.append({
                "patient_id": patient.patient_id,
                "condition": patient.condition or "",
                "age": patient.age or 0,
                "admission_id": adm.id,
                "discharge_date": adm.discharge_date.strftime("%Y-%m-%d") if adm.discharge_date else "",
                "notes": (adm.notes or "")[:500],
            })

        if not texts:
            return

        embeddings = embed_texts(texts)
        collection.add(
            ids=ids,
            embeddings=embeddings.tolist(),
            documents=texts,
            metadatas=metadatas,
        )
        print(f"Chroma index built with {len(texts)} cases.")


def get_similar_cases(
    query: str,
    top_k: int = 5,
    condition: Optional[str] = None,
    min_age: Optional[int] = None,
    max_age: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Retrieve top-k similar discharge cases.

    - min_age/max_age are applied as a HARD metadata filter in Chroma before
      ranking — a query like "in their 50s" with min_age=50, max_age=59 will
      never return a 34-year-old, unlike relying on embedding similarity alone.
    - condition is applied as a case-insensitive substring filter on the
      similarity-ranked candidates (over-fetched, then filtered), since
      Chroma's `where` only supports exact/range matches, not partial text.
      If no candidate matches the condition, falls back to the unfiltered
      ranked results rather than returning nothing.
    """
    collection = get_collection()
    if collection.count() == 0:
        return [{"error": "No cases available."}]

    where = None
    if min_age is not None or max_age is not None:
        age_filter: Dict[str, int] = {}
        if min_age is not None:
            age_filter["$gte"] = min_age
        if max_age is not None:
            age_filter["$lte"] = max_age
        where = {"age": age_filter}

    query_emb = embed_query(query)

    # Over-fetch when we still need to post-filter by condition substring,
    # so filtering doesn't leave us with fewer than top_k results.
    fetch_n = min(top_k * 4 if condition else top_k, collection.count())

    results = collection.query(
        query_embeddings=[query_emb.tolist()],
        n_results=fetch_n,
        where=where,
    )

    metadatas = list(results.get("metadatas", [[]])[0])

    if condition:
        cond_lower = condition.lower()
        matched = [m for m in metadatas if cond_lower in (m.get("condition") or "").lower()]
        if matched:
            metadatas = matched
        # else: no exact condition match among candidates — keep the
        # similarity-ranked results rather than returning an empty list.

    return metadatas[:top_k]


# Build index on module load (no-op if already populated)
build_index()
