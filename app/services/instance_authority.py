"""FG-038 Instance Owner and System Administrator administrative authority.

Separate from A/B/C information-domain grants in access_domains.py.
System Administrator is explicit org-scoped membership authority, not a domain.
"""

from __future__ import annotations

from datetime import datetime

from flask import abort
from flask_login import current_user

from app import db, login_manager
from app.models.organization import (
    ADMINISTRATOR_EVENT_APPOINT,
    ADMINISTRATOR_EVENT_REMOVE,
    INSTANCE_OWNER_EVENT_SET,
    Organization,
    OrganizationInstanceOwnerEvent,
    OrganizationSystemAdministratorEvent,
    OrganizationSystemAdministratorMembership,
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
OWNER_APPOINT_BLOCKED = (
    "The Instance Owner is not appointed as a System Administrator."
)
OWNER_REMOVE_BLOCKED = (
    "The Instance Owner cannot be removed as a System Administrator, and "
    "a System Administrator cannot remove the Instance Owner."
)
APPOINT_OWNER_ONLY = (
    "Only the Instance Owner may appoint a System Administrator."
)
REMOVE_UNAUTHORIZED = (
    "Only the Instance Owner or a System Administrator may remove a "
    "System Administrator."
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
    """True only for an explicit current Sys Admin row with active membership and user."""
    try:
        loaded = _load_user(user)
        org = _load_organization(organization_id)
    except InstanceAuthorityError:
        return False
    if not loaded.is_active:
        return False
    membership = UserMembership.query.filter_by(
        user_id=loaded.id,
        organization_id=org.id,
        is_active=True,
    ).first()
    if membership is None:
        return False
    row = OrganizationSystemAdministratorMembership.query.filter_by(
        organization_id=org.id,
        membership_id=membership.id,
    ).first()
    return row is not None


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
    """Authorize the effective Instance Owner or an effective System Administrator."""
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


def _actor_identifier(actor_user: User) -> str:
    return ((actor_user.display_name or "").strip() or f"user-{actor_user.id}")[:150]


def _current_administrator_row(organization_id: str, membership_id: int):
    return OrganizationSystemAdministratorMembership.query.filter_by(
        organization_id=organization_id,
        membership_id=membership_id,
    ).first()


def _target_membership_for_administrator(org: Organization, membership_id: int) -> UserMembership:
    membership = _load_membership(membership_id)
    if membership.organization_id != org.id:
        raise InstanceAuthorityError(
            "Membership does not belong to this organization."
        )
    if not membership.is_active:
        raise InstanceAuthorityError("Membership is inactive.")
    target_user = db.session.get(User, membership.user_id)
    if target_user is None or not target_user.is_active:
        raise InstanceAuthorityError("User is inactive.")
    return membership


def appoint_system_administrator(organization_id, membership_id, actor) -> OrganizationSystemAdministratorMembership:
    """Appoint a System Administrator. Instance Owner only. No HTTP."""
    org = _load_organization(organization_id)
    actor_user = _load_user(actor)
    if not actor_user.is_active:
        raise InstanceAuthorityError("Actor is inactive.")
    if not is_instance_owner(actor_user, org.id):
        raise InstanceAuthorityError(APPOINT_OWNER_ONLY)
    membership = _target_membership_for_administrator(org, membership_id)
    if org.instance_owner_membership_id == membership.id:
        raise InstanceAuthorityError(OWNER_APPOINT_BLOCKED)

    existing = _current_administrator_row(org.id, membership.id)
    if existing is not None:
        return existing

    now = datetime.utcnow()
    row = OrganizationSystemAdministratorMembership(
        organization_id=org.id,
        membership_id=membership.id,
        appointed_at=now,
        appointed_by_user_id=actor_user.id,
    )
    db.session.add(row)
    db.session.add(
        OrganizationSystemAdministratorEvent(
            organization_id=org.id,
            membership_id=membership.id,
            event=ADMINISTRATOR_EVENT_APPOINT,
            actor_user_id=actor_user.id,
            actor_identifier=_actor_identifier(actor_user),
            created_at=now,
        )
    )
    db.session.commit()
    return row


def remove_system_administrator(organization_id, membership_id, actor) -> None:
    """Remove a System Administrator. Owner any; Sys Admin another or self. No HTTP."""
    org = _load_organization(organization_id)
    actor_user = _load_user(actor)
    if not actor_user.is_active:
        raise InstanceAuthorityError("Actor is inactive.")
    membership = _load_membership(membership_id)
    if membership.organization_id != org.id:
        raise InstanceAuthorityError(
            "Membership does not belong to this organization."
        )
    if org.instance_owner_membership_id == membership.id:
        raise InstanceAuthorityError(OWNER_REMOVE_BLOCKED)

    actor_is_owner = is_instance_owner(actor_user, org.id)
    actor_is_admin = is_system_administrator(actor_user, org.id)
    if not actor_is_owner and not actor_is_admin:
        raise InstanceAuthorityError(REMOVE_UNAUTHORIZED)

    existing = _current_administrator_row(org.id, membership.id)
    if existing is None:
        return

    now = datetime.utcnow()
    db.session.delete(existing)
    db.session.add(
        OrganizationSystemAdministratorEvent(
            organization_id=org.id,
            membership_id=membership.id,
            event=ADMINISTRATOR_EVENT_REMOVE,
            actor_user_id=actor_user.id,
            actor_identifier=_actor_identifier(actor_user),
            created_at=now,
        )
    )
    db.session.commit()


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
