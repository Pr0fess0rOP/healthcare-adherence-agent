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

import pandas as pd
from app.ml.ml_utils import FEATURES, read_json_file, get_patient_feature_dataframe, load_cluster_assets

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
            "segment": result.get("segment", {}).get("label"),
            "intervention": result.get("intervention", {}).get("recommended_intervention"),
            "refill_status": refill_status,
            "escalate": escalation["escalate"],
            "review_status": review_status,
            "workflow_type": "conditional_langgraph_with_ml_segmentation",
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

@app.get("/model/compare")
def get_model_comparison():
    data = read_json_file("model_comparison.json")

    if not data:
        raise HTTPException(status_code=404, detail="Model comparison file not found")

    return data


@app.get("/model/feature-importance")
def get_feature_importance():
    data = read_json_file("feature_importance.json")

    if not data:
        raise HTTPException(status_code=404, detail="Feature importance file not found")

    return data


@app.get("/model/registry")
def get_model_registry():
    data = read_json_file("model_registry.json")

    if not data:
        raise HTTPException(status_code=404, detail="Model registry file not found")

    return data


@app.get("/patients/{patient_id}/explanation")
def get_patient_explanation(patient_id: str, db: Session = Depends(get_db)):
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

    return {
        "patient_id": patient_id,
        "risk": result.get("risk"),
        "segment": result.get("segment"),
        "intervention": result.get("intervention"),
        "summary": result.get("summary"),
    }


@app.get("/patients/segments")
def get_patient_segments(db: Session = Depends(get_db)):
    patients = db.query(Patient).all()

    if not patients:
        return []

    cluster_model, scaler = load_cluster_assets()

    results = []

    segment_labels = {
        0: "Stable adherence profile",
        1: "Refill delay monitor",
        2: "Missed-dose support needed",
        3: "High-touch adherence support",
    }

    for patient in patients:
        features = get_patient_feature_dataframe(patient)
        scaled = scaler.transform(features)
        cluster_id = int(cluster_model.predict(scaled)[0])

        results.append(
            {
                "patient_id": patient.patient_id,
                "medication": patient.medication,
                "segment_id": cluster_id,
                "segment": segment_labels.get(cluster_id, "General adherence monitoring"),
            }
        )

    return results


@app.get("/patients/{patient_id}/intervention")
def get_patient_intervention(patient_id: str, db: Session = Depends(get_db)):
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

    return {
        "patient_id": patient_id,
        "risk": result.get("risk"),
        "segment": result.get("segment"),
        "intervention": result.get("intervention"),
    }


@app.get("/patients/{patient_id}/risk-forecast")
def get_patient_risk_forecast(patient_id: str, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    runs = (
        db.query(AgentRun)
        .filter(AgentRun.patient_id == patient_id)
        .order_by(AgentRun.created_at.asc())
        .all()
    )

    if not runs:
        return {
            "patient_id": patient_id,
            "current_risk": None,
            "forecast_14_day_risk": None,
            "trend": "insufficient_history",
            "message": "Run at least one adherence check first.",
        }

    current_risk = float(runs[-1].risk_score)

    if len(runs) >= 2:
        previous_risk = float(runs[-2].risk_score)
        delta = current_risk - previous_risk
    else:
        refill_delay = max(0, patient.last_refill_days_ago - patient.supply_days)
        delta = 0.04 if refill_delay > 0 or patient.missed_doses_last_30_days >= 5 else -0.02

    forecast = max(0.0, min(1.0, current_risk + delta))

    if forecast > current_risk + 0.03:
        trend = "increasing"
    elif forecast < current_risk - 0.03:
        trend = "decreasing"
    else:
        trend = "stable"

    return {
        "patient_id": patient_id,
        "current_risk": round(current_risk, 2),
        "forecast_14_day_risk": round(forecast, 2),
        "trend": trend,
        "method": "simple trend + refill/missed-dose heuristic",
    }


@app.get("/model/drift")
def get_model_drift(db: Session = Depends(get_db)):
    baseline = read_json_file("drift_baseline.json")

    if not baseline:
        raise HTTPException(status_code=404, detail="Drift baseline file not found")

    patients = db.query(Patient).all()

    if not patients:
        return {
            "drift_detected": False,
            "drifted_features": [],
            "message": "No patient data available for drift check.",
        }

    live_rows = []

    for patient in patients:
        live_rows.append(
            {
                "age": patient.age,
                "last_refill_days_ago": patient.last_refill_days_ago,
                "supply_days": patient.supply_days,
                "missed_doses_last_30_days": patient.missed_doses_last_30_days,
                "prior_non_adherence": int(patient.prior_non_adherence),
            }
        )

    live_df = pd.DataFrame(live_rows, columns=FEATURES)

    drifted_features = []
    feature_checks = []

    for feature in FEATURES:
        live_mean = float(live_df[feature].mean())
        train_mean = float(baseline[feature]["mean"])
        train_std = max(float(baseline[feature]["std"]), 1e-6)

        z_delta = abs(live_mean - train_mean) / train_std
        drifted = z_delta >= 1.5

        if drifted:
            drifted_features.append(feature)

        feature_checks.append(
            {
                "feature": feature,
                "training_mean": round(train_mean, 4),
                "live_mean": round(live_mean, 4),
                "z_delta": round(z_delta, 4),
                "drifted": drifted,
            }
        )

    return {
        "drift_detected": len(drifted_features) > 0,
        "drifted_features": drifted_features,
        "feature_checks": feature_checks,
        "recommendation": (
            "Retrain model with newer data distribution."
            if drifted_features
            else "No major drift detected."
        ),
    }