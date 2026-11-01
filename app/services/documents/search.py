"""Browse, filter and search documents (paged in SQL; no file bytes or text are loaded for lists).

Search uses the SQLite FTS5 index when this database has it (ranked by bm25, with a highlighted snippet) and a LIKE
fallback otherwise (same filters, newest first). The viewer's scope (organization, sensitivity, field restriction)
is applied in SQL to the rows and to the count, so a count never includes a document the viewer cannot open.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Optional

from markupsafe import Markup, escape
from sqlalchemy import Float, Integer, String, and_, exists, func, or_, select, text

from app import db
from app.models.documents import (
    ACTION_DATE_KINDS,
    CONTEXT_COLUMNS,
    CONTEXT_COMPANY,
    CONTEXT_CUSTOMER,
    CONTEXT_EQUIPMENT,
    CONTEXT_KINDS,
    CONTEXT_PERSON,
    CONTEXT_PROJECT,
    CONTEXT_SUBCONTRACTOR,
    CONTEXT_SUPPLIER,
    DATE_CONFIRMED,
    DATE_PROPOSED,
    MISSING,
    STATUS_ACTIVE,
    STATUS_ARCHIVED,
    TYPE_SUGGESTED,
    Document,
    DocumentDate,
    DocumentLink,
    DocumentText,
    DocumentVersion,
)
from app.services.documents import fts
from app.services.documents.access import Scope, scope_filter
from app.services.documents.contexts import labels_for_documents
from app.services.documents.types import REGISTRY, type_label

PAGE_SIZE = 50
MAX_OFFSET = 2000
MAX_TERMS = 8
_TERM_RE = re.compile(r"\w+", re.UNICODE)
_MARK_OPEN, _MARK_CLOSE = "", ""


@dataclass
class Filters:
    q: str = ""
    type_code: str = ""
    family: str = ""
    context_kind: str = ""
    context_id: Optional[int] = None
    status: str = STATUS_ACTIVE  # ACTIVE | ARCHIVED | ALL
    uploaded_from: Optional[date] = None
    uploaded_to: Optional[date] = None
    expiring_within: Optional[int] = None  # confirmed action dates within N days (overdue included)
    dates: str = ""  # proposed | expired | none
    review: bool = False

    @classmethod
    def from_args(cls, args):
        def _date(name):
            try:
                return date.fromisoformat((args.get(name) or "").strip())
            except ValueError:
                return None

        def _int(name, limit=3650):
            try:
                value = int((args.get(name) or "").strip())
            except ValueError:
                return None
            return value if 0 <= value <= limit else None

        status = (args.get("status") or STATUS_ACTIVE).upper()
        kind = (args.get("context") or "").upper()
        return cls(q=(args.get("q") or "").strip()[:200], type_code=(args.get("type") or "").strip()[:60],
                   family=(args.get("family") or "").strip()[:40],
                   context_kind=kind if kind in CONTEXT_KINDS else "", context_id=_int("context_id", 2**31 - 1),
                   status=status if status in (STATUS_ACTIVE, STATUS_ARCHIVED, "ALL") else STATUS_ACTIVE,
                   uploaded_from=_date("from"), uploaded_to=_date("to"), expiring_within=_int("expiring"),
                   dates=(args.get("dates") or "").strip().lower()[:20], review=(args.get("review") or "") == "1")


@dataclass
class Row:
    document: Document
    version_number: Optional[int]
    filename: str
    media_type: str
    byte_size: int
    availability: str
    source_kind: str
    dates: list = field(default_factory=list)
    proposed: int = 0
    labels: list = field(default_factory=list)
    snippet: Optional[Markup] = None

    @property
    def type_label(self):
        return type_label(self.document.document_type)


@dataclass
class Page:
    rows: list
    total: int
    page: int
    page_size: int
    mode: str  # "fts" | "like" | "browse"

    @property
    def pages(self):
        return max(1, (self.total + self.page_size - 1) // self.page_size)

    @property
    def has_next(self):
        return self.page < self.pages and self.page * self.page_size < MAX_OFFSET + self.page_size

    @property
    def has_prev(self):
        return self.page > 1


def terms(q: str) -> list:
    return [t.lower() for t in _TERM_RE.findall(q or "")][:MAX_TERMS]


def fts_match_expression(q: str) -> str:
    """Every term quoted (FTS syntax such as NEAR, -, :, * or quotes in the user's text has no effect)."""
    return " ".join('"' + t.replace('"', "") + '"*' for t in terms(q))


def _on_current_version():
    """DocumentDate rows of the document's current version (both tables in the EXISTS; Document correlated)."""
    return and_(DocumentDate.document_id == Document.id, DocumentVersion.id == DocumentDate.version_id,
                DocumentVersion.is_current.is_(True))


def _action_dates_condition(*, until: Optional[date] = None, before: Optional[date] = None):
    condition = and_(_on_current_version(), DocumentDate.status == DATE_CONFIRMED,
                     DocumentDate.date_kind.in_(ACTION_DATE_KINDS))
    if until is not None:
        condition = and_(condition, DocumentDate.value <= until)
    if before is not None:
        condition = and_(condition, DocumentDate.value < before)
    return exists().where(condition)


def _apply_filters(query, filters: Filters, today: date):
    if filters.status in (STATUS_ACTIVE, STATUS_ARCHIVED):
        query = query.filter(Document.status == filters.status)
    if filters.type_code:
        query = query.filter(Document.document_type == filters.type_code)
    if filters.family:
        codes = [t.code for t in REGISTRY if t.family == filters.family]
        query = query.filter(Document.document_type.in_(codes or ["-"]))
    if filters.context_kind:
        condition = and_(DocumentLink.document_id == Document.id, DocumentLink.unlinked_at.is_(None),
                         DocumentLink.context_kind == filters.context_kind)
        column = CONTEXT_COLUMNS.get(filters.context_kind)
        if column and filters.context_id is not None:
            condition = and_(condition, getattr(DocumentLink, column) == filters.context_id)
        query = query.filter(exists().where(condition))
    if filters.uploaded_from:
        query = query.filter(Document.created_at >= datetime.combine(filters.uploaded_from, datetime.min.time()))
    if filters.uploaded_to:
        query = query.filter(Document.created_at < datetime.combine(filters.uploaded_to + timedelta(days=1),
                                                                    datetime.min.time()))
    if filters.expiring_within is not None:
        query = query.filter(_action_dates_condition(until=today + timedelta(days=filters.expiring_within)))
    if filters.dates == "expired":
        query = query.filter(_action_dates_condition(before=today))
    elif filters.dates == "proposed":
        query = query.filter(exists().where(and_(_on_current_version(), DocumentDate.status == DATE_PROPOSED)))
    elif filters.dates == "none":
        query = query.filter(~exists().where(and_(_on_current_version(), DocumentDate.status == DATE_CONFIRMED)))
    if filters.review:
        query = query.filter(or_(Document.type_basis == TYPE_SUGGESTED, exists().where(and_(
            DocumentVersion.document_id == Document.id, DocumentVersion.is_current.is_(True),
            DocumentVersion.availability == MISSING))))
    return query


def _like_term_condition(term: str):
    from app.models import Client, Project
    from app.models.equipment import OrganizationEquipment
    from app.models.subcontractor import Subcontractor
    from app.models.supplier_catalogue import Supplier
    from app.models.user import User, UserMembership

    pattern = f"%{term}%"
    current = and_(DocumentVersion.document_id == Document.id, DocumentVersion.is_current.is_(True))
    active_link = and_(DocumentLink.document_id == Document.id, DocumentLink.unlinked_at.is_(None))

    def linked(model, column, name_column, kind):
        return exists().where(and_(active_link, DocumentLink.context_kind == kind,
                                   getattr(DocumentLink, column) == model.id, func.lower(name_column).like(pattern)))

    return or_(
        func.lower(Document.title).like(pattern),
        func.lower(func.coalesce(Document.keywords, "")).like(pattern),
        func.lower(func.coalesce(Document.reference_number, "")).like(pattern),
        func.lower(func.coalesce(Document.counterparty, "")).like(pattern),
        exists().where(and_(current, func.lower(DocumentVersion.original_filename).like(pattern))),
        exists().where(and_(current, DocumentText.version_id == DocumentVersion.id,
                            func.lower(func.coalesce(DocumentText.body, "")).like(pattern))),
        linked(Project, "project_id", Project.name, CONTEXT_PROJECT),
        linked(Client, "client_id", Client.name, CONTEXT_CUSTOMER),
        linked(Subcontractor, "subcontractor_id", Subcontractor.legal_name, CONTEXT_SUBCONTRACTOR),
        linked(Supplier, "supplier_id", Supplier.legal_name, CONTEXT_SUPPLIER),
        linked(OrganizationEquipment, "equipment_id", OrganizationEquipment.name, CONTEXT_EQUIPMENT),
        exists().where(and_(active_link, DocumentLink.context_kind == CONTEXT_PERSON,
                            DocumentLink.membership_id == UserMembership.id, UserMembership.user_id == User.id,
                            func.lower(func.coalesce(User.display_name, "")).like(pattern))),
    )


def _snippet(raw: Optional[str]) -> Optional[Markup]:
    if not raw:
        return None
    safe = str(escape(raw))
    return Markup(safe.replace(_MARK_OPEN, "<mark>").replace(_MARK_CLOSE, "</mark>"))


def search(scope: Scope, filters: Filters, *, page: int = 1, page_size: int = PAGE_SIZE,
           today: Optional[date] = None, mode: Optional[str] = None) -> Page:
    today = today or date.today()
    page = max(1, int(page or 1))
    offset = min((page - 1) * page_size, MAX_OFFSET)
    words = terms(filters.q)
    use_fts = bool(words) and (mode == "fts" or (mode is None and fts.fts_enabled()))
    if mode == "fts" and not fts.fts_enabled():
        use_fts = False
    snippets = {}
    if use_fts:
        sub = text(
            "SELECT rowid AS doc_id, bm25(document_search, 0, 0, 0, 10.0, 5.0, 3.0, 2.0, 1.0) AS rank, "
            f"snippet(document_search, -1, '{_MARK_OPEN}', '{_MARK_CLOSE}', '…', 12) AS snip "
            "FROM document_search WHERE document_search MATCH :match AND organization_id = :org"
        ).columns(doc_id=Integer, rank=Float, snip=String).subquery("hits")
        base = (db.session.query(Document, sub.c.rank, sub.c.snip).join(sub, sub.c.doc_id == Document.id))
        base = _apply_filters(scope_filter(base, scope), filters, today).params(
            match=fts_match_expression(filters.q), org=scope.organization_id)
        total = base.order_by(None).count()
        rows = base.order_by(sub.c.rank, Document.created_at.desc(), Document.id.desc()).offset(offset).limit(
            page_size).all()
        documents = [r[0] for r in rows]
        snippets = {r[0].id: _snippet(r[2]) for r in rows}
        result_mode = "fts"
    else:
        base = _apply_filters(scope_filter(Document.query, scope), filters, today)
        for word in words:
            base = base.filter(_like_term_condition(word))
        total = base.order_by(None).count()
        documents = base.order_by(Document.created_at.desc(), Document.id.desc()).offset(offset).limit(page_size).all()
        result_mode = "like" if words else "browse"
    return Page(_rows(scope.organization_id, documents, snippets), total, page, page_size, result_mode)


def _rows(organization_id, documents, snippets=None) -> list:
    if not documents:
        return []
    ids = [d.id for d in documents]
    versions = {}
    for row in db.session.query(DocumentVersion.document_id, DocumentVersion.id, DocumentVersion.version_number,
                                DocumentVersion.original_filename, DocumentVersion.media_type,
                                DocumentVersion.byte_size, DocumentVersion.availability,
                                DocumentVersion.source_kind).filter(
            DocumentVersion.document_id.in_(ids), DocumentVersion.is_current.is_(True)).all():
        versions[row[0]] = row
    current_ids = [v[1] for v in versions.values()]
    dates = {}
    proposed = {}
    if current_ids:
        for d in DocumentDate.query.filter(DocumentDate.version_id.in_(current_ids),
                                           DocumentDate.status.in_((DATE_CONFIRMED, DATE_PROPOSED))).order_by(
                DocumentDate.value).all():
            if d.status == DATE_CONFIRMED:
                dates.setdefault(d.document_id, []).append(d)
            else:
                proposed[d.document_id] = proposed.get(d.document_id, 0) + 1
    labels = labels_for_documents(organization_id, ids)
    out = []
    for d in documents:
        v = versions.get(d.id)
        out.append(Row(d, v[2] if v else None, v[3] if v else "", v[4] if v else "", v[5] if v else 0,
                       v[6] if v else MISSING, v[7] if v else "", dates.get(d.id, []), proposed.get(d.id, 0),
                       [(k, label, url) for k, label, url, _ in labels.get(d.id, [])],
                       (snippets or {}).get(d.id)))
    return out


def context_rows(scope: Scope, context_kind: str, context_id=None, *, page=1, status=STATUS_ACTIVE, today=None) -> Page:
    """One context's documents (browse), newest first."""
    filters = Filters(context_kind=context_kind if context_kind != CONTEXT_COMPANY else CONTEXT_COMPANY,
                      context_id=context_id, status=status)
    return search(scope, filters, page=page, today=today)
