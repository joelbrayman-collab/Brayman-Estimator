"""Shared pieces of the Magnificent Seven (25 Oct 2026): history, photos, names, amounts and dates.

Every Field quick action (Add Receipt, Need Materials, Extra Work, Confirm Delivery, Job Update) keeps its photos in
the EXISTING Field capture (field_capture_events / field_capture_originals through app/services/build.py), so the
original image is kept exactly as uploaded, shows in the Project Hub's Field Observations and is read by the same
display routes. This module only adds the shared history row and small parsing helpers.
"""

from __future__ import annotations

import re
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Iterable, Optional

from app import db
from app.models.field_operations import FieldOperationEvent
from app.services.local_time import local_today

CENT = Decimal("0.01")
MAX_PHOTOS = 6
_MONEY = re.compile(r"^\$?\s*(\d{1,9}(?:,\d{3})*|\d+)(?:\.(\d{1,2}))?$")


class FieldOperationError(ValueError):
    """A plain message for the person (shown as is)."""


def actor_label(user) -> str:
    if user is None:
        return "CalibraytAI"
    name = (getattr(user, "display_name", None) or getattr(user, "email", None) or "").strip()
    return (name or "CalibraytAI")[:150]


def record(organization_id: str, record_type: str, record_id: int, event: str, *, actor=None, detail: str = "",
           project_id: Optional[int] = None) -> FieldOperationEvent:
    row = FieldOperationEvent(
        organization_id=organization_id, record_type=record_type, record_id=int(record_id),
        project_id=project_id, event=event[:40], detail=(detail or "")[:4000] or None,
        actor_user_id=getattr(actor, "id", None), actor_name=actor_label(actor))
    db.session.add(row)
    return row


def history(organization_id: str, record_type: str, record_id: int) -> list:
    return (FieldOperationEvent.query.filter_by(organization_id=organization_id, record_type=record_type,
                                                record_id=int(record_id))
            .order_by(FieldOperationEvent.occurred_at.asc(), FieldOperationEvent.id.asc()).all())


def project_history(organization_id: str, project_id: int, limit: int = 60) -> list:
    return (FieldOperationEvent.query.filter_by(organization_id=organization_id, project_id=project_id)
            .order_by(FieldOperationEvent.occurred_at.desc(), FieldOperationEvent.id.desc()).limit(limit).all())


def parse_money(raw, label: str = "Amount", *, required: bool = False) -> Optional[Decimal]:
    text = str(raw if raw is not None else "").strip().replace(" ", "")
    if not text:
        if required:
            raise FieldOperationError(f"Enter the {label.lower()}.")
        return None
    match = _MONEY.match(text)
    if not match:
        raise FieldOperationError(f"{label}: enter dollars and cents, for example 84.75.")
    whole = match.group(1).replace(",", "")
    cents = (match.group(2) or "0").ljust(2, "0")
    return Decimal(f"{whole}.{cents}").quantize(CENT)


def parse_quantity(raw, label: str = "Quantity") -> Decimal:
    text = str(raw if raw is not None else "").strip().replace(",", "")
    try:
        value = Decimal(text)
    except (InvalidOperation, ValueError):
        raise FieldOperationError(f"{label}: enter a number, for example 12.") from None
    if not value.is_finite() or value <= 0:
        raise FieldOperationError(f"{label} must be more than zero.")
    if value > Decimal("1000000"):
        raise FieldOperationError(f"{label} is too large.")
    return value.quantize(Decimal("0.001"))


def parse_day(raw, label: str = "Date", *, required: bool = False, not_future: bool = False,
              not_past: bool = False) -> Optional[date]:
    text = (raw or "").strip() if isinstance(raw, str) else raw
    if not text:
        if required:
            raise FieldOperationError(f"Enter the {label.lower()}.")
        return None
    if isinstance(text, date):
        value = text
    else:
        try:
            value = date.fromisoformat(text)
        except ValueError:
            raise FieldOperationError(f"{label}: choose a date.") from None
    today = local_today()
    if not_future and value > today:
        raise FieldOperationError(f"{label} cannot be in the future.")
    if not_past and value < today:
        raise FieldOperationError(f"{label} cannot be before today.")
    return value


def plain_quantity(value) -> str:
    if value is None:
        return ""
    text = format(Decimal(value).normalize(), "f")
    return text


def capture_photos(project, files: Iterable, *, note: str = "", organization_id: Optional[str] = None):
    """Keep uploaded photos as one Field capture on the project (existing BUILD custody). Returns the event, or
    None when no photo was chosen. The caller commits."""
    from app.services.build import BuildServiceError, add_binary_original, add_text_original, create_field_event

    chosen = [f for f in (files or []) if f is not None and getattr(f, "filename", "")]
    if not chosen:
        return None
    if len(chosen) > MAX_PHOTOS:
        raise FieldOperationError(f"Add at most {MAX_PHOTOS} photos at a time.")
    try:
        event = create_field_event(project, organization_id=organization_id or project.organization_id)
        for upload in chosen:
            add_binary_original(event, kind="image", data=upload.read(), filename=upload.filename)
        if note.strip():
            add_text_original(event, note.strip()[:4000])
    except BuildServiceError as exc:
        db.session.rollback()
        raise FieldOperationError(str(exc) or "The photo could not be saved.") from None
    return event


def image_originals(event_id: Optional[int]) -> list:
    if not event_id:
        return []
    from app.models.build import FieldCaptureOriginal

    return (FieldCaptureOriginal.query.filter_by(field_event_id=event_id, kind="image")
            .order_by(FieldCaptureOriginal.id.asc()).all())
