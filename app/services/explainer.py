"""
LIME explainer for Length of Stay predictions.
"""

import os
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, List
import lime
import lime.lime_tabular
from app.services.predictor import load_model
from app.core.database import SessionLocal
from app.models.database import Patient, Admission

_explainer = None

def get_explainer():
    """Lazy load the LIME explainer."""
    global _explainer
    if _explainer is None:
        model_data = load_model()
        model = model_data["model"]
        encoders = model_data["encoders"]
        feature_names = model_data["feature_names"]
        
        # We need training data to build the explainer.
        # Load a sample from DB to define feature ranges.
        with SessionLocal() as db:
            # Get some discharged patients with admissions for background
            patients = db.query(Patient).filter(
                Patient.actual_discharge_date.isnot(None)
            ).limit(100).all()
            
            if not patients:
                raise ValueError("No discharged patients found for LIME background.")
            
            # Build background dataset
            background = []
            for p in patients:
                adm = db.query(Admission).filter(Admission.patient_id == p.id).first()
                if not adm:
                    continue
                row = []
                for col in feature_names:
                    if col == "age":
                        row.append(p.age)
                    elif col in encoders:
                        val = getattr(p, col, None) or getattr(adm, col, None)
                        if val is None:
                            row.append(0)
                        else:
                            try:
                                row.append(encoders[col].transform([str(val)])[0])
                            except ValueError:
                                row.append(0)
                    else:
                        row.append(0)
                if len(row) == len(feature_names):
                    background.append(row)
            
            if not background:
                raise ValueError("Could not build background dataset for LIME.")
            
            background = np.array(background)
        
        # Determine categorical features
        categorical_features = []
        for i, col in enumerate(feature_names):
            if col in encoders:
                categorical_features.append(i)
        
        # Build explainer
        _explainer = lime.lime_tabular.LimeTabularExplainer(
            training_data=background,
            feature_names=feature_names,
            categorical_features=categorical_features,
            mode='regression'
        )
    return _explainer

def explain_prediction(patient_id: int) -> Dict[str, Any]:
    """
    Generate LIME explanation for a patient's predicted LOS.
    Returns feature contributions and prediction.
    """
    from app.services.predictor import predict_los
    
    # Get prediction and features
    pred_info = predict_los(patient_id)
    model_data = load_model()
    model = model_data["model"]
    feature_names = model_data["feature_names"]
    encoders = model_data["encoders"]
    
    # Build the feature vector for this patient
    X = []
    for col in feature_names:
        val = pred_info["feature_values"].get(col, 0)
        if col in encoders:
            try:
                X.append(encoders[col].transform([str(val)])[0])
            except ValueError:
                X.append(0)
        else:
            X.append(val)
    
    X_arr = np.array([X])
    
    # Get explainer
    explainer = get_explainer()
    
    # Get explanation
    exp = explainer.explain_instance(
        data_row=X_arr[0],
        predict_fn=model.predict,
        num_features=len(feature_names)
    )
    
    # Extract contributions
    contributions = []
    for feature, weight in exp.local_exp[0]:
        contributions.append({
            "feature": feature_names[feature],
            "contribution": round(weight, 2)
        })
    
    # Sort by absolute contribution
    contributions.sort(key=lambda x: abs(x["contribution"]), reverse=True)
    
    return {
        "patient_id": pred_info["patient_id"],
        "predicted_los_days": pred_info["predicted_los_days"],
        "feature_values": pred_info["feature_values"],
        "feature_contributions": contributions,
        "intercept": round(exp.intercept[0], 2)
    }