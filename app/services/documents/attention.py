"""Document items for "What needs your attention" (derived live; nothing stored).

Governed basis — an item is listed only when all hold:
1. the date is CONFIRMED (a person confirmed it or typed it);
2. it belongs to the document's current version;
3. the document is ACTIVE;
4. it is an expiry, inspection-due, renewal-due or warranty-end date;
5. it falls within its reminder window (default 30 days), or has passed;
6. the viewer may see the document (sensitivity; PEOPLE only for people administrators; field crew never).

Plus two roll-ups (one item each, never one per document): dates found in files waiting to be confirmed, and
documents to review (type not confirmed, or the file is missing). No compliance rule is invented here: nothing is
listed because a document is absent.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

from flask import has_request_context, url_for
from sqlalchemy import and_, exists, or_

from app import db
from app.models.documents import (
    ACTION_DATE_KINDS,
    DATE_CONFIRMED,
    DATE_EXPIRES,
    DATE_INSPECTION_DUE,
    DATE_PROPOSED,
    DATE_RENEWAL_DUE,
    DATE_WARRANTY_ENDS,
    MISSING,
    STATUS_ACTIVE,
    TYPE_SUGGESTED,
    Document,
    DocumentDate,
    DocumentVersion,
)
from app.services.documents.access import office_scope, scope_filter
from app.services.documents.contexts import labels_for_documents
from app.services.local_time import local_today

SOON_DAYS = 14
MAX_ITEMS = 50

_PHRASES = {
    DATE_EXPIRES: ("expires", "expired", "Expires"),
    DATE_INSPECTION_DUE: ("inspection due", "inspection overdue", "Inspection due"),
    DATE_RENEWAL_DUE: ("renewal due", "renewal overdue", "Renewal due"),
    DATE_WARRANTY_ENDS: ("warranty ends", "warranty ended", "Warranty ends"),
}


def _href(endpoint, fallback, **values):
    if has_request_context():
        try:
            return url_for(endpoint, **values)
        except Exception:  # noqa: BLE001
            pass
    return fallback


def _day(d: date) -> str:
    return f"{d:%a %b} {d.day}, {d.year}"


def _severity(value: date, today: date) -> str:
    if value < today:
        return "overdue"
    if value == today:
        return "today"
    if value <= today + timedelta(days=SOON_DAYS):
        return "soon"
    return ""


def _item(*, title, who, status, due, href, action, severity, kind="documents", sort_date=None):
    """Same shape as needs_attention._item, plus title / due_date / severity / url for other callers."""
    return {"kind": kind, "what": title, "who": who, "status": status, "when": _day(due) if due else "",
            "href": href, "action": action, "urgency": severity, "sort_date": sort_date or due or date.max,
            "title": title, "due_date": due, "severity": severity, "url": href}


def document_attention_items(organization_id: str, user, today: Optional[date] = None) -> list:
    scope = office_scope(user, organization_id) if user is not None else None
    if scope is None:
        return []
    today = today or local_today()  # the office's day, not the server's (UTC) date
    horizon = today + timedelta(days=365)
    rows = (scope_filter(db.session.query(DocumentDate, Document)
                         .join(Document, Document.id == DocumentDate.document_id)
                         .join(DocumentVersion, and_(DocumentVersion.id == DocumentDate.version_id,
                                                     DocumentVersion.is_current.is_(True))), scope)
            .filter(Document.status == STATUS_ACTIVE, DocumentDate.status == DATE_CONFIRMED,
                    DocumentDate.date_kind.in_(ACTION_DATE_KINDS), DocumentDate.value <= horizon,
                    DocumentDate.organization_id == organization_id)
            .order_by(DocumentDate.value).all())
    due_rows = [(d, doc) for d, doc in rows if d.value <= today + timedelta(days=d.remind_days_before)]
    labels = labels_for_documents(organization_id, [doc.id for _, doc in due_rows[:MAX_ITEMS]])
    items = []
    for date_row, document in due_rows[:MAX_ITEMS]:
        ahead, passed, _ = _PHRASES[date_row.date_kind]
        days = (date_row.value - today).days
        if days < 0:
            status = f"{passed.capitalize()} {-days} day{'s' if days != -1 else ''} ago"
            title = f"{document.title} — {passed}"
        elif days == 0:
            status = "Today"
            title = f"{document.title} — {ahead} today"
        else:
            status = f"In {days} day{'s' if days != 1 else ''}"
            title = f"{document.title} — {ahead}"
        who = ", ".join(label for _, label, _, _ in labels.get(document.id, [])[:2])
        items.append(_item(title=title, who=who, status=status, due=date_row.value,
                           href=_href("documents.detail", f"/documents/{document.public_id}", public_id=document.public_id),
                           action="Open the document", severity=_severity(date_row.value, today)))

    current = and_(DocumentVersion.document_id == Document.id, DocumentVersion.is_current.is_(True))
    proposed = (scope_filter(Document.query, scope).filter(Document.status == STATUS_ACTIVE).filter(
        exists().where(and_(DocumentDate.document_id == Document.id, DocumentDate.status == DATE_PROPOSED,
                            DocumentDate.version_id == DocumentVersion.id, current))).count())
    if proposed:
        items.append(_item(title=f"{proposed} document{'s have' if proposed != 1 else ' has'} dates to confirm",
                           who="", status="Found in the file, not confirmed", due=None,
                           href=_href("documents.library", "/documents?dates=proposed", dates="proposed"),
                           action="Review dates", severity="", sort_date=date.max))
    review = (scope_filter(Document.query, scope).filter(Document.status == STATUS_ACTIVE).filter(or_(
        Document.type_basis == TYPE_SUGGESTED,
        exists().where(and_(current, DocumentVersion.availability == MISSING)))).count())
    if review:
        items.append(_item(title=f"{review} document{'s' if review != 1 else ''} to review",
                           who="", status="Type not confirmed or file not available", due=None,
                           href=_href("documents.library", "/documents?review=1", review="1"),
                           action="Review documents", severity="", sort_date=date.max))
    return items
