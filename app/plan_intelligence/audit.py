"""Append-only Plan Intelligence audit events."""

from __future__ import annotations

import json
from typing import Any, Optional

from app import db
from app.plan_intelligence.models import PlanAuditEvent


def record_plan_audit(
    *,
    project_id: int,
    event_type: str,
    plan_document_id: Optional[int] = None,
    sheet_id: Optional[int] = None,
    extraction_run_id: Optional[int] = None,
    takeoff_candidate_id: Optional[int] = None,
    takeoff_package_id: Optional[int] = None,
    detail: Optional[Any] = None,
    commit: bool = False,
):
    """Append an audit event. Never update or delete prior events."""
    if detail is None:
        detail_text = None
    elif isinstance(detail, str):
        detail_text = detail
    else:
        detail_text = json.dumps(detail, default=str)

    event = PlanAuditEvent(
        project_id=project_id,
        plan_document_id=plan_document_id,
        sheet_id=sheet_id,
        extraction_run_id=extraction_run_id,
        takeoff_candidate_id=takeoff_candidate_id,
        takeoff_package_id=takeoff_package_id,
        event_type=event_type,
        detail=detail_text,
    )
    db.session.add(event)
    if commit:
        db.session.commit()
    return event
