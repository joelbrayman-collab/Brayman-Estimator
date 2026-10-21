"""People & Access (V1 defect, Joel 21 Oct 2026): the owner manages office and field sign-ins.

Before this, people and access were managed only by ``flask auth`` operator commands, and adding a
second sign-in or deactivating one had no command at all. This module is the office-page seam over
the services that already exist; it adds no table and no new external service.

* Authority: the effective Instance Owner or a System Administrator of the organization, within that
  organization only (the routes also use ``require_instance_owner_or_system_administrator``).
* Add a person: a User (unusable random password) and one active UserMembership, then the existing
  set-password email (PASSWORD_RESET template, ``password_reset.send_set_password_link``).
* Deactivate / reactivate: the existing ``User.is_active`` flag (``instance_authority.deactivate_user``
  refuses the Instance Owner). Deactivation also moves the credentials epoch on, so a session from
  before deactivation ends on its next request and never comes back after reactivation.
* Access domains: ``access_domains.grant_access_domain`` / ``revoke_access_domain``.
* System Administrator: ``instance_authority.appoint_system_administrator`` /
  ``remove_system_administrator`` (these write OrganizationSystemAdministratorEvent rows).

Audit: System Administrator changes are recorded in organization_system_administrator_events and every
email in transactional_messages, as those services already do. Adding a sign-in, deactivation,
reactivation and access-domain changes have no audit table in V1 (no schema change was made); each
is written to the application log (``people_access`` logger) with actor, organization and target.
"""

from __future__ import annotations

import logging
import re
import secrets
from dataclasses import dataclass, field
from typing import Optional

from sqlalchemy.exc import IntegrityError

from app import db
from app.models.organization import Organization, OrganizationSystemAdministratorMembership
from app.models.user import User, UserMembership, UserMembershipAccessDomainGrant
from app.services.access_domains import (
    ACCESS_DOMAIN_COMPANY_MANAGEMENT,
    RECOGNIZED_STORED_DOMAINS,
    AccessDomainError,
    grant_access_domain,
    revoke_access_domain,
)
from app.services.auth import AuthServiceError, hash_password, normalize_email
from app.services.instance_authority import (
    InstanceAuthorityError,
    appoint_system_administrator,
    deactivate_user,
    is_instance_owner,
    is_system_administrator,
    remove_system_administrator,
)

audit_log = logging.getLogger("people_access")

ACCESS_DOMAIN_LABELS = {
    ACCESS_DOMAIN_COMPANY_MANAGEMENT: "Company Management (Needs attention and company figures)",
}

PEOPLE_ADMIN_REQUIRED = "Only the owner or a System Administrator may manage people and access."
PERSON_NOT_FOUND = "Person not found."
EMAIL_TAKEN = "This email already has a sign-in. Use a different email."
CANNOT_DEACTIVATE_SELF = "You cannot deactivate your own sign-in."
CANNOT_DEACTIVATE_OWNER = "The owner's sign-in cannot be deactivated."
OTHER_COMPANY_SIGN_IN = "This sign-in also belongs to another company and cannot be changed here."

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class PeopleAccessError(Exception):
    """Plain-words failure shown to the owner."""


@dataclass
class PersonAccess:
    membership_id: int
    user_id: int
    display_name: str
    email: str
    user_active: bool
    membership_active: bool
    is_owner: bool
    is_administrator: bool
    is_self: bool
    domains: list = field(default_factory=list)
    field_only: bool = False

    @property
    def can_sign_in(self) -> bool:
        return self.user_active and self.membership_active

    @property
    def status_label(self) -> str:
        if not self.user_active:
            return "Deactivated"
        if not self.membership_active:
            return "Removed from company"
        return "Can sign in"

    @property
    def role_label(self) -> str:
        if self.is_owner:
            return "Owner"
        if self.is_administrator:
            return "System Administrator"
        return "Field only" if self.field_only else "Office"


_EVENT_FOR_LOG = {"ADD_PERSON": "ADDED", "DEACTIVATE": "DEACTIVATED", "REACTIVATE": "REACTIVATED",
                  "GRANT_ACCESS_DOMAIN": "ACCESS_GIVEN", "REVOKE_ACCESS_DOMAIN": "ACCESS_REMOVED",
                  "APPOINT_ADMINISTRATOR": "ADMINISTRATOR_APPOINTED", "REMOVE_ADMINISTRATOR": "ADMINISTRATOR_REMOVED"}


def record_people_event(*, organization_id: str, membership, action: str, actor=None, detail: str = "") -> None:
    """Durable People & Access history (people_access_events). Append-only; never blocks the action."""
    from app.models.people_access_event import PeopleAccessEvent

    membership = membership if isinstance(membership, UserMembership) else db.session.get(UserMembership, int(membership))
    if membership is None:
        return
    actor_user = None
    if actor is not None:
        actor_user = actor if isinstance(actor, User) else db.session.get(User, int(getattr(actor, "id", actor)))
    name = (getattr(actor_user, "display_name", None) or getattr(actor_user, "email", None)
            or (membership.user.display_name if action == "ACTIVATED" else "CalibraytAI"))
    try:
        db.session.add(PeopleAccessEvent(organization_id=organization_id, membership_id=membership.id,
                                         target_user_id=membership.user_id,
                                         actor_user_id=getattr(actor_user, "id", None), actor_name=name[:150],
                                         action=action, detail=(detail or None) and detail[:255]))
        db.session.commit()
    except Exception:  # history must never undo the change it records
        db.session.rollback()
        audit_log.exception("people_access history row not written: %s membership=%s", action, getattr(membership, "id", None))


def people_history(*, organization_id: str, membership_id, limit: int = 50) -> list:
    from app.models.people_access_event import PeopleAccessEvent

    return (PeopleAccessEvent.query.filter_by(organization_id=organization_id, membership_id=int(membership_id))
            .order_by(PeopleAccessEvent.created_at.desc(), PeopleAccessEvent.id.desc()).limit(limit).all())


def _audit(action: str, *, actor: User, organization_id: str, target: Optional[User], detail: str = "",
           membership=None) -> None:
    if membership is None and target is not None:
        membership = UserMembership.query.filter_by(user_id=target.id, organization_id=organization_id).first()
    if membership is not None and action in _EVENT_FOR_LOG:
        record_people_event(organization_id=organization_id, membership=membership, action=_EVENT_FOR_LOG[action],
                            actor=actor, detail=detail.replace("domain=", "") if detail else "")
    audit_log.info(
        "people_access %s org=%s actor_user_id=%s target_user_id=%s %s",
        action,
        organization_id,
        actor.id,
        getattr(target, "id", None),
        detail,
    )


def require_people_administrator(actor, organization_id: str) -> User:
    user = actor if isinstance(actor, User) else db.session.get(User, int(getattr(actor, "id", actor)))
    if user is None or not user.is_active:
        raise PeopleAccessError(PEOPLE_ADMIN_REQUIRED)
    if db.session.get(Organization, organization_id) is None:
        raise PeopleAccessError(PEOPLE_ADMIN_REQUIRED)
    if not (is_instance_owner(user, organization_id) or is_system_administrator(user, organization_id)):
        raise PeopleAccessError(PEOPLE_ADMIN_REQUIRED)
    return user


def _membership_in_org(membership_id, organization_id: str) -> UserMembership:
    try:
        mid = int(membership_id)
    except (TypeError, ValueError) as exc:
        raise PeopleAccessError(PERSON_NOT_FOUND) from exc
    membership = db.session.get(UserMembership, mid)
    if membership is None or membership.organization_id != organization_id:
        raise PeopleAccessError(PERSON_NOT_FOUND)
    return membership


def _describe(membership: UserMembership, org: Organization, actor: User, admin_ids: set) -> PersonAccess:
    user = membership.user
    domains = sorted(
        grant.domain_key
        for grant in UserMembershipAccessDomainGrant.query.filter_by(user_membership_id=membership.id)
        if grant.domain_key in RECOGNIZED_STORED_DOMAINS
    )
    return PersonAccess(
        membership_id=membership.id,
        user_id=user.id,
        display_name=user.display_name,
        email=user.email,
        user_active=bool(user.is_active),
        membership_active=bool(membership.is_active),
        is_owner=org.instance_owner_membership_id == membership.id,
        is_administrator=membership.id in admin_ids,
        is_self=user.id == actor.id,
        domains=domains,
        field_only=_is_field_only(membership),
    )


def _is_field_only(membership) -> bool:
    from app.services.access_domains import membership_is_field_only

    return bool(membership_is_field_only(membership))


def _admin_membership_ids(organization_id: str) -> set:
    return {
        row.membership_id
        for row in OrganizationSystemAdministratorMembership.query.filter_by(organization_id=organization_id)
    }


def list_people_access(*, organization_id: str, actor) -> list[PersonAccess]:
    actor_user = require_people_administrator(actor, organization_id)
    org = db.session.get(Organization, organization_id)
    admin_ids = _admin_membership_ids(org.id)
    rows = (
        UserMembership.query.join(User, User.id == UserMembership.user_id)
        .filter(UserMembership.organization_id == org.id)
        .order_by(User.is_active.desc(), User.display_name.asc(), User.id.asc())
        .all()
    )
    return [_describe(row, org, actor_user, admin_ids) for row in rows]


def get_person_access(*, organization_id: str, membership_id, actor) -> PersonAccess:
    actor_user = require_people_administrator(actor, organization_id)
    membership = _membership_in_org(membership_id, organization_id)
    org = db.session.get(Organization, organization_id)
    return _describe(membership, org, actor_user, _admin_membership_ids(org.id))


def add_person(*, organization_id: str, actor, display_name: str, email: str) -> UserMembership:
    """Create a sign-in (User + active membership in this organization). The caller sends the link."""
    actor_user = require_people_administrator(actor, organization_id)
    name = (display_name or "").strip()
    if not name:
        raise PeopleAccessError("Enter the person's name.")
    try:
        address = normalize_email(email)
    except AuthServiceError as exc:
        raise PeopleAccessError("Enter the person's email.") from exc
    if not _EMAIL_RE.match(address) or len(address) > 255:
        raise PeopleAccessError("Enter a valid email.")
    if User.query.filter_by(email=address).first() is not None:
        raise PeopleAccessError(EMAIL_TAKEN)
    # Nobody knows this password: the person chooses their own from the emailed link.
    user = User(
        email=address,
        display_name=name[:150],
        password_hash=hash_password(secrets.token_urlsafe(32)),
        is_active=True,
    )
    db.session.add(user)
    try:
        db.session.flush()
        membership = UserMembership(user_id=user.id, organization_id=organization_id, is_active=True)
        db.session.add(membership)
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise PeopleAccessError(EMAIL_TAKEN) from exc
    _audit("ADD_PERSON", actor=actor_user, organization_id=organization_id, target=user)
    return membership


def _require_only_this_org(user: User, organization_id: str) -> None:
    other = (
        UserMembership.query.filter(UserMembership.user_id == user.id)
        .filter(UserMembership.organization_id != organization_id)
        .filter(UserMembership.is_active.is_(True))
        .first()
    )
    if other is not None:
        raise PeopleAccessError(OTHER_COMPANY_SIGN_IN)


def deactivate_person(*, organization_id: str, membership_id, actor) -> User:
    actor_user = require_people_administrator(actor, organization_id)
    membership = _membership_in_org(membership_id, organization_id)
    user = membership.user
    if user.id == actor_user.id:
        raise PeopleAccessError(CANNOT_DEACTIVATE_SELF)
    org = db.session.get(Organization, organization_id)
    if org.instance_owner_membership_id == membership.id:
        raise PeopleAccessError(CANNOT_DEACTIVATE_OWNER)
    _require_only_this_org(user, organization_id)
    if not user.is_active:
        return user
    # End every existing session for good: reactivation must not bring an old session back.
    user.credentials_epoch = int(user.credentials_epoch or 0) + 1
    try:
        deactivate_user(user)  # refuses an effective Instance Owner anywhere; commits
    except InstanceAuthorityError as exc:
        db.session.rollback()
        raise PeopleAccessError(CANNOT_DEACTIVATE_OWNER) from exc
    _audit("DEACTIVATE", actor=actor_user, organization_id=organization_id, target=user)
    return user


def reactivate_person(*, organization_id: str, membership_id, actor) -> User:
    actor_user = require_people_administrator(actor, organization_id)
    membership = _membership_in_org(membership_id, organization_id)
    user = membership.user
    _require_only_this_org(user, organization_id)
    changed = not user.is_active or not membership.is_active
    user.is_active = True
    membership.is_active = True
    db.session.commit()
    if changed:
        _audit("REACTIVATE", actor=actor_user, organization_id=organization_id, target=user)
    return user


def set_access_domain(*, organization_id: str, membership_id, actor, domain_key: str, granted: bool) -> None:
    actor_user = require_people_administrator(actor, organization_id)
    membership = _membership_in_org(membership_id, organization_id)
    try:
        if granted:
            grant_access_domain(membership_id=membership.id, domain_key=domain_key)
        else:
            revoke_access_domain(membership_id=membership.id, domain_key=domain_key)
    except AccessDomainError as exc:
        raise PeopleAccessError(str(exc)) from exc
    _audit(
        "GRANT_ACCESS_DOMAIN" if granted else "REVOKE_ACCESS_DOMAIN",
        actor=actor_user,
        organization_id=organization_id,
        target=membership.user,
        detail=f"domain={domain_key}",
    )


def set_system_administrator(*, organization_id: str, membership_id, actor, appointed: bool) -> None:
    """Through the existing instance-authority functions (they write the event rows and their own rules:
    only the owner appoints; the owner is never a System Administrator and cannot be removed)."""
    actor_user = require_people_administrator(actor, organization_id)
    membership = _membership_in_org(membership_id, organization_id)
    try:
        if appointed:
            appoint_system_administrator(organization_id, membership.id, actor_user)
        else:
            remove_system_administrator(organization_id, membership.id, actor_user)
    except InstanceAuthorityError as exc:
        raise PeopleAccessError(str(exc)) from exc
    _audit("APPOINT_ADMINISTRATOR" if appointed else "REMOVE_ADMINISTRATOR", actor=actor_user,
           organization_id=organization_id, target=membership.user, membership=membership)


def membership_user(*, organization_id: str, membership_id, actor) -> User:
    require_people_administrator(actor, organization_id)
    return _membership_in_org(membership_id, organization_id).user
