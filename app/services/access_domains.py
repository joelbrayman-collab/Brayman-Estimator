"""Company/Management access-domain grants. Organization-owned identity capability."""

from __future__ import annotations

from flask import abort
from flask_login import current_user
from sqlalchemy.exc import IntegrityError

from app import db, login_manager
from app.models.user import User, UserMembership, UserMembershipAccessDomainGrant
from app.services.organizations import (
    OrganizationAccessError,
    get_current_organization_id,
    resolve_membership_organization_id,
)

ACCESS_DOMAIN_COMPANY_MANAGEMENT = "COMPANY_MANAGEMENT"
RECOGNIZED_STORED_DOMAINS = frozenset({ACCESS_DOMAIN_COMPANY_MANAGEMENT})

# Future separately governed direction only. Not recognized. Not stored by this slice.
ACCESS_DOMAIN_SENSITIVE_FINANCIAL = "SENSITIVE_FINANCIAL"


class AccessDomainError(Exception):
    """Operator-facing access-domain failure."""


def _user_id(user) -> int:
    try:
        return int(getattr(user, "id", user))
    except (TypeError, ValueError, AttributeError) as exc:
        raise AccessDomainError("An authenticated user is required.") from exc


def _load_user(user) -> User:
    if isinstance(user, User):
        loaded = user
    else:
        loaded = db.session.get(User, _user_id(user))
    if loaded is None:
        raise AccessDomainError("User not found.")
    return loaded


def _require_recognized_domain(domain_key: str) -> str:
    key = (domain_key or "").strip()
    if key not in RECOGNIZED_STORED_DOMAINS:
        raise AccessDomainError("Unknown access domain.")
    return key


def _active_membership_for_org(user: User, organization_id: str):
    if not user.is_active:
        return None
    rows = UserMembership.query.filter_by(
        user_id=user.id,
        organization_id=organization_id,
        is_active=True,
    ).all()
    if len(rows) != 1:
        return None
    return rows[0]


def membership_has_access_domain(user, organization_id, domain_key) -> bool:
    """Return True only when the user's active membership in this org has the grant."""
    try:
        key = _require_recognized_domain(domain_key)
        loaded = _load_user(user)
    except AccessDomainError:
        return False
    membership = _active_membership_for_org(loaded, organization_id)
    if membership is None:
        return False
    grant = UserMembershipAccessDomainGrant.query.filter_by(
        user_membership_id=membership.id,
        domain_key=key,
    ).first()
    return grant is not None


def require_access_domain(domain_key):
    """Abort unless the current request user has the named domain on the current org."""
    if not getattr(current_user, "is_authenticated", False):
        return login_manager.unauthorized()
    try:
        key = _require_recognized_domain(domain_key)
    except AccessDomainError:
        abort(403)
    if not current_user.is_active:
        abort(403)
    try:
        org_id = get_current_organization_id()
        resolved = resolve_membership_organization_id(current_user)
    except OrganizationAccessError:
        abort(403)
    if resolved != org_id:
        abort(403)
    if not membership_has_access_domain(current_user, org_id, key):
        abort(403)
    return None


def _get_membership(membership_id: int) -> UserMembership:
    try:
        mid = int(membership_id)
    except (TypeError, ValueError) as exc:
        raise AccessDomainError("Membership id is required.") from exc
    membership = db.session.get(UserMembership, mid)
    if membership is None:
        raise AccessDomainError("Membership not found.")
    return membership


def grant_access_domain(*, membership_id: int, domain_key: str) -> UserMembershipAccessDomainGrant:
    """Idempotent grant of a recognized stored domain onto an active membership."""
    key = _require_recognized_domain(domain_key)
    membership = _get_membership(membership_id)
    user = db.session.get(User, membership.user_id)
    if user is None or not user.is_active:
        raise AccessDomainError("User is inactive.")
    if not membership.is_active:
        raise AccessDomainError("Membership is inactive.")
    existing = UserMembershipAccessDomainGrant.query.filter_by(
        user_membership_id=membership.id,
        domain_key=key,
    ).first()
    if existing is not None:
        return existing
    grant = UserMembershipAccessDomainGrant(
        user_membership_id=membership.id,
        domain_key=key,
    )
    db.session.add(grant)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        existing = UserMembershipAccessDomainGrant.query.filter_by(
            user_membership_id=membership.id,
            domain_key=key,
        ).first()
        if existing is None:
            raise AccessDomainError("Could not grant access domain.")
        return existing
    return grant


def revoke_access_domain(*, membership_id: int, domain_key: str) -> bool:
    """Idempotent revoke. Missing grant is a successful no-op. Returns True if a row was deleted."""
    key = _require_recognized_domain(domain_key)
    membership = _get_membership(membership_id)
    grant = UserMembershipAccessDomainGrant.query.filter_by(
        user_membership_id=membership.id,
        domain_key=key,
    ).first()
    if grant is None:
        return False
    db.session.delete(grant)
    db.session.commit()
    return True


def describe_access_domains(*, membership_id: int) -> dict:
    """Inspect stored grants and whether COMPANY_MANAGEMENT is currently effective."""
    membership = _get_membership(membership_id)
    user = db.session.get(User, membership.user_id)
    stored = [
        grant.domain_key
        for grant in UserMembershipAccessDomainGrant.query.filter_by(
            user_membership_id=membership.id
        ).order_by(UserMembershipAccessDomainGrant.domain_key.asc())
        if grant.domain_key in RECOGNIZED_STORED_DOMAINS
    ]
    user_active = bool(user is not None and user.is_active)
    membership_active = bool(membership.is_active)
    effective = False
    if user is not None:
        effective = membership_has_access_domain(
            user,
            membership.organization_id,
            ACCESS_DOMAIN_COMPANY_MANAGEMENT,
        )
    return {
        "membership_id": membership.id,
        "organization_id": membership.organization_id,
        "user_id": membership.user_id,
        "user_active": user_active,
        "membership_active": membership_active,
        "stored_domains": stored,
        "effective_COMPANY_MANAGEMENT": effective,
    }
