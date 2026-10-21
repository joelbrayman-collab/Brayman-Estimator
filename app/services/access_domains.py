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

# Field-only restriction (Joel, 21 Oct 2026, V1 defect: crew could reach office costs). Stored as a
# row in the same grants table, but it is a RESTRICTION, not a grant: a membership carrying it reaches
# only the Field pages and its own account pages (app/__init__.py protect_office_routes), and has no
# scheduling authority. It is deliberately not in RECOGNIZED_STORED_DOMAINS, so the generic
# grant/revoke/require helpers refuse it; it is changed only through set_field_only (owner or
# System Administrator). Memberships without the row keep exactly the access they had.
MEMBERSHIP_RESTRICTION_FIELD_ONLY = "FIELD_ONLY"

# What a field-only user may open. Everything else: pages redirect to /field/today, POST and API 403.
FIELD_ONLY_ALLOWED_PREFIXES = ("field.",)
FIELD_ONLY_ALLOWED_ENDPOINTS = frozenset(
    {
        "auth.change_password",  # their own account page
        "help.ask_help",  # the Field pages' contextual help (static help text, no company data)
        # Field capture (field.js) and the photo on Field Today. Project identity and observations
        # only; no cost, price or commercial data. Office review of derived candidates is excluded.
        "api_v1.me",
        "api_v1.list_projects",
        "api_v1.get_project",
        "api_v1.field_events",
        "api_v1.field_event_detail",
        "api_v1.field_event_originals",
        "api_v1.field_event_original_detail",
        "api_v1.field_event_original_content",
        "api_v1.field_event_original_display",
    }
)


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


def membership_is_field_only(membership) -> bool:
    """True when this membership carries the FIELD_ONLY restriction."""
    if membership is None:
        return False
    return (
        UserMembershipAccessDomainGrant.query.filter_by(
            user_membership_id=membership.id,
            domain_key=MEMBERSHIP_RESTRICTION_FIELD_ONLY,
        ).first()
        is not None
    )


def user_is_field_only(user, organization_id) -> bool:
    """True when the user's active membership in this organization is restricted to Field."""
    try:
        loaded = _load_user(user)
    except AccessDomainError:
        return False
    rows = UserMembership.query.filter_by(user_id=loaded.id, organization_id=organization_id).all()
    # Fail closed toward the restriction: an inactive membership row that still carries it counts.
    return any(membership_is_field_only(row) for row in rows)


def field_only_endpoint_allowed(endpoint) -> bool:
    if not endpoint:
        return False
    return endpoint in FIELD_ONLY_ALLOWED_ENDPOINTS or endpoint.startswith(FIELD_ONLY_ALLOWED_PREFIXES)


def has_office_scheduling_authority(user, organization_id) -> bool:
    """Office members (and so the owner and System Administrators) may change the schedule.
    A field-only member never may. Organization membership itself is enforced by the office wall."""
    try:
        loaded = _load_user(user)
    except AccessDomainError:
        return False
    if not loaded.is_active:
        return False
    if _active_membership_for_org(loaded, organization_id) is None:
        return False
    return not user_is_field_only(loaded, organization_id)


def require_office_scheduling_authority():
    """Abort 403 unless the current request user may create, move or retire scheduled work."""
    if not getattr(current_user, "is_authenticated", False):
        return login_manager.unauthorized()
    try:
        org_id = get_current_organization_id()
    except OrganizationAccessError:
        abort(403)
    if not has_office_scheduling_authority(current_user, org_id):
        abort(403)
    return None


def set_field_only(membership, field_only: bool, actor) -> bool:
    """Mark (True) or clear (False) the FIELD_ONLY restriction on one membership. Idempotent.

    `membership` is a UserMembership or its id; `actor` a User or user id who must be the effective
    Instance Owner or a System Administrator of that membership's organization. The Instance Owner
    and System Administrators cannot be marked field-only (they would lose the authority they hold).
    Returns the resulting state.
    """
    from app.services.instance_authority import (
        get_instance_owner_membership,
        is_instance_owner,
        is_system_administrator,
    )
    from app.models.organization import OrganizationSystemAdministratorMembership

    target = membership if isinstance(membership, UserMembership) else _get_membership(membership)
    actor_user = _load_user(actor)
    org_id = target.organization_id
    if not actor_user.is_active:
        raise AccessDomainError("Actor is inactive.")
    if not (is_instance_owner(actor_user, org_id) or is_system_administrator(actor_user, org_id)):
        raise AccessDomainError(
            "Only the Instance Owner or a System Administrator may change field-only access."
        )
    if field_only:
        owner = get_instance_owner_membership(org_id)
        if owner is not None and owner.id == target.id:
            raise AccessDomainError("The Instance Owner cannot be marked field-only.")
        if OrganizationSystemAdministratorMembership.query.filter_by(
            organization_id=org_id, membership_id=target.id
        ).first() is not None:
            raise AccessDomainError("A System Administrator cannot be marked field-only.")
    existing = UserMembershipAccessDomainGrant.query.filter_by(
        user_membership_id=target.id,
        domain_key=MEMBERSHIP_RESTRICTION_FIELD_ONLY,
    ).first()
    if field_only and existing is None:
        db.session.add(
            UserMembershipAccessDomainGrant(
                user_membership_id=target.id,
                domain_key=MEMBERSHIP_RESTRICTION_FIELD_ONLY,
            )
        )
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
    elif not field_only and existing is not None:
        db.session.delete(existing)
        db.session.commit()
    return membership_is_field_only(target)


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
        "field_only": membership_is_field_only(membership),
        "membership_id": membership.id,
        "organization_id": membership.organization_id,
        "user_id": membership.user_id,
        "user_active": user_active,
        "membership_active": membership_active,
        "stored_domains": stored,
        "effective_COMPANY_MANAGEMENT": effective,
    }


FIELD_ASSIGNMENT_LOOKBACK_DAYS = 14


def field_visible_project_ids(user, organization_id):
    """Projects a field-only crew member may see (Crew Access, 21 Oct 2026): those with active scheduled
    work they are on, directly or through a crew they belong to during that work, ending no more than
    two weeks ago or later. Returns None for anyone not marked field-only (no restriction)."""
    from datetime import date, timedelta

    from app.models.organization_crew import OrganizationCrewMember
    from app.models.schedule import SCHEDULE_STATUS_ACTIVE, WorkScheduleAssignment, WorkScheduleItem

    if not user_is_field_only(user, organization_id):
        return None
    user_id = int(getattr(user, "id", user))
    since = date.today() - timedelta(days=FIELD_ASSIGNMENT_LOOKBACK_DAYS)
    items = (WorkScheduleItem.query.filter(WorkScheduleItem.organization_id == organization_id,
                                           WorkScheduleItem.status == SCHEDULE_STATUS_ACTIVE,
                                           WorkScheduleItem.scheduled_end >= since).all())
    memberships = OrganizationCrewMember.query.filter_by(organization_id=organization_id, user_id=user_id).all()
    visible = set()
    for item in items:
        for a in WorkScheduleAssignment.query.filter_by(work_schedule_item_id=item.id).all():
            if a.worker_user_id == user_id:
                visible.add(item.project_id)
            elif a.crew_id is not None:
                for m in memberships:
                    if m.crew_id == a.crew_id and m.effective_from <= item.scheduled_end and (
                            m.effective_to is None or m.effective_to >= item.scheduled_start):
                        visible.add(item.project_id)
    return visible
