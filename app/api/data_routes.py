from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Integer
from typing import Optional
from datetime import date
from app.core.database import get_db
from app.models.database import Patient, Admission, Bed, DischargePrediction
from app.core.cache import _get_redis_client
import json
import subprocess
import sys

router = APIRouter(prefix="/api", tags=["Data"])

@router.get("/dashboard/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    total_patients = db.query(Patient).count()
    active_patients = db.query(Patient).filter(Patient.is_active == True).count()
    total_beds = db.query(Bed).count()
    occupied_beds = db.query(Bed).filter(Bed.is_occupied == True).count()
    occupancy_pct = round((occupied_beds / total_beds * 100) if total_beds else 0, 1)
    
    # PostgreSQL-compatible average length of stay (in days)
    avg_los = db.query(
        func.avg(
            func.extract('day', Patient.actual_discharge_date - Patient.admission_date)
        )
    ).filter(Patient.actual_discharge_date.isnot(None)).scalar() or 0
    avg_los = round(avg_los, 1)
    
    pending_discharges = db.query(Patient).filter(
        Patient.is_active == True,
        Patient.expected_discharge_date <= date.today()
    ).count()
    
    return {
        "total_patients": total_patients,
        "active_patients": active_patients,
        "bed_occupancy_pct": occupancy_pct,
        "avg_los_days": avg_los,
        "pending_discharges": pending_discharges,
        "total_beds": total_beds,
        "occupied_beds": occupied_beds
    }

@router.get("/patients")
def list_patients(
    skip: int = 0,
    limit: int = 50,
    search: Optional[str] = None,
    ward: Optional[str] = None,
    condition: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Patient)
    if search:
        query = query.filter(
            (Patient.patient_id.ilike(f"%{search}%")) |
            (Patient.name.ilike(f"%{search}%"))
        )
    if condition and condition != "ANY":
        query = query.filter(Patient.condition.ilike(f"%{condition}%"))
    if ward and ward != "ALL WARDS":
        query = query.join(Admission).filter(Admission.department == ward)
    patients = query.offset(skip).limit(limit).all()
    result = []
    for p in patients:
        admission = db.query(Admission).filter(Admission.patient_id == p.id).first()
        result.append({
            "id": p.id,
            "patient_id": p.patient_id,
            "name": p.name,
            "age": p.age,
            "gender": p.gender,
            "condition": p.condition,
            "admission_date": p.admission_date.isoformat() if p.admission_date else None,
            "is_active": p.is_active,
            "ward": admission.department if admission else None,
            "bed_number": admission.bed_number if admission else None,
            "admission_type": admission.admission_type if admission else None,
        })
    return result

@router.get("/patients/{patient_id}")
def get_patient(patient_id: int, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(404, "Patient not found")
    admission = db.query(Admission).filter(Admission.patient_id == patient.id).first()
    prediction = db.query(DischargePrediction).filter(DischargePrediction.patient_id == patient.id).order_by(DischargePrediction.prediction_date.desc()).first()
    return {
        "id": patient.id,
        "patient_id": patient.patient_id,
        "name": patient.name,
        "age": patient.age,
        "gender": patient.gender,
        "condition": patient.condition,
        "admission_date": patient.admission_date.isoformat() if patient.admission_date else None,
        "expected_discharge_date": patient.expected_discharge_date.isoformat() if patient.expected_discharge_date else None,
        "actual_discharge_date": patient.actual_discharge_date.isoformat() if patient.actual_discharge_date else None,
        "is_active": patient.is_active,
        "admission": {
            "type": admission.admission_type if admission else None,
            "department": admission.department if admission else None,
            "bed_number": admission.bed_number if admission else None,
            "doctor": admission.doctor_in_charge if admission else None,
            "notes": admission.notes if admission else None,
        } if admission else None,
        "prediction": {
            "predicted_discharge_date": prediction.predicted_discharge_date.isoformat() if prediction else None,
            "confidence": prediction.confidence_score if prediction else None,
        } if prediction else None
    }

@router.get("/beds/occupancy")
def get_bed_occupancy(db: Session = Depends(get_db)):
    # Group by ward and count total and occupied beds
    results = db.query(
        Bed.ward,
        func.count(Bed.id).label("total"),
        func.count().filter(Bed.is_occupied == True).label("occupied")
    ).group_by(Bed.ward).all()
    return [{"ward": r.ward, "total": r.total, "occupied": r.occupied} for r in results]

@router.get("/admissions")
def list_admissions(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    admissions = db.query(Admission).offset(skip).limit(limit).all()
    return [{
        "id": a.id,
        "patient_id": a.patient_id,
        "admission_type": a.admission_type,
        "department": a.department,
        "bed_number": a.bed_number,
        "doctor": a.doctor_in_charge,
        "admission_date": a.admission_date.isoformat() if a.admission_date else None,
        "discharge_date": a.discharge_date.isoformat() if a.discharge_date else None,
        "is_discharged": a.is_discharged,
    } for a in admissions]

@router.get("/discharge-predictions")
def list_predictions(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    preds = db.query(DischargePrediction).offset(skip).limit(limit).all()
    return [{
        "id": p.id,
        "patient_id": p.patient_id,
        "predicted_discharge_date": p.predicted_discharge_date.isoformat() if p.predicted_discharge_date else None,
        "confidence": p.confidence_score,
        "factors": json.loads(p.factors) if p.factors else None,
        "actual_discharge_date": p.actual_discharge_date.isoformat() if p.actual_discharge_date else None,
    } for p in preds]

@router.post("/cache/clear")
def clear_cache():
    redis_client = _get_redis_client()
    if redis_client is None:
        raise HTTPException(500, "Redis not available")
    try:
        redis_client.flushdb()
        return {"message": "Cache cleared successfully"}
    except Exception as e:
        raise HTTPException(500, f"Failed to clear cache: {str(e)}")

@router.post("/model/retrain")
def retrain_model():
    try:
        result = subprocess.run([sys.executable, "scripts/train_model.py"], capture_output=True, text=True)
        if result.returncode != 0:
            raise HTTPException(500, f"Training failed: {result.stderr}")
        return {"message": "Model retrained successfully", "output": result.stdout}
    except Exception as e:
        raise HTTPException(500, f"Failed to retrain: {str(e)}")