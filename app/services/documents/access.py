"""Who may see which documents, mapped onto Calibrayt's existing access model (no new capability system).

* Signed out → the office wall (login). Supplier Hub users never pass the office wall (app/__init__.py), so they
  never reach any contractor document.
* Field-only members reach only the two field document pages (allow-listed in access_domains.py); there they see
  documents linked to the jobs they work on (field_visible_project_ids) of the crew-visible types (drawings,
  specifications, instructions, safety) with STANDARD sensitivity, and nothing else.
* Office members see STANDARD documents and, with has_office_financial_access, FINANCIAL ones.
* People administrators (instance owner or System Administrator) also see PEOPLE documents and person pages.
* Any document with an active link to a person is for people administrators only, whatever its sensitivity (review
  fix I1, 1 Nov 2026: linking raises it to PEOPLE; this is the defence in depth for any row that is not).

Every filter here is applied in SQL by the list, search and attention queries, never by hiding rows in a page.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from sqlalchemy import and_, exists

from app.models.documents import (
    CONTEXT_PERSON,
    CONTEXT_PROJECT,
    SENSITIVITY_FINANCIAL,
    SENSITIVITY_PEOPLE,
    SENSITIVITY_STANDARD,
    Document,
    DocumentLink,
)
from app.services.documents.contexts import DocumentNotFound


@dataclass(frozen=True)
class Scope:
    organization_id: str
    user_id: Optional[int]
    sensitivities: tuple
    people_admin: bool = False
    field: bool = False
    project_ids: Optional[frozenset] = None  # None = no project restriction
    type_codes: Optional[frozenset] = None  # None = every type

    @property
    def can_change(self) -> bool:
        return not self.field


def is_people_admin(user, organization_id) -> bool:
    from app.services.people_access import PeopleAccessError, require_people_administrator

    try:
        require_people_administrator(user, organization_id)
    except PeopleAccessError:
        return False
    except Exception:  # noqa: BLE001 - fail closed
        return False
    return True


def office_scope(user, organization_id) -> Optional[Scope]:
    """The office view, or None for a field-only member (they get field_scope)."""
    from app.services.access_domains import has_office_financial_access, user_is_field_only

    if user is None or user_is_field_only(user, organization_id):
        return None
    sensitivities = [SENSITIVITY_STANDARD]
    if has_office_financial_access(user, organization_id):
        sensitivities.append(SENSITIVITY_FINANCIAL)
    admin = is_people_admin(user, organization_id)
    if admin:
        sensitivities.append(SENSITIVITY_PEOPLE)
    return Scope(organization_id, int(user.id), tuple(sensitivities), people_admin=admin)


def field_scope(user, organization_id) -> Scope:
    """Crew view of job documents: their jobs only, crew-visible types only, STANDARD only."""
    from app.services.access_domains import field_visible_project_ids
    from app.services.documents.types import FIELD_VISIBLE_TYPES

    visible = field_visible_project_ids(user, organization_id)
    return Scope(organization_id, int(user.id), (SENSITIVITY_STANDARD,), field=True,
                 project_ids=frozenset(visible) if visible is not None else None,
                 type_codes=FIELD_VISIBLE_TYPES)


def scope_filter(query, scope: Scope):
    """Apply the scope to a query over Document (SQL)."""
    query = query.filter(Document.organization_id == scope.organization_id,
                         Document.sensitivity.in_(scope.sensitivities))
    if scope.type_codes is not None:
        query = query.filter(Document.document_type.in_(sorted(scope.type_codes)))
    if not scope.people_admin:
        query = query.filter(~exists().where(and_(DocumentLink.document_id == Document.id,
                                                  DocumentLink.unlinked_at.is_(None),
                                                  DocumentLink.context_kind == CONTEXT_PERSON)))
    if scope.field:
        condition = and_(DocumentLink.document_id == Document.id, DocumentLink.unlinked_at.is_(None),
                         DocumentLink.context_kind == CONTEXT_PROJECT)
        if scope.project_ids is not None:
            condition = and_(condition, DocumentLink.project_id.in_(sorted(scope.project_ids)))
        query = query.filter(exists().where(condition))
    return query


def require_document(public_id: str, scope: Scope) -> Document:
    """The document if this viewer may open it; otherwise DocumentNotFound (404)."""
    if scope is None or not public_id or len(public_id) > 32:
        raise DocumentNotFound(public_id)
    document = scope_filter(Document.query, scope).filter(Document.public_id == public_id).first()
    if document is None:
        raise DocumentNotFound(public_id)
    return document


def may_see_context_kind(scope: Scope, kind: str) -> bool:
    if kind == CONTEXT_PERSON:
        return scope.people_admin
    return True
