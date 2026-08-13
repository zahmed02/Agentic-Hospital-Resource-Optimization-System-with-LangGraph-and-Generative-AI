"""
FastAPI endpoints for explainability (LIME).

CHANGE: now uses centralized schemas (app.models.schemas) and serializes
admission_date / predicted_discharge_datetime / baseline_discharge_datetime
as ISO 8601 strings so the frontend can format them as real dates/times.
"""

from fastapi import APIRouter, HTTPException
from app.services.explainer import explain_prediction
from app.services.predictor import predict_los
from app.core.cache import get_cached_response, set_cache
from app.models.schemas import ExplanationResponse, FeatureContribution
import json

router = APIRouter(prefix="/explain", tags=["Explainability"])


@router.get("/predict/{patient_id}", response_model=ExplanationResponse)
async def explain_patient(patient_id: int):
    """
    Get LIME explanation for a patient's predicted length of stay,
    including real calendar date/times for the baseline and AI-adjusted
    discharge estimate. Results are cached (exact and semantic).
    """
    cache_key = f"explain:{patient_id}"

    cached, _ = get_cached_response(cache_key)
    if cached:
        try:
            data = json.loads(cached)
            return ExplanationResponse(**data)
        except Exception:
            pass  # If corrupt or stale schema, recompute

    try:
        result = explain_prediction(patient_id)
        serializable = {
            "patient_id": result["patient_id"],
            "admission_date": result["admission_date"].isoformat(),
            "predicted_los_days": result["predicted_los_days"],
            "predicted_discharge_datetime": result["predicted_discharge_datetime"].isoformat(),
            "baseline_discharge_datetime": result["baseline_discharge_datetime"].isoformat(),
            "feature_values": result["feature_values"],
            "feature_contributions": [
                {"feature": c["feature"], "contribution": c["contribution"]}
                for c in result["feature_contributions"]
            ],
            "intercept": result["intercept"]
        }
        set_cache(cache_key, json.dumps(serializable))
        return ExplanationResponse(**serializable)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Explanation error: {str(e)}")


@router.get("/predict/{patient_id}/raw")
async def raw_predict(patient_id: int):
    """
    Get raw prediction (no explanation) for a patient, including the
    real predicted discharge date/time.
    """
    try:
        result = predict_los(patient_id)
        result["admission_date"] = result["admission_date"].isoformat()
        result["predicted_discharge_datetime"] = result["predicted_discharge_datetime"].isoformat()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
