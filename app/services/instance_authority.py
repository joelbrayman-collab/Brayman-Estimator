"""FG-038 PA-A Instance Owner administrative authority.

Separate from A/B/C information-domain grants in access_domains.py.
System Administrator persistence is PA-B; is_system_administrator is False here.
"""

from __future__ import annotations

from datetime import datetime

from flask import abort
from flask_login import current_user

from app import db, login_manager
from app.models.organization import (
    INSTANCE_OWNER_EVENT_SET,
    Organization,
    OrganizationInstanceOwnerEvent,
)
from app.models.user import User, UserMembership
from app.services.organizations import (
    OrganizationAccessError,
    get_current_organization_id,
    resolve_membership_organization_id,
)

OWNER_DEACTIVATION_BLOCKED = (
    "This membership is the Instance Owner. Ordinary deactivation is not "
    "allowed. Future governed transfer/recovery is required."
)
OWNER_USER_DEACTIVATION_BLOCKED = (
    "This user is the Instance Owner. Ordinary deactivation is not allowed. "
    "Future governed transfer/recovery is required."
)


class InstanceAuthorityError(Exception):
    """Operator-facing Instance Owner authority failure."""


def _user_id(user) -> int:
    try:
        return int(getattr(user, "id", user))
    except (TypeError, ValueError, AttributeError) as exc:
        raise InstanceAuthorityError("An authenticated user is required.") from exc


def _load_user(user) -> User:
    if isinstance(user, User):
        loaded = user
    else:
        loaded = db.session.get(User, _user_id(user))
    if loaded is None:
        raise InstanceAuthorityError("User not found.")
    return loaded


def _load_organization(organization_id: str) -> Organization:
    org_id = (organization_id or "").strip()
    if not org_id:
        raise InstanceAuthorityError("Organization is required.")
    org = db.session.get(Organization, org_id)
    if org is None:
        raise InstanceAuthorityError("Organization not found.")
    return org


def _load_membership(membership_id: int) -> UserMembership:
    try:
        mid = int(membership_id)
    except (TypeError, ValueError) as exc:
        raise InstanceAuthorityError("Membership id is required.") from exc
    membership = db.session.get(UserMembership, mid)
    if membership is None:
        raise InstanceAuthorityError("Membership not found.")
    return membership


def _membership_is_effective_owner(org: Organization, membership: UserMembership) -> bool:
    if org.instance_owner_membership_id != membership.id:
        return False
    if membership.organization_id != org.id:
        return False
    if not membership.is_active:
        return False
    user = db.session.get(User, membership.user_id)
    return bool(user is not None and user.is_active)


def get_instance_owner_membership(organization_id: str):
    """Return the effective Instance Owner membership, or None."""
    try:
        org = _load_organization(organization_id)
    except InstanceAuthorityError:
        return None
    if org.instance_owner_membership_id is None:
        return None
    membership = db.session.get(UserMembership, org.instance_owner_membership_id)
    if membership is None:
        return None
    if not _membership_is_effective_owner(org, membership):
        return None
    return membership


def is_instance_owner(user, organization_id: str) -> bool:
    try:
        loaded = _load_user(user)
    except InstanceAuthorityError:
        return False
    if not loaded.is_active:
        return False
    membership = get_instance_owner_membership(organization_id)
    if membership is None:
        return False
    return membership.user_id == loaded.id


def is_system_administrator(user, organization_id: str) -> bool:
    """PA-B not implemented. Always False in PA-A."""
    return False


def require_instance_owner():
    """Abort unless the current request user is the effective Instance Owner."""
    if not getattr(current_user, "is_authenticated", False):
        return login_manager.unauthorized()
    if not current_user.is_active:
        abort(403)
    try:
        org_id = get_current_organization_id()
        resolved = resolve_membership_organization_id(current_user)
    except OrganizationAccessError:
        abort(403)
    if resolved != org_id:
        abort(403)
    if not is_instance_owner(current_user, org_id):
        abort(403)
    return None


def require_instance_owner_or_system_administrator():
    """PA-A: Instance Owner only. PA-B may later OR Sys Admin without changing callers."""
    if not getattr(current_user, "is_authenticated", False):
        return login_manager.unauthorized()
    if not current_user.is_active:
        abort(403)
    try:
        org_id = get_current_organization_id()
        resolved = resolve_membership_organization_id(current_user)
    except OrganizationAccessError:
        abort(403)
    if resolved != org_id:
        abort(403)
    if is_instance_owner(current_user, org_id):
        return None
    if is_system_administrator(current_user, org_id):
        return None
    abort(403)


def set_instance_owner(organization_id, membership_id, actor) -> Organization:
    """Set the current Instance Owner. CLI/bootstrap only in PA-A. No HTTP."""
    org = _load_organization(organization_id)
    membership = _load_membership(membership_id)
    actor_user = _load_user(actor)
    if membership.organization_id != org.id:
        raise InstanceAuthorityError(
            "Membership does not belong to this organization."
        )
    if not membership.is_active:
        raise InstanceAuthorityError("Membership is inactive.")
    target_user = db.session.get(User, membership.user_id)
    if target_user is None or not target_user.is_active:
        raise InstanceAuthorityError("User is inactive.")
    if not actor_user.is_active:
        raise InstanceAuthorityError("Actor is inactive.")

    previous_id = org.instance_owner_membership_id
    if previous_id == membership.id and get_instance_owner_membership(org.id) is not None:
        return org

    now = datetime.utcnow()
    actor_identifier = (actor_user.display_name or "").strip() or f"user-{actor_user.id}"
    org.instance_owner_membership_id = membership.id
    org.instance_owner_set_at = now
    org.instance_owner_set_by_user_id = actor_user.id
    db.session.add(
        OrganizationInstanceOwnerEvent(
            organization_id=org.id,
            event=INSTANCE_OWNER_EVENT_SET,
            previous_membership_id=previous_id,
            new_membership_id=membership.id,
            actor_user_id=actor_user.id,
            actor_identifier=actor_identifier[:150],
            created_at=now,
        )
    )
    db.session.commit()
    return org


def deactivate_membership(membership: UserMembership) -> UserMembership:
    """Ordinary membership deactivation. Refuses the current Instance Owner."""
    if membership is None:
        raise InstanceAuthorityError("Membership is required.")
    org = db.session.get(Organization, membership.organization_id)
    if org is not None and org.instance_owner_membership_id == membership.id:
        raise InstanceAuthorityError(OWNER_DEACTIVATION_BLOCKED)
    membership.is_active = False
    db.session.commit()
    return membership


def deactivate_user(user) -> User:
    """Ordinary user deactivation. Refuses an effective Instance Owner user."""
    loaded = _load_user(user)
    memberships = UserMembership.query.filter_by(user_id=loaded.id).all()
    for membership in memberships:
        org = db.session.get(Organization, membership.organization_id)
        if org is None:
            continue
        if _membership_is_effective_owner(org, membership):
            raise InstanceAuthorityError(OWNER_USER_DEACTIVATION_BLOCKED)
    loaded.is_active = False
    db.session.commit()
    return loaded
