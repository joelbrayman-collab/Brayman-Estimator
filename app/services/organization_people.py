"""FG-038 PA-C Person / Worker identity foundation.

Person is organization-scoped human/worker identity, distinct from User,
Membership, A/B/C, Instance Owner, and System Administrator.

Hourly wage is mandatory Person compensation data. It is not Domain C.
Read and write go through this service. Ordinary identity payloads omit wage.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Optional

from app import db
from app.models.organization import Organization
from app.models.person import OrganizationPerson
from app.models.user import User
from app.services.instance_authority import (
    is_instance_owner,
    is_system_administrator,
)

PERSON_ADMIN_REQUIRED = (
    "Only the Instance Owner or a System Administrator may administer People."
)
PERSON_WAGE_READ_DENIED = (
    "Only the Instance Owner or a System Administrator may read hourly wage."
)
PERSON_NOT_FOUND = "Person not found."
PERSON_ORG_REQUIRED = "Organization is required."
PERSON_CROSS_ORG = "Person does not belong to this organization."


class PersonAuthorityError(Exception):
    """Operator-facing Person identity failure."""


@dataclass(frozen=True)
class PersonIdentity:
    """Ordinary Person identity. Does not include hourly wage."""

    id: int
    organization_id: str
    full_name: str
    address: str
    mobile_number: str
    email_address: str
    is_active: bool


def _load_user(user) -> User:
    try:
        if isinstance(user, User):
            loaded = user
        else:
            loaded = db.session.get(User, int(getattr(user, "id", user)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise PersonAuthorityError("An authenticated user is required.") from exc
    if loaded is None:
        raise PersonAuthorityError("User not found.")
    return loaded


def _load_organization(organization_id: str) -> Organization:
    org_id = (organization_id or "").strip()
    if not org_id:
        raise PersonAuthorityError(PERSON_ORG_REQUIRED)
    org = db.session.get(Organization, org_id)
    if org is None:
        raise PersonAuthorityError("Organization not found.")
    return org


def _require_person_administrator(actor, organization_id: str) -> User:
    loaded = _load_user(actor)
    org = _load_organization(organization_id)
    if is_instance_owner(loaded, org.id) or is_system_administrator(loaded, org.id):
        return loaded
    raise PersonAuthorityError(PERSON_ADMIN_REQUIRED)


def _nonempty(value, field_name: str) -> str:
    text = (value or "").strip() if isinstance(value, str) else str(value or "").strip()
    if not text:
        raise PersonAuthorityError(f"{field_name} is required.")
    return text


def _normalize_email(value) -> str:
    email = _nonempty(value, "Email address").lower()
    if "@" not in email or email.startswith("@") or email.endswith("@"):
        raise PersonAuthorityError("Email address is required.")
    return email[:255]


def _normalize_wage(value) -> Decimal:
    if value is None or (isinstance(value, str) and not value.strip()):
        raise PersonAuthorityError("Hourly wage is required.")
    try:
        wage = Decimal(str(value)).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError) as exc:
        raise PersonAuthorityError("Hourly wage is required.") from exc
    if wage < 0:
        raise PersonAuthorityError("Hourly wage is required.")
    return wage


def _identity(person: OrganizationPerson) -> PersonIdentity:
    return PersonIdentity(
        id=person.id,
        organization_id=person.organization_id,
        full_name=person.full_name,
        address=person.address,
        mobile_number=person.mobile_number,
        email_address=person.email_address,
        is_active=bool(person.is_active),
    )


def _load_person(person_id: int, organization_id: str) -> OrganizationPerson:
    try:
        pid = int(person_id)
    except (TypeError, ValueError) as exc:
        raise PersonAuthorityError(PERSON_NOT_FOUND) from exc
    org = _load_organization(organization_id)
    person = db.session.get(OrganizationPerson, pid)
    if person is None:
        raise PersonAuthorityError(PERSON_NOT_FOUND)
    if person.organization_id != org.id:
        raise PersonAuthorityError(PERSON_CROSS_ORG)
    return person


def create_person(
    *,
    organization_id: str,
    actor,
    full_name: str,
    address: str,
    mobile_number: str,
    email_address: str,
    hourly_wage,
) -> PersonIdentity:
    actor_user = _require_person_administrator(actor, organization_id)
    org = _load_organization(organization_id)
    now = datetime.utcnow()
    person = OrganizationPerson(
        organization_id=org.id,
        full_name=_nonempty(full_name, "Full name")[:150],
        address=_nonempty(address, "Address"),
        mobile_number=_nonempty(mobile_number, "Mobile number")[:40],
        email_address=_normalize_email(email_address),
        hourly_wage=_normalize_wage(hourly_wage),
        is_active=True,
        created_at=now,
        created_by_user_id=actor_user.id,
        updated_at=now,
        updated_by_user_id=actor_user.id,
    )
    db.session.add(person)
    db.session.commit()
    return _identity(person)


def get_person(*, organization_id: str, person_id: int, actor) -> PersonIdentity:
    _require_person_administrator(actor, organization_id)
    return _identity(_load_person(person_id, organization_id))


def list_organization_people(*, organization_id: str, actor) -> list[PersonIdentity]:
    _require_person_administrator(actor, organization_id)
    org = _load_organization(organization_id)
    rows = (
        OrganizationPerson.query.filter_by(organization_id=org.id)
        .order_by(OrganizationPerson.id.asc())
        .all()
    )
    return [_identity(row) for row in rows]


def update_person(
    *,
    organization_id: str,
    person_id: int,
    actor,
    full_name: Optional[str] = None,
    address: Optional[str] = None,
    mobile_number: Optional[str] = None,
    email_address: Optional[str] = None,
    hourly_wage=None,
) -> PersonIdentity:
    actor_user = _require_person_administrator(actor, organization_id)
    person = _load_person(person_id, organization_id)
    if full_name is not None:
        person.full_name = _nonempty(full_name, "Full name")[:150]
    if address is not None:
        person.address = _nonempty(address, "Address")
    if mobile_number is not None:
        person.mobile_number = _nonempty(mobile_number, "Mobile number")[:40]
    if email_address is not None:
        person.email_address = _normalize_email(email_address)
    if hourly_wage is not None:
        person.hourly_wage = _normalize_wage(hourly_wage)
    person.updated_at = datetime.utcnow()
    person.updated_by_user_id = actor_user.id
    db.session.commit()
    return _identity(person)


def deactivate_person(*, organization_id: str, person_id: int, actor) -> PersonIdentity:
    actor_user = _require_person_administrator(actor, organization_id)
    person = _load_person(person_id, organization_id)
    person.is_active = False
    person.updated_at = datetime.utcnow()
    person.updated_by_user_id = actor_user.id
    db.session.commit()
    return _identity(person)


def reactivate_person(*, organization_id: str, person_id: int, actor) -> PersonIdentity:
    actor_user = _require_person_administrator(actor, organization_id)
    person = _load_person(person_id, organization_id)
    person.is_active = True
    person.updated_at = datetime.utcnow()
    person.updated_by_user_id = actor_user.id
    db.session.commit()
    return _identity(person)


def get_person_hourly_wage(*, organization_id: str, person_id: int, actor) -> Decimal:
    actor_user = _load_user(actor)
    org = _load_organization(organization_id)
    if not (
        is_instance_owner(actor_user, org.id)
        or is_system_administrator(actor_user, org.id)
    ):
        raise PersonAuthorityError(PERSON_WAGE_READ_DENIED)
    person = _load_person(person_id, organization_id)
    return Decimal(person.hourly_wage).quantize(Decimal("0.01"))
