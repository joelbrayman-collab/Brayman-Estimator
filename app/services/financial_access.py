"""Who may see internal financial figures (Joel's ruling 1, 2 Nov 2026).

Two separate permissions, so they can be granted separately later:

* ``can_view_employee_cost``: compensation components and each employee's Loaded Labour Rate (wages, truck, fuel,
  tools, RRSP, benefits, WSIB). Owner or System Administrator only — the people who may read wages.
* ``can_view_project_economics``: project-level cost, price and profit (the Internal Project Financial Summary's
  totals and the live internal P&L) with no per-employee wage or benefit detail. Today also Owner or System
  Administrator only. A future "project performance" grant for authorized project managers would widen this check
  only; it would not widen employee cost detail. That view is not built in this release.

A page that shows both requires both: where a viewer may see project economics but not employee cost, the summary is
rendered without the crew's names and rates (``employee_detail=False``).
"""

from __future__ import annotations

from typing import Optional


def _is_owner_or_system_administrator(user, organization_id: Optional[str]) -> bool:
    from app.services.documents.access import is_people_admin

    if user is None or not getattr(user, "is_authenticated", True) or not organization_id:
        return False
    return is_people_admin(user, organization_id)


def can_view_employee_cost(user, organization_id: Optional[str]) -> bool:
    return _is_owner_or_system_administrator(user, organization_id)


def can_view_project_economics(user, organization_id: Optional[str]) -> bool:
    # Future: or the user holds an explicit project-performance grant (not built).
    return _is_owner_or_system_administrator(user, organization_id)
