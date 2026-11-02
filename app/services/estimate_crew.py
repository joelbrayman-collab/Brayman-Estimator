"""The crew on an estimate (Joel, 2 Nov 2026): who does the labour and their share of the hours.

Real labour cost on the Internal Project Financial Summary = the estimate's labour hours x each crew member's Loaded
Labour Rate x their share. Only an active employee with a complete cost profile can be assigned (an employee without
one cannot be put on a crew). Shares default to equal. Changing the crew ends the earlier rows and adds new ones, so
the history is kept; the rates used when the estimate is approved are frozen in its approval record.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import List, Optional

from app import db
from app.models.person import EstimateCrewMember, OrganizationPerson
from app.services.labour_cost_profile import current_profile, is_complete

CREW_NOT_ASSIGNED = "Crew not assigned — real labour cost not available"


class EstimateCrewError(ValueError):
    """A plain-language refusal shown to the person."""


def current_rows(estimate) -> List[EstimateCrewMember]:
    return (EstimateCrewMember.query.filter_by(estimate_id=estimate.id, removed_at=None)
            .order_by(EstimateCrewMember.id.asc()).all())


def crew(estimate) -> List[dict]:
    """The current crew: each member with their share and current Loaded Labour Rate (None if no longer complete)."""
    out = []
    for row in current_rows(estimate):
        person = row.person or db.session.get(OrganizationPerson, row.person_id)
        profile = current_profile(person.id)
        complete = is_complete(profile, person) and bool(person.is_active)
        out.append({"row": row, "person": person, "name": person.full_name, "share": Decimal(str(row.share)),
                    "loaded_rate": Decimal(str(profile.loaded_rate)) if complete else None, "complete": complete})
    return out


def crew_rates(estimate) -> Optional[list]:
    """[{name, loaded_rate, share}] when every crew member has a current complete profile; None otherwise."""
    rows = crew(estimate)
    if not rows or any(not r["complete"] for r in rows):
        return None
    return [{"name": r["name"], "loaded_rate": r["loaded_rate"], "share": r["share"]} for r in rows]


def crew_problem(estimate) -> Optional[str]:
    rows = crew(estimate)
    if not rows:
        return CREW_NOT_ASSIGNED
    missing = [r["name"] for r in rows if not r["complete"]]
    if missing:
        return (f"{', '.join(missing)} on the crew {'has' if len(missing) == 1 else 'have'} no current cost profile — "
                "real labour cost not available")
    return None


def _share(raw) -> Decimal:
    text = ("" if raw is None else str(raw)).strip().replace("%", "")
    if text == "":
        return Decimal("1")
    try:
        value = Decimal(text)
    except InvalidOperation:
        raise EstimateCrewError(f"A share of the hours must be a number (you entered “{raw}”).") from None
    if not value.is_finite() or value <= 0:
        raise EstimateCrewError("A share of the hours must be more than 0.")
    return value.quantize(Decimal("0.0001"))


def set_crew(estimate, *, organization_id: str, person_ids, shares=None, actor: str) -> List[EstimateCrewMember]:
    """Replace the estimate's crew. ``shares`` maps person id to a share (blank = equal shares)."""
    name = (actor or "").strip()[:150]
    if not name:
        raise EstimateCrewError("A person must assign the crew.")
    if estimate.project.organization_id != organization_id:
        raise EstimateCrewError("Estimate not found.")
    ids = []
    for raw in person_ids or []:
        try:
            pid = int(raw)
        except (TypeError, ValueError):
            raise EstimateCrewError("Choose employees from the list.") from None
        if pid not in ids:
            ids.append(pid)
    chosen = []
    for pid in ids:
        person = db.session.get(OrganizationPerson, pid)
        if person is None or person.organization_id != organization_id:
            raise EstimateCrewError("Choose employees from the list.")
        if not person.is_active:
            raise EstimateCrewError(f"{person.full_name} is not an active employee.")
        if not is_complete(current_profile(person.id), person):
            raise EstimateCrewError(f"{person.full_name} has no complete cost profile. Enter it under People & "
                                    "Access → Employees before putting them on a crew.")
        chosen.append((person, _share((shares or {}).get(pid) or (shares or {}).get(str(pid)))))
    now = datetime.utcnow()
    for row in current_rows(estimate):
        row.removed_at = now
        row.removed_by_name = name
    added = []
    for person, share in chosen:
        row = EstimateCrewMember(organization_id=organization_id, estimate_id=estimate.id, person_id=person.id,
                                 share=share, assigned_at=now, assigned_by_name=name)
        db.session.add(row)
        added.append(row)
    db.session.commit()
    return added
