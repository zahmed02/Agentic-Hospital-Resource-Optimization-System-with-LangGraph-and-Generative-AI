"""
ChromaDB-based RAG retriever for similar discharge cases.

CHANGE: this previously hand-rolled a `faiss.IndexFlatL2` and persisted it
via pickle. It now uses a proper vector database (ChromaDB, persistent
client) as the spec called for. Embeddings come from the shared client in
app.core.embeddings so we don't load a second SentenceTransformer instance.
"""

import os
from typing import List, Dict, Any
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


def get_similar_cases(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Retrieve top-k similar discharge cases based on a query string."""
    collection = get_collection()
    if collection.count() == 0:
        return [{"error": "No cases available."}]

    query_emb = embed_query(query)
    results = collection.query(
        query_embeddings=[query_emb.tolist()],
        n_results=min(top_k, collection.count()),
    )

    metadatas = results.get("metadatas", [[]])[0]
    return list(metadatas)


# Build index on module load (no-op if already populated)
build_index()
