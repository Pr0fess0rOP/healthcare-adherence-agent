from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, JSON, ForeignKey
from sqlalchemy.sql import func

from app.database import Base


class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String, unique=True, index=True)
    age = Column(Integer)
    medication = Column(String)
    last_refill_days_ago = Column(Integer)
    supply_days = Column(Integer)
    missed_doses_last_30_days = Column(Integer)
    prior_non_adherence = Column(Boolean)
    preferred_contact = Column(String)


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String, ForeignKey("patients.patient_id"))

    risk_score = Column(Float)
    risk_level = Column(String)
    refill_status = Column(String)
    escalate = Column(Boolean)
    priority = Column(String)

    # Human-in-the-loop review
    review_status = Column(String, default="not_required")  
    # values: not_required, pending, approved, rejected

    review_notes = Column(String, nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)

    full_trace = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String, index=True)
    agent_run_id = Column(Integer, ForeignKey("agent_runs.id"), nullable=True)

    channel = Column(String)  # sms, email
    message = Column(String)
    status = Column(String, default="queued")  # queued, sent, failed

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)

    action = Column(String, index=True)
    entity_type = Column(String, index=True)
    entity_id = Column(String, nullable=True)
    details = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())