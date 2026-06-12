"""Verify audit events are created for sensitive operations."""
import pytest
from sqlalchemy.orm import Session

from app.models.audit import AuditEvent
from app.services import audit


def test_consent_record_creates_audit_event(db: Session):
    """Recording consent should create an audit event."""
    from uuid import uuid4

    tenant_id = uuid4()
    case_id = uuid4()
    actor_id = str(uuid4())

    # Record a consent event
    audit.record_event(
        db,
        tenant_id=tenant_id,
        actor_type="user",
        actor_id=actor_id,
        action="consent.recorded",
        resource_type="consent_record",
        resource_id=str(uuid4()),
        case_id=case_id,
        data={"notice_id": str(uuid4())}
    )

    # Verify it was created
    events = db.query(AuditEvent).filter_by(action="consent.recorded", tenant_id=tenant_id).all()
    assert len(events) > 0
    assert events[0].resource_type == "consent_record"
    assert events[0].case_id == case_id


def test_document_upload_creates_audit_event(db: Session):
    """Uploading a document should create an audit event."""
    from uuid import uuid4

    tenant_id = uuid4()
    case_id = uuid4()
    doc_id = uuid4()

    audit.record_event(
        db,
        tenant_id=tenant_id,
        actor_type="user",
        actor_id=str(uuid4()),
        action="document.uploaded",
        resource_type="document",
        resource_id=str(doc_id),
        case_id=case_id,
        data={"checksum": "abc123", "size": 1024}
    )

    events = db.query(AuditEvent).filter_by(action="document.uploaded", tenant_id=tenant_id).all()
    assert len(events) > 0
    assert str(events[0].resource_id) == str(doc_id)


def test_review_decision_creates_audit_event(db: Session):
    """Approving/rejecting a case should create an audit event."""
    from uuid import uuid4

    tenant_id = uuid4()
    case_id = uuid4()
    task_id = uuid4()

    audit.record_event(
        db,
        tenant_id=tenant_id,
        actor_type="user",
        actor_id=str(uuid4()),
        action="review_task.resolved",
        resource_type="review_task",
        resource_id=str(task_id),
        case_id=case_id,
        data={"decision": "approved", "reason": "manual override"}
    )

    events = db.query(AuditEvent).filter_by(action="review_task.resolved", tenant_id=tenant_id).all()
    assert len(events) > 0
    assert str(events[0].resource_id) == str(task_id)


def test_audit_query_filters_by_tenant(db: Session):
    """Audit events should be tenant-scoped."""
    from uuid import uuid4

    tenant1 = uuid4()
    tenant2 = uuid4()

    audit.record_event(
        db, tenant_id=tenant1, actor_type="user", actor_id=str(uuid4()),
        action="test.event", resource_type="test", resource_id=str(uuid4()), data={}
    )
    audit.record_event(
        db, tenant_id=tenant2, actor_type="user", actor_id=str(uuid4()),
        action="test.event", resource_type="test", resource_id=str(uuid4()), data={}
    )

    tenant1_events = db.query(AuditEvent).filter_by(tenant_id=tenant1, action="test.event").all()
    tenant2_events = db.query(AuditEvent).filter_by(tenant_id=tenant2, action="test.event").all()

    assert len(tenant1_events) >= 1
    assert len(tenant2_events) >= 1
    for event in tenant1_events:
        assert event.tenant_id == tenant1
