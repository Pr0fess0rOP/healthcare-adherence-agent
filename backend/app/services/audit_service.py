from sqlalchemy.orm import Session

from app.models import AuditLog


def create_audit_log(
    db: Session,
    action: str,
    entity_type: str,
    entity_id: str | None = None,
    details: dict | None = None,
):
    audit_log = AuditLog(
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details or {},
    )

    db.add(audit_log)
    db.commit()
    db.refresh(audit_log)

    return audit_log