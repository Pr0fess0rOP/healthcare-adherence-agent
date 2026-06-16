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
    full_trace = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())