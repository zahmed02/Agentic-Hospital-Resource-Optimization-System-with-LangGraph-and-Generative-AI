"""
FAISS-based RAG retriever for similar discharge cases.
Builds index from admission notes and discharge data at startup.
"""

import os
import pickle
import numpy as np
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
import faiss
from app.core.database import SessionLocal
from app.models.database import Admission, Patient, DischargePrediction

# Global variables
_index = None
_metadata = None
_embedder = None

def get_embedder():
    """Lazy load sentence transformer model."""
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer('all-MiniLM-L6-v2')
    return _embedder

def build_faiss_index(force_rebuild=False):
    """
    Build FAISS index from discharge notes and predictions.
    Stores in a pickle file for persistence.
    """
    global _index, _metadata
    
    index_path = "./data/processed/faiss_index.pkl"
    
    if not force_rebuild and os.path.exists(index_path):
        with open(index_path, 'rb') as f:
            _index, _metadata = pickle.load(f)
        return
    
    # Query database for discharged patients with notes
    with SessionLocal() as db:
        # Get admissions that have discharge notes and are discharged
        admissions = db.query(Admission).filter(
            Admission.is_discharged == True,
            Admission.notes.isnot(None)
        ).all()
        
        if not admissions:
            print("No discharged admissions with notes found. Index empty.")
            _index = None
            _metadata = []
            return
        
        # Prepare texts and metadata
        texts = []
        metadata_list = []
        for adm in admissions:
            patient = db.query(Patient).filter(Patient.id == adm.patient_id).first()
            if not patient:
                continue
            # Combine condition, age, notes
            text = f"Condition: {patient.condition}\nAge: {patient.age}\nNotes: {adm.notes or ''}"
            texts.append(text)
            metadata_list.append({
                "patient_id": patient.patient_id,
                "condition": patient.condition,
                "age": patient.age,
                "admission_id": adm.id,
                "discharge_date": adm.discharge_date.strftime("%Y-%m-%d") if adm.discharge_date else None,
                "notes": adm.notes
            })
        
        if not texts:
            _index = None
            _metadata = []
            return
        
        # Embed texts
        embedder = get_embedder()
        embeddings = embedder.encode(texts, convert_to_numpy=True)
        
        # Build FAISS index
        dim = embeddings.shape[1]
        index = faiss.IndexFlatL2(dim)
        index.add(embeddings)
        
        _index = index
        _metadata = metadata_list
        
        # Save to disk
        os.makedirs("./data/processed", exist_ok=True)
        with open(index_path, 'wb') as f:
            pickle.dump((_index, _metadata), f)
        
        print(f"FAISS index built with {len(metadata_list)} cases.")

def get_similar_cases(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Retrieve top-k similar cases based on query string."""
    global _index, _metadata
    
    if _index is None or _metadata is None or len(_metadata) == 0:
        return [{"error": "No cases available."}]
    
    embedder = get_embedder()
    query_emb = embedder.encode([query], convert_to_numpy=True)
    
    distances, indices = _index.search(query_emb, min(top_k, len(_metadata)))
    
    results = []
    for idx in indices[0]:
        if idx < len(_metadata):
            results.append(_metadata[idx])
    return results

# Build index on module load
build_faiss_index()