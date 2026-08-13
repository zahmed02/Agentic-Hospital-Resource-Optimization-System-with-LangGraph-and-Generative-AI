"""
LIME explainer for Length of Stay predictions.

CHANGE: explain_prediction() now also returns admission_date,
predicted_discharge_datetime, and baseline_discharge_datetime
(admission_date + LIME intercept days) — real calendar dates/times
instead of raw day-counts.
"""

import numpy as np
from typing import Dict, Any
from datetime import timedelta
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
        feature_names = model_data["feature_names"]
        encoders = model_data["encoders"]

        with SessionLocal() as db:
            patients = db.query(Patient).filter(
                Patient.actual_discharge_date.isnot(None)
            ).limit(100).all()

            if not patients:
                raise ValueError("No discharged patients found for LIME background.")

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

        categorical_features = [i for i, col in enumerate(feature_names) if col in encoders]

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
    Returns feature contributions, prediction, and real calendar
    date/times for both the baseline and AI-adjusted discharge estimate.
    """
    from app.services.predictor import predict_los

    pred_info = predict_los(patient_id)
    model_data = load_model()
    model = model_data["model"]
    feature_names = model_data["feature_names"]
    encoders = model_data["encoders"]

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

    explainer = get_explainer()
    exp = explainer.explain_instance(
        data_row=X_arr[0],
        predict_fn=model.predict,
        num_features=len(feature_names)
    )

    contributions = []
    for feature, weight in exp.local_exp[0]:
        contributions.append({
            "feature": feature_names[feature],
            "contribution": round(weight, 2)
        })
    contributions.sort(key=lambda x: abs(x["contribution"]), reverse=True)

    intercept_days = round(exp.intercept[0], 2)
    baseline_discharge_datetime = pred_info["admission_date"] + timedelta(days=intercept_days)

    return {
        "patient_id": pred_info["patient_id"],
        "admission_date": pred_info["admission_date"],
        "predicted_los_days": pred_info["predicted_los_days"],
        "predicted_discharge_datetime": pred_info["predicted_discharge_datetime"],
        "baseline_discharge_datetime": baseline_discharge_datetime,
        "feature_values": pred_info["feature_values"],
        "feature_contributions": contributions,
        "intercept": intercept_days
    }
