from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models import Notification


def queue_notification(
    db: Session,
    patient_id: str,
    channel: str,
    message: str,
    agent_run_id: int | None = None,
):
    notification = Notification(
        patient_id=patient_id,
        agent_run_id=agent_run_id,
        channel=channel,
        message=message,
        status="queued",
    )

    db.add(notification)
    db.commit()
    db.refresh(notification)

    return notification


def update_notification_status(
    db: Session,
    notification_id: int,
    status: str,
):
    notification = db.query(Notification).filter(Notification.id == notification_id).first()

    if not notification:
        return None

    notification.status = status
    notification.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(notification)

    return notification