"""
Prediction service for Length of Stay using RandomForest model.
"""

import os
import joblib
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from app.core.database import SessionLocal
from app.models.database import Patient, Admission

MODEL_PATH = "./models/los_predictor.joblib"
_model_data = None

def load_model():
    """Load the trained model and encoders."""
    global _model_data
    if _model_data is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"Model not found at {MODEL_PATH}. Run scripts/train_model.py first.")
        _model_data = joblib.load(MODEL_PATH)
    return _model_data

def predict_los(patient_id: int) -> Dict[str, Any]:
    """
    Predict length of stay for a given patient.
    Returns dict with prediction and feature values.
    """
    model_data = load_model()
    model = model_data["model"]
    encoders = model_data["encoders"]
    feature_names = model_data["feature_names"]
    
    with SessionLocal() as db:
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            raise ValueError(f"Patient {patient_id} not found.")
        
        admission = db.query(Admission).filter(
            Admission.patient_id == patient_id
        ).first()
        if not admission:
            raise ValueError(f"No admission found for patient {patient_id}.")
        
        # Build feature vector
        features = {
            "age": patient.age,
            "condition": patient.condition,
            "admission_type": admission.admission_type,
            "gender": patient.gender
        }
        
        # Encode categoricals
        X = []
        for col in feature_names:
            if col in encoders:
                val = str(features.get(col, "Unknown"))
                try:
                    encoded = encoders[col].transform([val])[0]
                except ValueError:
                    # Unknown category - use 0 as fallback
                    encoded = 0
                X.append(encoded)
            else:
                X.append(features.get(col, 0))
        
        X_arr = np.array([X])
        prediction = model.predict(X_arr)[0]
        
        return {
            "patient_id": patient.patient_id,
            "age": patient.age,
            "condition": patient.condition,
            "admission_type": admission.admission_type,
            "gender": patient.gender,
            "predicted_los_days": round(float(prediction), 1),
            "feature_names": feature_names,
            "feature_values": features
        }