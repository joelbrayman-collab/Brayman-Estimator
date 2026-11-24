"""Who may see internal financial figures (Joel's ruling 1, 2 Nov 2026).

Two separate permissions, so they can be granted separately later:

* ``can_view_employee_cost``: compensation components and each employee's Loaded Labour Rate (wages, truck, fuel,
  tools, RRSP, benefits, WSIB). Owner or System Administrator only — the people who may read wages.
* ``can_view_project_economics``: project-level cost, price and profit (the Internal Project Financial Summary's
  totals and the live internal P&L) with no per-employee wage or benefit detail. Owner, System Administrator, or a
  person holding the PROJECT_PERFORMANCE grant (FG-042 S2b, 24 Nov 2026). The grant widens this check only; it never
  widens employee cost detail.

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


def has_project_performance_grant(user, organization_id: Optional[str]) -> bool:
    """The explicit PROJECT_PERFORMANCE grant (FG-042 S2b). A field-only member never has it in effect."""
    from app.services.access_domains import (
        ACCESS_DOMAIN_PROJECT_PERFORMANCE,
        membership_has_access_domain,
        user_is_field_only,
    )

    if user is None or not getattr(user, "is_authenticated", True) or not organization_id:
        return False
    try:
        if user_is_field_only(user, organization_id):
            return False
        return membership_has_access_domain(user, organization_id, ACCESS_DOMAIN_PROJECT_PERFORMANCE)
    except Exception:  # noqa: BLE001 - fail closed
        return False


def can_view_project_economics(user, organization_id: Optional[str]) -> bool:
    """Owner, System Administrator, or a person holding the project-performance grant. This widens project
    economics only; it never widens ``can_view_employee_cost``."""
    return _is_owner_or_system_administrator(user, organization_id) or has_project_performance_grant(
        user, organization_id)


def require_project_economics():
    """Abort 403 unless the current request user may see project economics (cost, price, profit)."""
    from flask import abort
    from flask_login import current_user

    from app.services.organizations import OrganizationAccessError, get_current_organization_id

    if not getattr(current_user, "is_authenticated", False):
        abort(403)
    try:
        org_id = get_current_organization_id()
    except OrganizationAccessError:
        abort(403)
    if not can_view_project_economics(current_user, org_id):
        abort(403)


def can_issue_customer_estimate(user, organization_id: Optional[str]) -> bool:
    """Who may freeze the customer estimate for Ben's approval and send it to him (3 Nov 2026).

    The customer estimate holds no wage or internal-economics figures, so this is exactly the rule that governs
    estimate sign-off and sending the proposal to the client today: an active office member of the organization
    (the office wall plus the field-only refusal; access_domains.has_office_scheduling_authority). Neither broader
    nor narrower than that."""
    from app.services.access_domains import has_office_scheduling_authority

    if user is None or not getattr(user, "is_authenticated", True) or not organization_id:
        return False
    return has_office_scheduling_authority(user, organization_id)
