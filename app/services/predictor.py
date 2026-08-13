"""
Prediction service for Length of Stay using RandomForest model.

CHANGE: predict_los() now returns admission_date and a computed
predicted_discharge_datetime (admission_date + predicted_los_days) —
a real calendar date/time, not just a floating day-count.
"""

import os
import joblib
import numpy as np
from typing import Dict, Any
from datetime import timedelta
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
    Returns dict with prediction, feature values, admission_date, and a
    computed predicted_discharge_datetime (real calendar date/time).
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

        features = {
            "age": patient.age,
            "condition": patient.condition,
            "admission_type": admission.admission_type,
            "gender": patient.gender
        }

        X = []
        for col in feature_names:
            if col in encoders:
                val = str(features.get(col, "Unknown"))
                try:
                    encoded = encoders[col].transform([val])[0]
                except ValueError:
                    encoded = 0
                X.append(encoded)
            else:
                X.append(features.get(col, 0))

        X_arr = np.array([X])
        prediction = model.predict(X_arr)[0]
        predicted_los_days = round(float(prediction), 1)

        # Real calendar date/time this patient is predicted to be
        # discharged, anchored to their actual admission timestamp —
        # not just a duration in days.
        predicted_discharge_datetime = patient.admission_date + timedelta(days=predicted_los_days)

        return {
            "patient_id": patient.patient_id,
            "age": patient.age,
            "condition": patient.condition,
            "admission_type": admission.admission_type,
            "gender": patient.gender,
            "admission_date": patient.admission_date,
            "predicted_los_days": predicted_los_days,
            "predicted_discharge_datetime": predicted_discharge_datetime,
            "feature_names": feature_names,
            "feature_values": features
        }
