from app.database import SessionLocal, Base, engine
from app.models import Patient

Base.metadata.create_all(bind=engine)

db = SessionLocal()

patients = [
    Patient(
        patient_id="P1001",
        age=45,
        medication="Metformin",
        last_refill_days_ago=22,
        supply_days=30,
        missed_doses_last_30_days=1,
        prior_non_adherence=False,
        preferred_contact="sms",
    ),
    Patient(
        patient_id="P1002",
        age=67,
        medication="Atorvastatin",
        last_refill_days_ago=41,
        supply_days=30,
        missed_doses_last_30_days=6,
        prior_non_adherence=True,
        preferred_contact="email",
    ),
    Patient(
        patient_id="P1003",
        age=58,
        medication="Lisinopril",
        last_refill_days_ago=29,
        supply_days=30,
        missed_doses_last_30_days=3,
        prior_non_adherence=False,
        preferred_contact="sms",
    ),
]

for patient in patients:
    exists = db.query(Patient).filter(Patient.patient_id == patient.patient_id).first()
    if not exists:
        db.add(patient)

db.commit()
db.close()

print("Seeded synthetic patients.")