"""
Seed script for Hospital-Resource-Optimizer-Agent
Generates 100+ synthetic patients, admissions, beds, and discharge histories.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import random
from datetime import datetime, timedelta
from faker import Faker
from sqlalchemy import text
from app.core.database import SessionLocal, engine, Base
from app.models.database import Patient, Admission, Bed, DischargePrediction

fake = Faker()

# ========== Realistic Medical Data ==========
CONDITIONS = [
    "Pneumonia", "Fractured Femur", "Cardiac Arrhythmia", "Appendicitis",
    "Stroke", "Type 2 Diabetes", "Hypertension", "Asthma Exacerbation",
    "Urinary Tract Infection", "Sepsis", "Gallstones", "Kidney Stones",
    "COVID-19", "Heart Failure", "COPD", "Pulmonary Embolism",
    "Gastroenteritis", "Migraine", "Cellulitis", "Anemia"
]

DEPARTMENTS = ["Emergency", "Cardiology", "Orthopedics", "Internal Medicine", 
               "Pulmonology", "Neurology", "General Surgery", "Urology"]

WARDS = ["Ward A", "Ward B", "Ward C", "Ward D", "ICU", "CCU"]

DOCTORS = [
    "Dr. Sarah Johnson", "Dr. Michael Chen", "Dr. Emily Davis", 
    "Dr. Robert Williams", "Dr. Jessica Brown", "Dr. David Miller",
    "Dr. Maria Garcia", "Dr. James Wilson"
]

ADMISSION_TYPES = ["Emergency", "Elective", "Urgent"]

# ========== Helper Functions ==========
def random_date(start, end):
    """Generate a random datetime between start and end."""
    return start + timedelta(
        seconds=random.randint(0, int((end - start).total_seconds()))
    )

def get_expected_los(condition):
    """Return expected length of stay (days) based on condition severity."""
    severe = ["Stroke", "Sepsis", "Heart Failure", "Pneumonia", "COVID-19"]
    moderate = ["Fractured Femur", "Cardiac Arrhythmia", "COPD", "Pulmonary Embolism"]
    mild = ["UTI", "Gastroenteritis", "Migraine", "Cellulitis", "Anemia"]
    
    if condition in severe:
        return random.randint(5, 12)
    elif condition in moderate:
        return random.randint(3, 7)
    else:
        return random.randint(1, 4)

# ========== Clear Existing Data ==========
def clear_data():
    """Delete all existing data in reverse dependency order."""
    print("🧹 Clearing existing data...")
    with SessionLocal() as db:
        db.execute(text("DELETE FROM discharge_predictions;"))
        db.execute(text("DELETE FROM admissions;"))
        db.execute(text("DELETE FROM beds;"))
        db.execute(text("DELETE FROM patients;"))
        db.commit()
    print("Existing data cleared.")

# ========== Seed Patients & Admissions ==========
def seed_database(num_patients=120):
    """Generate and insert synthetic data."""
    print(f"Generating {num_patients} patients...")
    
    with SessionLocal() as db:
        # 1. Create Patients
        patients = []
        for i in range(num_patients):
            condition = random.choice(CONDITIONS)
            age = random.randint(18, 90)
            gender = random.choice(["Male", "Female"])
            admitted_at = random_date(
                datetime.now() - timedelta(days=30),
                datetime.now() + timedelta(days=1)
            )
            
            patient = Patient(
                patient_id=f"P-{2026}{i:04d}",
                name=fake.name(),
                age=age,
                gender=gender,
                condition=condition,
                admission_date=admitted_at,
                is_active=True
            )
            patients.append(patient)
        
        db.add_all(patients)
        db.commit()
        
        # 2. Refresh patients to get IDs
        for p in patients:
            db.refresh(p)
        
        # 3. Create Beds (40 beds across wards)
        print("Creating 40 beds...")
        beds = []
        bed_counter = 1
        for ward in WARDS:
            for _ in range(8):  # 8 beds per ward
                beds.append(
                    Bed(
                        ward=ward,
                        bed_number=f"{ward[:1]}-{bed_counter:02d}",
                        is_occupied=False
                    )
                )
                bed_counter += 1
        db.add_all(beds)
        db.commit()
        
        # 4. Create Admissions & Assign Beds
        print("Creating admissions and assigning beds...")
        admissions = []
        discharge_predictions = []
        active_patients = random.sample(patients, min(35, len(patients)))  # 35 active
        
        for patient in patients:
            is_active = patient in active_patients
            admitted_at = patient.admission_date
            department = random.choice(DEPARTMENTS)
            doctor = random.choice(DOCTORS)
            los = get_expected_los(patient.condition)
            predicted_discharge = admitted_at + timedelta(days=los)
            
            # Assign a bed if active
            assigned_bed = None
            if is_active:
                available_beds = [b for b in beds if not b.is_occupied]
                if available_beds:
                    assigned_bed = random.choice(available_beds)
                    assigned_bed.is_occupied = True
                    assigned_bed.patient_id = patient.id
            
            admission = Admission(
                patient_id=patient.id,
                admission_type=random.choice(ADMISSION_TYPES),
                department=department,
                bed_number=assigned_bed.bed_number if assigned_bed else None,
                doctor_in_charge=doctor,
                admission_date=admitted_at,
                discharge_date=None if is_active else admitted_at + timedelta(days=los + random.randint(0, 3)),
                notes=fake.paragraph(nb_sentences=3),
                is_discharged=not is_active
            )
            admissions.append(admission)
            
            # Create discharge prediction
            prediction = DischargePrediction(
                patient_id=patient.id,
                prediction_date=admitted_at + timedelta(days=1),
                predicted_discharge_date=predicted_discharge,
                confidence_score=round(random.uniform(0.65, 0.95), 2),
                factors=f'["{patient.condition}", "Age: {patient.age}", "Comorbidities: None"]',
                actual_discharge_date=None if is_active else admitted_at + timedelta(days=los + random.randint(0, 3))
            )
            discharge_predictions.append(prediction)
        
        db.add_all(admissions)
        db.add_all(discharge_predictions)
        db.commit()
        
        # 5. Summary
        print("\n" + "="*50)
        print("DATABASE SEEDING COMPLETE!")
        print("="*50)
        print(f"Patients created:   {len(patients)}")
        print(f"Beds created:       {len(beds)}")
        print(f"Admissions:         {len(admissions)}")
        print(f"Predictions:        {len(discharge_predictions)}")
        print(f"Active Patients:    {len(active_patients)}")
        print(f"Occupied Beds:      {len([b for b in beds if b.is_occupied])}")
        print("="*50)

# ========== Main ==========
if __name__ == "__main__":
    # Clear old data if you want a fresh start
    # clear_data()  # Uncomment if you want to reset each time
    
    # Seed the database
    seed_database(num_patients=120)