import random
import math
from app.database import SessionLocal, Base, engine
from app.models import Patient

Base.metadata.create_all(bind=engine)

db = SessionLocal()

# Clinical options for synthetic patients
medications = [
    "Metformin", "Atorvastatin", "Lisinopril", "Levothyroxine", 
    "Amlodipine", "Albuterol", "Omeprazole", "Gabapentin", 
    "Losartan", "Metoprolol"
]
contact_methods = ["sms", "email"]

def get_poisson(lmbda):
    """Simple Knuth algorithm for Poisson random variable."""
    L = math.exp(-lmbda)
    k = 0
    p = 1.0
    while p > L:
        k += 1
        p *= random.random()
    return k - 1

# Generate 500 synthetic patients matching the training data distributions
patients = []
for i in range(1, 501):
    patient_id = f"P{1000 + i}"
    age = random.randint(22, 90)
    medication = random.choice(medications)
    
    # 72% 30-day supply, 18% 60-day supply, 10% 90-day supply
    supply_days = random.choices([30, 60, 90], weights=[72, 18, 10])[0]
    
    # 28% prior non-adherence rate
    prior_non_adherence = random.choices([False, True], weights=[72, 28])[0]
    
    # Generate realistic refill days based on supply and prior history
    base_refill = random.normalvariate(supply_days - 4, 12)
    if prior_non_adherence:
        base_refill += random.normalvariate(8, 6)
    last_refill_days_ago = int(max(1, min(110, round(base_refill))))
    
    # Generate missed doses via Poisson distribution mimicking drift baseline/train
    missed_base = 2
    if last_refill_days_ago > supply_days:
        missed_base += 3
    if prior_non_adherence:
        missed_base += 2
    if age >= 65:
        missed_base += random.choices([0, 1, 2], weights=[50, 35, 15])[0]
        
    missed_doses = int(max(0, min(30, get_poisson(missed_base))))
    preferred_contact = random.choice(contact_methods)
    
    patient = Patient(
        patient_id=patient_id,
        age=age,
        medication=medication,
        last_refill_days_ago=last_refill_days_ago,
        supply_days=supply_days,
        missed_doses_last_30_days=missed_doses,
        prior_non_adherence=prior_non_adherence,
        preferred_contact=preferred_contact,
    )
    patients.append(patient)

# Check and seed patients in a single transaction
seeded_count = 0
for patient in patients:
    exists = db.query(Patient).filter(Patient.patient_id == patient.patient_id).first()
    if not exists:
        db.add(patient)
        seeded_count += 1

db.commit()
db.close()

print(f"Seeded {seeded_count} new synthetic patients (total checked: 500).")