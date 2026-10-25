"""Project Lead (Joel, 24 Oct 2026, decision 1).

An optional Project Lead on a project: one of the company's own authorized people — an active person with an
active membership in the project's organization (office staff or crew, the People & Access list), never a
deactivated person and never anyone of another organization. Existing projects start unassigned.

The Project Lead is a name on the project, nothing more:

* It grants no permission. Every access check stays the existing one (People & Access, Field-only, the office
  wall, the owner and System Administrator decisions). Nothing in the platform reads this field to allow anything.
* It is kept apart from crew assignments (the work schedule) and appointment assignees (the Company Calendar).

It is shown on the Project Hub, on the project's card in the Company Calendar, and in the Start a New Project and
Manage a Project wizards. There is no project-field audit table in the platform; a change made from a wizard is
written to that wizard's own history (wizard_run_events).
"""

from __future__ import annotations

from typing import Optional

from app import db
from app.models.project import Project
from app.models.user import User, UserMembership

UNASSIGNED = "Unassigned"


class ProjectLeadError(Exception):
    """The project or the person cannot be used."""


def lead_choices(organization_id: str) -> list[dict]:
    """The company's authorized people (active user, active membership in this organization), by name."""
    from app.services.access_domains import membership_is_field_only

    rows = (
        db.session.query(User, UserMembership)
        .join(UserMembership, UserMembership.user_id == User.id)
        .filter(UserMembership.organization_id == organization_id, UserMembership.is_active.is_(True),
                User.is_active.is_(True))
        .order_by(User.display_name, User.id)
        .all()
    )
    out, seen = [], set()
    for user, membership in rows:
        if user.id in seen:
            continue
        seen.add(user.id)
        field = membership_is_field_only(membership)
        out.append({"id": user.id, "name": user.display_name or user.email,
                    "label": (user.display_name or user.email) + (" (Field crew)" if field else "")})
    return out


def _authorized_person(organization_id: str, user_id: int) -> User:
    user = db.session.get(User, user_id)
    if user is None or not user.is_active:
        raise ProjectLeadError("Choose a Project Lead from this company's people.")
    membership = UserMembership.query.filter_by(user_id=user.id, organization_id=organization_id,
                                                is_active=True).first()
    if membership is None:
        raise ProjectLeadError("Choose a Project Lead from this company's people.")
    return user


def parse_lead(value) -> Optional[int]:
    """'' / None / 'unassigned' → None (no Project Lead); a number → that person's id."""
    text = str(value or "").strip()
    if not text or text.lower() == "unassigned":
        return None
    if not text.isdigit():
        raise ProjectLeadError("Choose a Project Lead from this company's people.")
    return int(text)


def set_project_lead(*, organization_id: str, project_id: int, user_id, commit: bool = True) -> bool:
    """Set (or clear, with None) the Project Lead of this company's project. Returns True when it changed."""
    if not organization_id or project_id is None:
        raise ProjectLeadError("Project not found.")
    project = Project.query.filter_by(id=project_id, organization_id=organization_id).one_or_none()
    if project is None:
        raise ProjectLeadError("Project not found.")
    lead_id = parse_lead(user_id) if not isinstance(user_id, int) else user_id
    if lead_id is not None:
        lead_id = _authorized_person(organization_id, lead_id).id
    if project.project_lead_user_id == lead_id:
        return False
    project.project_lead_user_id = lead_id
    if commit:
        db.session.commit()
    else:
        db.session.flush()
    return True


def lead_name(project) -> str:
    """The Project Lead's name, or 'Unassigned'. A lead who has since left the company is named as such."""
    if project is None or not project.project_lead_user_id:
        return UNASSIGNED
    user = project.project_lead
    if user is None:
        return UNASSIGNED
    name = user.display_name or user.email
    active = user.is_active and UserMembership.query.filter_by(
        user_id=user.id, organization_id=project.organization_id, is_active=True).first() is not None
    return name if active else f"{name} (no longer active)"
