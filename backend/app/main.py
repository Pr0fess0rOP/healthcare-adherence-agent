import json
import os
from datetime import datetime, timezone

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine, get_db
from app.models import Patient, AgentRun, Notification, AuditLog
from app.schemas import ReviewRequest
from app.workflow.adherence_graph import build_adherence_graph
from app.services.audit_service import create_audit_log
from app.services.notification_service import queue_notification, update_notification_status

Base.metadata.create_all(bind=engine)

app = FastAPI(title="HealthAgent Multi-Agent API")

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
    return {"message": "HealthAgent API is running"}


@app.get("/patients")
def get_patients(db: Session = Depends(get_db)):
    patients = db.query(Patient).all()

    create_audit_log(
        db=db,
        action="PATIENTS_LISTED",
        entity_type="patient",
        details={"count": len(patients)},
    )

    return [
        {
            "id": patient.id,
            "patient_id": patient.patient_id,
            "age": patient.age,
            "medication": patient.medication,
            "last_refill_days_ago": patient.last_refill_days_ago,
            "supply_days": patient.supply_days,
            "missed_doses_last_30_days": patient.missed_doses_last_30_days,
            "prior_non_adherence": patient.prior_non_adherence,
            "preferred_contact": patient.preferred_contact,
        }
        for patient in patients
    ]


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

    refill_status = result.get("refill", {}).get("refill_status", "not_checked")
    escalation = result.get(
        "escalation",
        {
            "escalate": False,
            "priority": "normal",
            "reason": "Escalation not required",
        },
    )

    review_status = "pending" if escalation["escalate"] else "not_required"

    agent_run = AgentRun(
        patient_id=patient.patient_id,
        risk_score=result["risk"]["risk_score"],
        risk_level=result["risk"]["risk_level"],
        refill_status=refill_status,
        escalate=escalation["escalate"],
        priority=escalation["priority"],
        review_status=review_status,
        full_trace=result,
    )

    db.add(agent_run)
    db.commit()
    db.refresh(agent_run)

    # Queue notification from Reminder Agent
    if "reminder" in result:
        notification = queue_notification(
            db=db,
            patient_id=patient.patient_id,
            agent_run_id=agent_run.id,
            channel=result["reminder"]["channel"],
            message=result["reminder"]["message"],
        )

        create_audit_log(
            db=db,
            action="NOTIFICATION_QUEUED",
            entity_type="notification",
            entity_id=str(notification.id),
            details={
                "patient_id": patient.patient_id,
                "agent_run_id": agent_run.id,
                "channel": notification.channel,
            },
        )

    create_audit_log(
        db=db,
        action="ADHERENCE_CHECK_RUN",
        entity_type="agent_run",
        entity_id=str(agent_run.id),
        details={
            "patient_id": patient.patient_id,
            "risk_level": result["risk"]["risk_level"],
            "risk_score": result["risk"]["risk_score"],
            "refill_status": refill_status,
            "escalate": escalation["escalate"],
            "review_status": review_status,
            "workflow_type": "conditional_langgraph",
        },
    )

    return result


@app.get("/agent-runs")
def get_agent_runs(db: Session = Depends(get_db)):
    runs = db.query(AgentRun).order_by(AgentRun.created_at.desc()).all()

    return [
        {
            "id": run.id,
            "patient_id": run.patient_id,
            "risk_score": run.risk_score,
            "risk_level": run.risk_level,
            "refill_status": run.refill_status,
            "escalate": run.escalate,
            "priority": run.priority,
            "review_status": run.review_status,
            "review_notes": run.review_notes,
            "reviewed_at": run.reviewed_at,
            "full_trace": run.full_trace,
            "created_at": run.created_at,
        }
        for run in runs
    ]

@app.patch("/agent-runs/{run_id}/review")
def review_agent_run(
    run_id: int,
    review: ReviewRequest,
    db: Session = Depends(get_db),
):
    if review.review_status not in ["approved", "rejected"]:
        raise HTTPException(
            status_code=400,
            detail="review_status must be either approved or rejected",
        )

    agent_run = db.query(AgentRun).filter(AgentRun.id == run_id).first()

    if not agent_run:
        raise HTTPException(status_code=404, detail="Agent run not found")

    if agent_run.review_status == "not_required":
        raise HTTPException(
            status_code=400,
            detail="This agent run does not require review",
        )

    agent_run.review_status = review.review_status
    agent_run.review_notes = review.review_notes
    agent_run.reviewed_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(agent_run)

    create_audit_log(
        db=db,
        action="ESCALATION_REVIEWED",
        entity_type="agent_run",
        entity_id=str(agent_run.id),
        details={
            "patient_id": agent_run.patient_id,
            "review_status": review.review_status,
            "review_notes": review.review_notes,
        },
    )

    return agent_run


@app.get("/dashboard/summary")
def get_dashboard_summary(db: Session = Depends(get_db)):
    total_patients = db.query(Patient).count()
    total_agent_runs = db.query(AgentRun).count()

    high_risk_runs = db.query(AgentRun).filter(AgentRun.risk_level == "high").count()
    medium_risk_runs = db.query(AgentRun).filter(AgentRun.risk_level == "medium").count()
    low_risk_runs = db.query(AgentRun).filter(AgentRun.risk_level == "low").count()

    pending_reviews = db.query(AgentRun).filter(AgentRun.review_status == "pending").count()
    approved_reviews = db.query(AgentRun).filter(AgentRun.review_status == "approved").count()
    rejected_reviews = db.query(AgentRun).filter(AgentRun.review_status == "rejected").count()

    queued_notifications = db.query(Notification).filter(Notification.status == "queued").count()

    return {
        "total_patients": total_patients,
        "total_agent_runs": total_agent_runs,
        "high_risk_runs": high_risk_runs,
        "medium_risk_runs": medium_risk_runs,
        "low_risk_runs": low_risk_runs,
        "pending_reviews": pending_reviews,
        "approved_reviews": approved_reviews,
        "rejected_reviews": rejected_reviews,
        "queued_notifications": queued_notifications,
    }


@app.get("/notifications")
def get_notifications(db: Session = Depends(get_db)):
    return db.query(Notification).order_by(Notification.created_at.desc()).all()


@app.post("/notifications/{notification_id}/mark-sent")
def mark_notification_sent(notification_id: int, db: Session = Depends(get_db)):
    notification = update_notification_status(
        db=db,
        notification_id=notification_id,
        status="sent",
    )

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    create_audit_log(
        db=db,
        action="NOTIFICATION_SENT",
        entity_type="notification",
        entity_id=str(notification.id),
        details={
            "patient_id": notification.patient_id,
            "channel": notification.channel,
        },
    )

    return notification


@app.post("/notifications/{notification_id}/mark-failed")
def mark_notification_failed(notification_id: int, db: Session = Depends(get_db)):
    notification = update_notification_status(
        db=db,
        notification_id=notification_id,
        status="failed",
    )

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    create_audit_log(
        db=db,
        action="NOTIFICATION_FAILED",
        entity_type="notification",
        entity_id=str(notification.id),
        details={
            "patient_id": notification.patient_id,
            "channel": notification.channel,
        },
    )

    return notification


@app.get("/model/metrics")
def get_model_metrics():
    metrics_path = os.path.join(
        os.path.dirname(__file__),
        "ml",
        "model_metrics.json",
    )

    if not os.path.exists(metrics_path):
        raise HTTPException(status_code=404, detail="Model metrics file not found")

    with open(metrics_path, "r", encoding="utf-8") as file:
        return json.load(file)


@app.get("/audit-logs")
def get_audit_logs(db: Session = Depends(get_db)):
    return db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(100).all()


@app.get("/patients/{patient_id}/risk-history")
def get_patient_risk_history(patient_id: str, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    runs = (
        db.query(AgentRun)
        .filter(AgentRun.patient_id == patient_id)
        .order_by(AgentRun.created_at.asc())
        .all()
    )

    return [
        {
            "id": run.id,
            "patient_id": run.patient_id,
            "created_at": run.created_at,
            "risk_score": run.risk_score,
            "risk_level": run.risk_level,
            "refill_status": run.refill_status,
            "escalate": run.escalate,
            "priority": run.priority,
            "review_status": run.review_status,
        }
        for run in runs
    ]