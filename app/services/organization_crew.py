"""FG-035 SCH-B optional Organization Crew configuration.

Period membership is only enough to answer who was on a named crew during
a scheduled window. This is not HR and not FG-008 Crew Template.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from app import db
from app.models.organization_crew import (
    CREW_STATUS_ACTIVE,
    CREW_STATUS_INACTIVE,
    OrganizationCrew,
    OrganizationCrewMember,
)
from app.models.user import User, UserMembership
from app.services.organizations import get_current_organization_id


class CrewError(Exception):
    """Raised when a Crew mutation cannot complete."""


class CrewNotFoundError(CrewError):
    """Raised when a Crew row is missing or cross-org."""


def _org_id(organization_id: Optional[str] = None) -> str:
    return organization_id or get_current_organization_id()


def parse_crew_date(value) -> date:
    if value is None or str(value).strip() == "":
        raise CrewError("Choose a date.")
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    try:
        return date.fromisoformat(str(value).strip())
    except ValueError as exc:
        raise CrewError("Enter a valid date.") from exc


def require_active_org_user(user_id: int, organization_id: str) -> User:
    user = db.session.get(User, user_id)
    if user is None or not user.is_active:
        raise CrewNotFoundError("That person was not found.")
    membership = UserMembership.query.filter_by(
        user_id=user.id,
        organization_id=organization_id,
        is_active=True,
    ).first()
    if membership is None:
        raise CrewError("That person does not belong to this organization.")
    return user


def list_org_people(organization_id: Optional[str] = None) -> list[User]:
    org_id = _org_id(organization_id)
    return (
        User.query.join(UserMembership, UserMembership.user_id == User.id)
        .filter(
            UserMembership.organization_id == org_id,
            UserMembership.is_active.is_(True),
            User.is_active.is_(True),
        )
        .order_by(User.display_name, User.id)
        .all()
    )


def get_crew(crew_id: int, *, organization_id: Optional[str] = None) -> OrganizationCrew:
    org_id = _org_id(organization_id)
    crew = OrganizationCrew.query.filter_by(id=crew_id, organization_id=org_id).first()
    if crew is None:
        raise CrewNotFoundError("Crew not found.")
    return crew


def list_crews(organization_id: Optional[str] = None, *, include_inactive: bool = False):
    org_id = _org_id(organization_id)
    query = OrganizationCrew.query.filter_by(organization_id=org_id)
    if not include_inactive:
        query = query.filter_by(status=CREW_STATUS_ACTIVE)
    return query.order_by(OrganizationCrew.name, OrganizationCrew.id).all()


def create_crew(*, name: str, organization_id: Optional[str] = None, commit: bool = True) -> OrganizationCrew:
    org_id = _org_id(organization_id)
    cleaned = (name or "").strip()
    if not cleaned:
        raise CrewError("Enter a crew name.")
    existing = OrganizationCrew.query.filter_by(
        organization_id=org_id,
        name=cleaned,
    ).first()
    if existing is not None:
        raise CrewError("A crew with that name already exists. Rename the retired crew first.")
    crew = OrganizationCrew(
        organization_id=org_id,
        name=cleaned,
        status=CREW_STATUS_ACTIVE,
    )
    db.session.add(crew)
    if commit:
        db.session.commit()
    else:
        db.session.flush()
    return crew


def retire_crew(crew_id: int, *, organization_id: Optional[str] = None, commit: bool = True) -> OrganizationCrew:
    crew = get_crew(crew_id, organization_id=organization_id)
    if crew.status == CREW_STATUS_INACTIVE:
        return crew
    crew.status = CREW_STATUS_INACTIVE
    crew.updated_at = datetime.utcnow()
    if commit:
        db.session.commit()
    return crew


def membership_overlaps_window(member: OrganizationCrewMember, window_start: date, window_end: date) -> bool:
    if member.effective_from > window_end:
        return False
    if member.effective_to is None:
        return True
    return member.effective_to >= window_start


def users_on_crew_during_window(
    crew_id: int,
    window_start: date,
    window_end: date,
    *,
    organization_id: Optional[str] = None,
) -> list[User]:
    org_id = _org_id(organization_id)
    crew = get_crew(crew_id, organization_id=org_id)
    users = []
    seen = set()
    for member in OrganizationCrewMember.query.filter_by(
        organization_id=org_id,
        crew_id=crew.id,
    ).all():
        if not membership_overlaps_window(member, window_start, window_end):
            continue
        if member.user_id in seen:
            continue
        seen.add(member.user_id)
        if member.user is not None:
            users.append(member.user)
    return users


def _periods_overlap(left_from: date, left_to: Optional[date], right_from: date, right_to: Optional[date]) -> bool:
    left_end = left_to or date.max
    right_end = right_to or date.max
    return left_from <= right_end and right_from <= left_end


def add_crew_member(
    crew_id: int,
    *,
    user_id: int,
    effective_from,
    effective_to=None,
    organization_id: Optional[str] = None,
    commit: bool = True,
) -> OrganizationCrewMember:
    org_id = _org_id(organization_id)
    crew = get_crew(crew_id, organization_id=org_id)
    require_active_org_user(user_id, org_id)
    start = parse_crew_date(effective_from)
    end = parse_crew_date(effective_to) if effective_to not in (None, "") else None
    if end is not None and end < start:
        raise CrewError("The last day cannot be before the first day.")
    existing = OrganizationCrewMember.query.filter_by(
        organization_id=org_id,
        crew_id=crew.id,
        user_id=user_id,
    ).all()
    for row in existing:
        if _periods_overlap(row.effective_from, row.effective_to, start, end):
            raise CrewError("That person already has overlapping dates on this crew.")
    member = OrganizationCrewMember(
        organization_id=org_id,
        crew_id=crew.id,
        user_id=user_id,
        effective_from=start,
        effective_to=end,
    )
    db.session.add(member)
    if commit:
        db.session.commit()
    else:
        db.session.flush()
    return member


def close_crew_membership(
    member_id: int,
    *,
    effective_to,
    organization_id: Optional[str] = None,
    commit: bool = True,
) -> OrganizationCrewMember:
    org_id = _org_id(organization_id)
    member = OrganizationCrewMember.query.filter_by(
        id=member_id,
        organization_id=org_id,
    ).first()
    if member is None:
        raise CrewNotFoundError("Crew membership not found.")
    end = parse_crew_date(effective_to)
    if end < member.effective_from:
        raise CrewError("The last day cannot be before the first day.")
    others = OrganizationCrewMember.query.filter(
        OrganizationCrewMember.organization_id == org_id,
        OrganizationCrewMember.crew_id == member.crew_id,
        OrganizationCrewMember.user_id == member.user_id,
        OrganizationCrewMember.id != member.id,
    ).all()
    for row in others:
        if _periods_overlap(row.effective_from, row.effective_to, member.effective_from, end):
            raise CrewError("That person already has overlapping dates on this crew.")
    member.effective_to = end
    if commit:
        db.session.commit()
    return member
