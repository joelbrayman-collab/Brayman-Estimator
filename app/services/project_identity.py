"""Project identity (Joel, 30 Oct 2026): Brayman Project # and Client Project #.

Brayman Project # (``Project.project_number``)
    Assigned automatically when the project record is created: ``BC-YYYY-NNNN`` for Brayman Construction (ORG-001),
    the year the project was created and the next number in that year. Another organization uses its own id as the
    prefix, so numbers never collide across companies. The number is taken from ``project_number_sequences`` inside
    the same transaction that inserts the project (one atomic "add one and read" statement; the database serialises
    writers), and the column is unique, so two projects created at the same moment can never share a number. The
    counter only counts up: a number is never reused, even after its project is closed or removed; gaps are fine.

    Lifecycle: the New Project form and the compact Start a New Project wizard collect details first; nothing is
    numbered until the project record itself is created (the form's Create / the wizard's Continue on Details). An
    abandoned form or wizard never uses a number. A Lead is a real project record and is numbered.

    Permanent: changing the client, name, address, scope, estimator or status never changes it. A change after
    assignment is refused unless made through ``correct_brayman_project_number`` (an administrative correction with a
    named person and a reason, recorded in ``project_identity_events``).

Client Project # (``Project.client_project_number``)
    The client's own reference (Lockwood Brothers' job number, a tender number, a customer job #): text, so letters,
    digits, hyphens, slashes, periods and leading zeros are kept exactly. Never generated; blank when there is none.
    Not unique; a possible duplicate for the same client is reported as a warning, not blocked. Office users can change
    it; every change is recorded with the previous and new values, who and when.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import List, Optional

from sqlalchemy import inspect, text

from app import db

ORG_PREFIXES = {"ORG-001": "BC"}  # migration r5e6f7a8b9c0 keeps the same map
FIELD_BRAYMAN = "BRAYMAN_PROJECT_NUMBER"
FIELD_CLIENT = "CLIENT_PROJECT_NUMBER"
CLIENT_NUMBER_MAX = 80
_CLIENT_NUMBER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 \-/.#_:()&]*$")
_COMPANY_TIME = "COMPANY-TIME-"


class ProjectIdentityError(ValueError):
    pass


def prefix_for(organization_id: str) -> str:
    return ORG_PREFIXES.get(organization_id) or re.sub(r"[^A-Z0-9-]", "", (organization_id or "").upper()) or "P"


def format_number(organization_id: str, year: int, value: int) -> str:
    return f"{prefix_for(organization_id)}-{year}-{value:04d}"


def _next_value(connection, organization_id: str, year: int) -> int:
    now = datetime.utcnow()
    connection.execute(text(
        "INSERT INTO project_number_sequences (organization_id, year, last_value, updated_at) VALUES (:o, :y, 1, :t) "
        "ON CONFLICT (organization_id, year) DO UPDATE SET last_value = project_number_sequences.last_value + 1, "
        "updated_at = :t"), {"o": organization_id, "y": year, "t": now})
    return connection.execute(text(
        "SELECT last_value FROM project_number_sequences WHERE organization_id = :o AND year = :y"),
        {"o": organization_id, "y": year}).scalar()


def issue_number(connection, organization_id: str, year: int) -> str:
    """The next unused Brayman Project # for the organization and year (skips any number already on a project)."""
    for _attempt in range(1000):
        number = format_number(organization_id, year, _next_value(connection, organization_id, year))
        exists = connection.execute(text("SELECT 1 FROM projects WHERE project_number = :n"), {"n": number}).first()
        if exists is None:
            return number
    raise ProjectIdentityError("Could not issue a project number.")


def assign_on_insert(connection, target) -> None:
    """Project before_insert (registered in app/models/project.py): give a new project its Brayman Project #."""
    if target.project_number:
        return
    created = target.created_at or datetime.utcnow()
    if not target.organization_id:
        from app.services.organizations import get_current_organization_id

        target.organization_id = get_current_organization_id()
    target.project_number = issue_number(connection, target.organization_id, created.year)
    target._identity_assigned = True


def record_on_insert(connection, target) -> None:
    """Project after_insert: the assignment goes into the identity history."""
    if not getattr(target, "_identity_assigned", False):
        return
    connection.execute(text(
        "INSERT INTO project_identity_events (organization_id, project_id, field, previous_value, new_value, "
        "actor_identifier, actor_user_id, reason, created_at) VALUES (:o, :p, :f, NULL, :n, :a, NULL, :r, :t)"),
        {"o": target.organization_id, "p": target.id, "f": FIELD_BRAYMAN, "n": target.project_number,
         "a": "CalibraytAI (automatic)", "r": "Assigned when the project was created", "t": datetime.utcnow()})
    target._identity_assigned = False


def guard_on_update(target) -> None:
    """Project before_update: a Brayman Project # never changes once assigned (except a recorded correction)."""
    history = inspect(target).attrs.project_number.history
    if not history.has_changes():
        return
    previous = history.deleted[0] if history.deleted else None
    if previous and not getattr(target, "_identity_correction", False):
        raise ProjectIdentityError(
            f"The Brayman Project # {previous} is permanent. An administrative correction needs a reason.")


# ---------------------------------------------------------------------------------------------- client project #
def clean_client_number(raw) -> Optional[str]:
    text_value = " ".join(("" if raw is None else str(raw)).split())
    if not text_value:
        return None
    if len(text_value) > CLIENT_NUMBER_MAX:
        raise ProjectIdentityError(f"Client Project # is at most {CLIENT_NUMBER_MAX} characters.")
    if not _CLIENT_NUMBER.match(text_value):
        raise ProjectIdentityError(
            "Client Project # can use letters, digits, spaces and - / . # _ : ( ) & (starting with a letter or digit).")
    return text_value


def possible_duplicates(project_or_client_id, client_number: Optional[str], *, organization_id: str,
                        exclude_project_id: Optional[int] = None) -> List:
    """Other projects of the same client with the same Client Project # (a warning, never a block)."""
    from app.models.project import Project

    if not client_number:
        return []
    client_id = getattr(project_or_client_id, "client_id", project_or_client_id)
    query = Project.query.filter(Project.organization_id == organization_id, Project.client_id == client_id,
                                 db.func.lower(Project.client_project_number) == client_number.lower())
    if exclude_project_id is not None:
        query = query.filter(Project.id != exclude_project_id)
    return query.all()


def _record(project, field: str, previous, new, *, actor: str, user_id=None, reason=None) -> None:
    from app.models.project import ProjectIdentityEvent

    db.session.add(ProjectIdentityEvent(organization_id=project.organization_id, project_id=project.id, field=field,
                                        previous_value=previous, new_value=new, actor_identifier=actor[:150],
                                        actor_user_id=user_id, reason=(reason or None)))


def set_client_project_number(project, raw, *, actor: str, user_id=None, reason: str = "") -> dict:
    """Set or change the Client Project # (blank clears it). Recorded with the previous and new values."""
    name = (actor or "").strip()
    if not name:
        raise ProjectIdentityError("A named person is required to change the Client Project #.")
    value = clean_client_number(raw)
    previous = project.client_project_number
    if value == previous:
        return {"changed": False, "duplicates": []}
    project.client_project_number = value
    _record(project, FIELD_CLIENT, previous, value, actor=name, user_id=user_id, reason=(reason or "").strip() or None)
    dupes = possible_duplicates(project, value, organization_id=project.organization_id, exclude_project_id=project.id)
    return {"changed": True, "duplicates": dupes}


def correct_brayman_project_number(project, new_number: str, *, actor: str, reason: str, user_id=None) -> None:
    """Administrative correction of a Brayman Project # (a genuine error only): named person and reason required,
    the new number must be unused, and the change is recorded. Not offered on any everyday page."""
    from app.models.project import Project

    name = (actor or "").strip()
    why = (reason or "").strip()
    if not name or not why:
        raise ProjectIdentityError("A correction needs a named person and a reason.")
    number = (new_number or "").strip().upper()
    if not re.match(r"^[A-Z0-9-]+-\d{4}-\d{4,}$", number):
        raise ProjectIdentityError("A Brayman Project # looks like BC-2026-0001.")
    if Project.query.filter(Project.project_number == number, Project.id != project.id).first() is not None:
        raise ProjectIdentityError(f"{number} is already another project's number.")
    previous = project.project_number
    project._identity_correction = True
    try:
        project.project_number = number
        _record(project, FIELD_BRAYMAN, previous, number, actor=name, user_id=user_id, reason=why)
        db.session.flush()
    finally:
        project._identity_correction = False


def identity_history(project) -> list:
    from app.models.project import ProjectIdentityEvent

    return (ProjectIdentityEvent.query.filter_by(organization_id=project.organization_id, project_id=project.id)
            .order_by(ProjectIdentityEvent.created_at.asc(), ProjectIdentityEvent.id.asc()).all())


# ---------------------------------------------------------------------------------------------- documents
def is_numbered_customer_project(project) -> bool:
    number = getattr(project, "project_number", None) or ""
    return bool(number) and not number.startswith(_COMPANY_TIME)


def reference_pairs(project) -> list:
    """[("Brayman Project #", "BC-2026-0001"), ("Client Project #", "L-2291")] for documents (only what exists)."""
    if project is None:
        return []
    pairs = []
    if is_numbered_customer_project(project):
        pairs.append(("Brayman Project #", project.project_number))
    if getattr(project, "client_project_number", None):
        pairs.append(("Client Project #", project.client_project_number))
    return pairs


def reference_line(project, separator: str = " · ") -> str:
    """"Brayman Project # BC-2026-0001 · Client Project # L-2291" (empty when neither exists)."""
    return separator.join(f"{label} {value}" for label, value in reference_pairs(project))
