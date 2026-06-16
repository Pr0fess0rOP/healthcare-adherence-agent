from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine, get_db
from app.models import Patient, AgentRun
from app.workflow.adherence_graph import build_adherence_graph

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Healthcare Adherence Multi-Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

adherence_graph = build_adherence_graph()


@app.get("/")
def root():
    return {"message": "Healthcare Adherence API is running"}


@app.get("/patients")
def get_patients(db: Session = Depends(get_db)):
    return db.query(Patient).all()


@app.post("/run-adherence-check/{patient_id}")
def run_adherence_check(patient_id: str, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    patient_dict = {
        "patient_id": patient.patient_id,
        "age": patient.age,
        "medication": patient.medication,
        "last_refill_days_ago": patient.last_refill_days_ago,
        "supply_days": patient.supply_days,
        "missed_doses_last_30_days": patient.missed_doses_last_30_days,
        "prior_non_adherence": patient.prior_non_adherence,
        "preferred_contact": patient.preferred_contact,
    }

    result = adherence_graph.invoke({"patient": patient_dict})

    agent_run = AgentRun(
        patient_id=patient.patient_id,
        risk_score=result["risk"]["risk_score"],
        risk_level=result["risk"]["risk_level"],
        refill_status=result["refill"]["refill_status"],
        escalate=result["escalation"]["escalate"],
        priority=result["escalation"]["priority"],
        full_trace=result,
    )

    db.add(agent_run)
    db.commit()
    db.refresh(agent_run)

    return result


@app.get("/agent-runs")
def get_agent_runs(db: Session = Depends(get_db)):
    return db.query(AgentRun).order_by(AgentRun.created_at.desc()).all()