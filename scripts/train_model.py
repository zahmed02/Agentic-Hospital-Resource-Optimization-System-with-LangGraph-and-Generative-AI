"""
Train a RandomForest model to predict Length of Stay (LOS).
Run once to generate the model file.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import joblib
from app.core.database import SessionLocal
from app.models.database import Patient, Admission

def load_training_data():
    """Load discharged patients with actual discharge dates."""
    with SessionLocal() as db:
        # Get patients who have been discharged (actual_discharge_date not null)
        patients = db.query(Patient).filter(
            Patient.actual_discharge_date.isnot(None)
        ).all()
        
        if not patients:
            print("No discharged patients found. Cannot train.")
            return None
        
        data = []
        for p in patients:
            # Get first admission for this patient
            admission = db.query(Admission).filter(
                Admission.patient_id == p.id
            ).first()
            if not admission:
                continue
            
            # Calculate length of stay in days
            if p.actual_discharge_date and p.admission_date:
                los = (p.actual_discharge_date - p.admission_date.date()).days
                if los <= 0:
                    continue
            else:
                continue
            
            data.append({
                "patient_id": p.id,
                "age": p.age,
                "condition": p.condition,
                "admission_type": admission.admission_type,
                "department": admission.department,
                "gender": p.gender,
                "los": los
            })
        
        return pd.DataFrame(data)

def train_model():
    """Train and save the RandomForest model."""
    print("Loading training data...")
    df = load_training_data()
    if df is None or df.empty:
        print("No training data available. Please seed discharged patients first.")
        return
    
    print(f"Training data shape: {df.shape}")
    
    # Prepare features
    feature_cols = ["age", "condition", "admission_type", "gender"]
    X = df[feature_cols].copy()
    y = df["los"].values
    
    # Encode categorical columns
    categorical_cols = ["condition", "admission_type", "gender"]
    encoders = {}
    for col in categorical_cols:
        le = LabelEncoder()
        X[col] = le.fit_transform(X[col].astype(str))
        encoders[col] = le
    
    # Split for validation
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # Train model
    print("Training RandomForest model...")
    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    print(f"Model trained: MAE={mae:.2f} days, R2={r2:.2f}")
    
    # Save model and encoders
    os.makedirs("./models", exist_ok=True)
    model_path = "./models/los_predictor.joblib"
    joblib.dump({
        "model": model,
        "encoders": encoders,
        "feature_names": feature_cols,
        "mae": mae,
        "r2": r2
    }, model_path)
    print(f"Model saved to {model_path}")
    
    return model

if __name__ == "__main__":
    train_model()