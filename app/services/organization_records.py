"""R01 service-boundary tenancy: reload organization-owned records.

Mutating services must not trust a caller-loaded ORM object. Resolve the
acting organization, then reload by primary key AND that organization.
Missing and cross-organization are indistinguishable.
"""

from __future__ import annotations

from flask import has_request_context
from flask_login import current_user

from app.models.project import Project
from app.services.organizations import get_current_organization_id
from app.services.shared_api import get_organization_project


class OrganizationRecordNotFoundError(LookupError):
    """Record is missing or not in the acting organization."""


def acting_organization_id(organization_id=None) -> str:
    """Return the organization the current actor is allowed to mutate as.

    Authenticated HTTP uses membership only (spoofed organization_id is ignored).
    CLI / tests without a request may pass an explicit organization_id.
    """
    authenticated = has_request_context() and getattr(
        current_user, "is_authenticated", False
    )
    if authenticated:
        return get_current_organization_id()
    if organization_id:
        return organization_id
    return get_current_organization_id()


def record_primary_key(record_or_id):
    if record_or_id is None or isinstance(record_or_id, bool):
        return None
    if isinstance(record_or_id, int):
        return record_or_id
    pk = getattr(record_or_id, "id", None)
    if pk is not None:
        return pk
    try:
        return int(record_or_id)
    except (TypeError, ValueError):
        return None


def _raise_not_found(error_class, message):
    raise (error_class or OrganizationRecordNotFoundError)(message)


def require_organization_project(
    project_or_id,
    *,
    organization_id=None,
    error_class=None,
    message="Not found.",
) -> Project:
    """Reload a Project for the acting organization. Do not trust the object."""
    org_id = acting_organization_id(organization_id)
    pk = record_primary_key(project_or_id)
    if pk is None:
        _raise_not_found(error_class, message)
    project = get_organization_project(org_id, int(pk))
    if project is None:
        _raise_not_found(error_class, message)
    return project


def require_organization_owned(
    model,
    record_or_id,
    *,
    organization_id=None,
    error_class=None,
    message="Not found.",
    extra_filters=None,
):
    """Reload a row that itself stores organization_id."""
    org_id = acting_organization_id(organization_id)
    pk = record_primary_key(record_or_id)
    if pk is None:
        _raise_not_found(error_class, message)
    query = model.query.filter_by(id=pk, organization_id=org_id)
    if extra_filters:
        query = query.filter_by(**extra_filters)
    row = query.first()
    if row is None:
        _raise_not_found(error_class, message)
    return row


def require_organization_estimate(
    estimate_or_id,
    *,
    organization_id=None,
    error_class=None,
    message="Not found.",
):
    from app.models.estimate import Estimate

    org_id = acting_organization_id(organization_id)
    pk = record_primary_key(estimate_or_id)
    if pk is None:
        _raise_not_found(error_class, message)
    row = (
        Estimate.query.join(Project, Estimate.project_id == Project.id)
        .filter(Estimate.id == pk, Project.organization_id == org_id)
        .first()
    )
    if row is None:
        _raise_not_found(error_class, message)
    return row


def require_organization_estimate_version(
    version_or_id,
    *,
    organization_id=None,
    error_class=None,
    message="Not found.",
):
    from app.models.estimate import Estimate, EstimateVersion

    org_id = acting_organization_id(organization_id)
    pk = record_primary_key(version_or_id)
    if pk is None:
        _raise_not_found(error_class, message)
    row = (
        EstimateVersion.query.join(Estimate, EstimateVersion.estimate_id == Estimate.id)
        .join(Project, Estimate.project_id == Project.id)
        .filter(EstimateVersion.id == pk, Project.organization_id == org_id)
        .first()
    )
    if row is None:
        _raise_not_found(error_class, message)
    return row


def require_organization_change_order(
    change_order_or_id,
    *,
    organization_id=None,
    error_class=None,
    message="Not found.",
):
    from app.project_controls.models import ChangeOrder

    org_id = acting_organization_id(organization_id)
    pk = record_primary_key(change_order_or_id)
    if pk is None:
        _raise_not_found(error_class, message)
    row = (
        ChangeOrder.query.join(Project, ChangeOrder.project_id == Project.id)
        .filter(ChangeOrder.id == pk, Project.organization_id == org_id)
        .first()
    )
    if row is None:
        _raise_not_found(error_class, message)
    return row


def require_organization_change_order_item(
    item_or_id,
    *,
    organization_id=None,
    error_class=None,
    message="Not found.",
):
    from app.project_controls.models import ChangeOrder, ChangeOrderItem

    org_id = acting_organization_id(organization_id)
    pk = record_primary_key(item_or_id)
    if pk is None:
        _raise_not_found(error_class, message)
    row = (
        ChangeOrderItem.query.join(
            ChangeOrder, ChangeOrderItem.change_order_id == ChangeOrder.id
        )
        .join(Project, ChangeOrder.project_id == Project.id)
        .filter(ChangeOrderItem.id == pk, Project.organization_id == org_id)
        .first()
    )
    if row is None:
        _raise_not_found(error_class, message)
    return row
