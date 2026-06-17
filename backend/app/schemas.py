from pydantic import BaseModel
from typing import Any, Optional
from datetime import datetime


class PatientResponse(BaseModel):
    patient_id: str
    age: int
    medication: str
    last_refill_days_ago: int
    supply_days: int
    missed_doses_last_30_days: int
    prior_non_adherence: bool
    preferred_contact: str

    class Config:
        from_attributes = True


class AgentRunResponse(BaseModel):
    id: int
    patient_id: str
    risk_score: float
    risk_level: str
    refill_status: str
    escalate: bool
    priority: str
    review_status: str
    review_notes: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    full_trace: dict[str, Any]
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ReviewRequest(BaseModel):
    review_status: str  # approved or rejected
    review_notes: Optional[str] = None


class DashboardSummary(BaseModel):
    total_patients: int
    total_agent_runs: int
    high_risk_runs: int
    medium_risk_runs: int
    low_risk_runs: int
    pending_reviews: int
    approved_reviews: int
    rejected_reviews: int
    queued_notifications: int


class NotificationResponse(BaseModel):
    id: int
    patient_id: str
    agent_run_id: Optional[int] = None
    channel: str
    message: str
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AuditLogResponse(BaseModel):
    id: int
    action: str
    entity_type: str
    entity_id: Optional[str] = None
    details: Optional[dict[str, Any]] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True