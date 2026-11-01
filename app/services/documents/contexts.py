"""Where a document belongs: company, project, person, equipment, supplier, subcontractor or customer.

Every context is resolved inside the organization; anything else is "not found" (the route answers 404, never 403,
so another organization's records are not revealed). Suppliers are shared across organizations: a supplier context
is allowed only for a supplier this organization has an active account with (contractor_supplier_accounts).
Person documents belong to the People & Access record (user_memberships; ruling D1).
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Optional

from flask import has_request_context, url_for

from app import db
from app.models.documents import (
    CONTEXT_COLUMNS,
    CONTEXT_COMPANY,
    CONTEXT_CUSTOMER,
    CONTEXT_EQUIPMENT,
    CONTEXT_KINDS,
    CONTEXT_PERSON,
    CONTEXT_PROJECT,
    CONTEXT_SUBCONTRACTOR,
    CONTEXT_SUPPLIER,
    DocumentLink,
)

CONTEXT_LABELS = {
    CONTEXT_COMPANY: "Company",
    CONTEXT_PROJECT: "Project",
    CONTEXT_PERSON: "Person",
    CONTEXT_EQUIPMENT: "Equipment",
    CONTEXT_SUPPLIER: "Supplier",
    CONTEXT_SUBCONTRACTOR: "Subcontractor",
    CONTEXT_CUSTOMER: "Customer",
}


class DocumentNotFound(LookupError):
    """The document, context or record is not in this organization (or not visible): the route answers 404."""


@dataclass(frozen=True)
class Context:
    kind: str
    target_id: Optional[int]
    label: str
    url: Optional[str] = None

    @property
    def kind_label(self):
        return CONTEXT_LABELS.get(self.kind, self.kind.title())


def _url(endpoint, **values):
    if not has_request_context():
        return None
    try:
        return url_for(endpoint, **values)
    except Exception:  # noqa: BLE001 - a label never breaks a page
        return None


def supplier_ids_for_org(organization_id) -> set:
    from app.models.supplier_catalogue import ContractorSupplierAccount

    return {row[0] for row in db.session.query(ContractorSupplierAccount.supplier_id).filter(
        ContractorSupplierAccount.organization_id == organization_id,
        ContractorSupplierAccount.status == "ACTIVE").distinct()}


def _person_label(membership) -> str:
    from app.models.user import User

    user = db.session.get(User, membership.user_id)
    return (user.display_name or user.email) if user is not None else f"Person {membership.id}"


def resolve_context(organization_id: str, kind: str, target_id=None) -> Context:
    """The context, checked against this organization. Raises DocumentNotFound."""
    from app.models import Client, Project
    from app.models.equipment import OrganizationEquipment
    from app.models.subcontractor import Subcontractor
    from app.models.supplier_catalogue import Supplier
    from app.models.user import UserMembership

    kind = (kind or "").upper()
    if kind not in CONTEXT_KINDS:
        raise DocumentNotFound(kind)
    if kind == CONTEXT_COMPANY:
        return Context(kind, None, "Company library", _url("documents.library"))
    try:
        target_id = int(target_id)
    except (TypeError, ValueError) as exc:
        raise DocumentNotFound(kind) from exc
    if kind == CONTEXT_PROJECT:
        row = Project.query.filter_by(id=target_id, organization_id=organization_id).first()
        if row is None:
            raise DocumentNotFound(kind)
        number = (row.project_number or "").strip()
        return Context(kind, row.id, f"{row.name}" + (f" ({number})" if number else ""),
                       _url("documents.project_documents", project_id=row.id))
    if kind == CONTEXT_CUSTOMER:
        row = Client.query.filter_by(id=target_id, organization_id=organization_id).first()
        if row is None:
            raise DocumentNotFound(kind)
        return Context(kind, row.id, row.name, _url("documents.customer_documents", client_id=row.id))
    if kind == CONTEXT_SUBCONTRACTOR:
        row = Subcontractor.query.filter_by(id=target_id, organization_id=organization_id).first()
        if row is None:
            raise DocumentNotFound(kind)
        return Context(kind, row.id, row.legal_name, _url("documents.subcontractor_documents", subcontractor_id=row.id))
    if kind == CONTEXT_EQUIPMENT:
        row = OrganizationEquipment.query.filter_by(id=target_id, organization_id=organization_id).first()
        if row is None:
            raise DocumentNotFound(kind)
        return Context(kind, row.id, row.label, _url("equipment.detail", equipment_id=row.id))
    if kind == CONTEXT_PERSON:
        row = UserMembership.query.filter_by(id=target_id, organization_id=organization_id).first()
        if row is None:
            raise DocumentNotFound(kind)
        return Context(kind, row.id, _person_label(row), _url("documents.person_documents", membership_id=row.id))
    if kind == CONTEXT_SUPPLIER:
        if target_id not in supplier_ids_for_org(organization_id):
            raise DocumentNotFound(kind)
        row = db.session.get(Supplier, target_id)
        if row is None:
            raise DocumentNotFound(kind)
        return Context(kind, row.id, row.legal_name, _url("documents.supplier_documents", supplier_id=row.id))
    raise DocumentNotFound(kind)


def link_filter(query, context: Context):
    """Restrict a DocumentLink query to this context."""
    query = query.filter(DocumentLink.context_kind == context.kind)
    column = CONTEXT_COLUMNS.get(context.kind)
    if column:
        query = query.filter(getattr(DocumentLink, column) == context.target_id)
    return query


def _labels_by_kind(organization_id, ids_by_kind) -> dict:
    """{(kind, id): label} in a fixed number of queries."""
    from app.models import Client, Project
    from app.models.equipment import OrganizationEquipment
    from app.models.subcontractor import Subcontractor
    from app.models.supplier_catalogue import Supplier
    from app.models.user import User, UserMembership

    out = {}
    if ids_by_kind.get(CONTEXT_PROJECT):
        for row in Project.query.filter(Project.id.in_(ids_by_kind[CONTEXT_PROJECT])).all():
            number = (row.project_number or "").strip()
            out[(CONTEXT_PROJECT, row.id)] = row.name + (f" ({number})" if number else "")
    if ids_by_kind.get(CONTEXT_CUSTOMER):
        for row in Client.query.filter(Client.id.in_(ids_by_kind[CONTEXT_CUSTOMER])).all():
            out[(CONTEXT_CUSTOMER, row.id)] = row.name
    if ids_by_kind.get(CONTEXT_SUBCONTRACTOR):
        for row in Subcontractor.query.filter(Subcontractor.id.in_(ids_by_kind[CONTEXT_SUBCONTRACTOR])).all():
            out[(CONTEXT_SUBCONTRACTOR, row.id)] = row.legal_name
    if ids_by_kind.get(CONTEXT_SUPPLIER):
        for row in Supplier.query.filter(Supplier.id.in_(ids_by_kind[CONTEXT_SUPPLIER])).all():
            out[(CONTEXT_SUPPLIER, row.id)] = row.legal_name
    if ids_by_kind.get(CONTEXT_EQUIPMENT):
        for row in OrganizationEquipment.query.filter(OrganizationEquipment.id.in_(ids_by_kind[CONTEXT_EQUIPMENT])).all():
            out[(CONTEXT_EQUIPMENT, row.id)] = row.label
    if ids_by_kind.get(CONTEXT_PERSON):
        rows = db.session.query(UserMembership.id, User.display_name, User.email).join(
            User, User.id == UserMembership.user_id).filter(UserMembership.id.in_(ids_by_kind[CONTEXT_PERSON])).all()
        for mid, name, email in rows:
            out[(CONTEXT_PERSON, mid)] = name or email
    return out


def _context_url(kind, target_id):
    endpoints = {
        CONTEXT_COMPANY: ("documents.library", {}),
        CONTEXT_PROJECT: ("documents.project_documents", {"project_id": target_id}),
        CONTEXT_CUSTOMER: ("documents.customer_documents", {"client_id": target_id}),
        CONTEXT_SUBCONTRACTOR: ("documents.subcontractor_documents", {"subcontractor_id": target_id}),
        CONTEXT_SUPPLIER: ("documents.supplier_documents", {"supplier_id": target_id}),
        CONTEXT_EQUIPMENT: ("equipment.detail", {"equipment_id": target_id}),
        CONTEXT_PERSON: ("documents.person_documents", {"membership_id": target_id}),
    }
    endpoint, values = endpoints[kind]
    return _url(endpoint, **values)


def labels_for_documents(organization_id, document_ids) -> dict:
    """{document_id: [(kind, label, url, link)]} for active links, in a fixed number of queries."""
    if not document_ids:
        return {}
    links = DocumentLink.query.filter(DocumentLink.document_id.in_(list(document_ids)),
                                      DocumentLink.organization_id == organization_id,
                                      DocumentLink.unlinked_at.is_(None)).order_by(
        DocumentLink.is_primary.desc(), DocumentLink.id).all()
    ids_by_kind = defaultdict(set)
    for link in links:
        if link.target_id is not None:
            ids_by_kind[link.context_kind].add(link.target_id)
    names = _labels_by_kind(organization_id, ids_by_kind)
    out = defaultdict(list)
    for link in links:
        if link.context_kind == CONTEXT_COMPANY:
            label = "Company library"
        else:
            label = names.get((link.context_kind, link.target_id), CONTEXT_LABELS.get(link.context_kind))
        out[link.document_id].append((link.context_kind, label, _context_url(link.context_kind, link.target_id), link))
    return dict(out)


def link_labels(document, *, active_only=True) -> list:
    """[(kind, label, url)] for one document."""
    rows = labels_for_documents(document.organization_id, [document.id]).get(document.id, [])
    return [(kind, label, url) for kind, label, url, _ in rows]
