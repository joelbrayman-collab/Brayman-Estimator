"""Person-to-User link and the dated loaded labour rate (FG-042 M1 / S2, approved by Joel 24 Nov 2026).

The employee register (People & Access, Employees) stays the one authoritative list of employees and employment
costs. This module adds two things on top of it and nothing else:

* a link from an employee (OrganizationPerson) to the sign-in user who enters that employee's time, so an approved
  time entry reaches the employee's cost record;
* a lookup of the employee's Loaded Labour Rate on a work date, from the cost profile in force that day. Profiles are
  never edited (insert-only), so the answer for a past date never changes when a later profile is saved.

A person whose time cannot be tied to an employee with a complete cost profile is never priced at some other
person's rate here. The caller gets ``None`` and decides how to label it (project labour cost uses the company rate
and says so).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from app import db

LOG = logging.getLogger(__name__)

CENT = Decimal("0.01")

BASIS_IN_FORCE = "IN_FORCE"
BASIS_PREDATES_FIRST_PROFILE = "PREDATES_FIRST_PROFILE"


class EmployeeLinkError(ValueError):
    """A plain-language refusal shown to the owner or System Administrator."""


@dataclass(frozen=True)
class DatedRate:
    person_id: int
    work_date: date
    loaded_rate: Decimal
    cost_profile_id: int
    effective_from: date
    basis: str


# ------------------------------------------------------------------------------------------------ the link
def link_person_to_user(organization_id: str, person_id: int, user_id: Optional[int], *, actor) -> object:
    """Link (or, with ``user_id=None``, unlink) an employee and a sign-in user. Owner / System Administrator only."""
    from app.models.person import OrganizationPerson
    from app.models.user import UserMembership
    from app.services.people_access import PeopleAccessError, require_people_administrator

    try:
        require_people_administrator(actor, organization_id)
    except PeopleAccessError as exc:
        raise EmployeeLinkError(str(exc)) from exc
    person = OrganizationPerson.query.filter_by(id=person_id, organization_id=organization_id).first()
    if person is None:
        raise EmployeeLinkError("Employee not found.")
    new_uid = None if user_id in (None, "", 0) else int(user_id)
    if person.user_id is not None and person.user_id != new_uid:
        # Cost is applied on read from this link, so changing it would re-price time already entered. Refuse.
        from app.models.time_entry import LabourTimeEntry

        if LabourTimeEntry.query.filter(LabourTimeEntry.organization_id == organization_id,
                                        LabourTimeEntry.worker_user_id == person.user_id).first() is not None:
            raise EmployeeLinkError("This user has time entries. Changing the link would change the cost of "
                                    "time already entered, so it is not allowed.")
    if new_uid is None:
        person.user_id = None
    else:
        uid = new_uid
        membership = UserMembership.query.filter_by(user_id=uid, organization_id=organization_id,
                                                    is_active=True).first()
        if membership is None:
            raise EmployeeLinkError("That user is not an active member of this company.")
        taken = (OrganizationPerson.query
                 .filter(OrganizationPerson.organization_id == organization_id,
                         OrganizationPerson.user_id == uid, OrganizationPerson.id != person.id).first())
        if taken is not None:
            raise EmployeeLinkError(f"That user is already linked to {taken.full_name}. A user can be linked "
                                    "to one employee only.")
        person.user_id = uid
    person.updated_at = datetime.utcnow()
    person.updated_by_user_id = getattr(actor, "id", None)
    db.session.commit()
    LOG.info("employee link: organization=%s person=%s user=%s actor=%s", organization_id, person.id,
             person.user_id, getattr(actor, "id", None))
    return person


def person_for_user(organization_id: str, user_id: int):
    from app.models.person import OrganizationPerson

    if user_id is None:
        return None
    return OrganizationPerson.query.filter_by(organization_id=organization_id, user_id=int(user_id)).first()


# ------------------------------------------------------------------------------------------------ dated rate
def _profile_date(profile) -> date:
    if profile.effective_from is not None:
        return profile.effective_from
    return profile.created_at.date()


def loaded_rate_on(person_id: int, day: date) -> Optional[DatedRate]:
    """The employee's loaded rate on a work date: the profile with the latest effective date on or before the day
    (the newest saved wins a tie). A day before the first profile uses the first profile and says so. ``None``
    when the employee has no usable profile."""
    from app.models.person import OrganizationPersonCostProfile as P

    profiles = (P.query.filter(P.person_id == person_id).order_by(P.id.asc()).all())
    usable = [p for p in profiles if p.loaded_rate is not None and Decimal(str(p.loaded_rate)) > 0]
    if not usable:
        return None
    in_force = [p for p in usable if _profile_date(p) <= day]
    if in_force:
        chosen = max(in_force, key=lambda p: (_profile_date(p), p.id))
        basis = BASIS_IN_FORCE
    else:
        chosen = min(usable, key=lambda p: (_profile_date(p), p.id))
        basis = BASIS_PREDATES_FIRST_PROFILE
    return DatedRate(person_id=person_id, work_date=day, loaded_rate=Decimal(str(chosen.loaded_rate)).quantize(CENT),
                     cost_profile_id=chosen.id, effective_from=_profile_date(chosen), basis=basis)


class UserRateBook:
    """Loaded rates for the users who entered time, looked up once per (user, day)."""

    def __init__(self, organization_id: str):
        self.organization_id = organization_id
        self._person = {}
        self._rate = {}

    def on(self, user_id, day: date) -> Optional[DatedRate]:
        if user_id is None:
            return None
        if user_id not in self._person:
            person = person_for_user(self.organization_id, user_id)
            self._person[user_id] = person.id if person is not None else None
        person_id = self._person[user_id]
        if person_id is None:
            return None
        key = (person_id, day)
        if key not in self._rate:
            self._rate[key] = loaded_rate_on(person_id, day)
        return self._rate[key]
