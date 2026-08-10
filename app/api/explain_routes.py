"""
FastAPI endpoints for explainability (LIME).
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any
from app.services.explainer import explain_prediction
from app.services.predictor import predict_los
from app.core.cache import get_cached_response, set_cache
import json

router = APIRouter(prefix="/explain", tags=["Explainability"])

class FeatureContribution(BaseModel):
    feature: str
    contribution: float

class ExplanationResponse(BaseModel):
    patient_id: str
    predicted_los_days: float
    feature_values: Dict[str, Any]
    feature_contributions: List[FeatureContribution]
    intercept: float

@router.get("/predict/{patient_id}", response_model=ExplanationResponse)
async def explain_patient(patient_id: int):
    """
    Get LIME explanation for a patient's predicted length of stay.
    Results are cached (exact and semantic).
    """
    # Build cache key for this patient
    cache_key = f"explain:{patient_id}"
    
    # Try cache
    cached, _ = get_cached_response(cache_key)
    if cached:
        # Deserialize from JSON
        try:
            data = json.loads(cached)
            return ExplanationResponse(**data)
        except:
            pass  # If corrupt, recompute
    
    try:
        result = explain_prediction(patient_id)
        # Convert to serializable format
        serializable = {
            "patient_id": result["patient_id"],
            "predicted_los_days": result["predicted_los_days"],
            "feature_values": result["feature_values"],
            "feature_contributions": [
                {"feature": c["feature"], "contribution": c["contribution"]}
                for c in result["feature_contributions"]
            ],
            "intercept": result["intercept"]
        }
        # Cache as JSON string
        set_cache(cache_key, json.dumps(serializable))
        return ExplanationResponse(**serializable)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Explanation error: {str(e)}")

@router.get("/predict/{patient_id}/raw")
async def raw_predict(patient_id: int):
    """
    Get raw prediction (no explanation) for a patient.
    """
    try:
        result = predict_los(patient_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))