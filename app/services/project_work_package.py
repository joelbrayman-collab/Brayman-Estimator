"""Confirm project scope. Does not estimate, price, or request quotes."""

from __future__ import annotations

from datetime import datetime

from app import db
from app.models.project import Project
from app.models.project_work_package import (
    DELIVERY_VALUES,
    SOURCE_CONTRACTOR,
    SOURCE_PLAN,
    STATUS_CONFIRMED,
    STATUS_RETIRED,
    ProjectWorkPackage,
)
from app.models.work_structure import (
    WORK_STATUS_ACTIVE,
    WorkElementTemplate,
    WorkType,
)
from app.plan_intelligence.models import PlanDocument
from app.services.estimates import EstimateServiceError

_REJECTED_ACTORS = {"system", "ai", "automatic", "calibrytai"}


class ProjectWorkPackageError(EstimateServiceError):
    """Fail-closed project scope error."""


def _require_actor(actor):
    name = (actor or "").strip()
    if not name or name.lower() in _REJECTED_ACTORS:
        raise ProjectWorkPackageError("A person must confirm this project work.")
    return name[:150]


def _project(organization_id, project_id):
    project = Project.query.filter_by(
        id=project_id,
        organization_id=organization_id,
    ).first()
    if project is None:
        raise ProjectWorkPackageError("Project not found.")
    return project


def work_choices(organization_id):
    """Active catalog elements for this company, including the shared baseline."""
    return (
        WorkElementTemplate.query.join(WorkType)
        .filter(WorkElementTemplate.status == WORK_STATUS_ACTIVE)
        .filter(WorkType.status == WORK_STATUS_ACTIVE)
        .filter(
            db.or_(
                WorkElementTemplate.organization_id.is_(None),
                WorkElementTemplate.organization_id == organization_id,
            )
        )
        .order_by(
            WorkType.sort_order.asc(),
            WorkElementTemplate.sort_order.asc(),
            WorkElementTemplate.display_name.asc(),
        )
        .all()
    )


def list_confirmed(organization_id, project_id):
    _project(organization_id, project_id)
    return (
        ProjectWorkPackage.query.filter_by(
            organization_id=organization_id,
            project_id=project_id,
            status=STATUS_CONFIRMED,
        )
        .order_by(ProjectWorkPackage.id.asc())
        .all()
    )


def project_plans(organization_id, project_id):
    _project(organization_id, project_id)
    return (
        PlanDocument.query.filter_by(project_id=project_id, archived_at=None)
        .order_by(PlanDocument.id.asc())
        .all()
    )


def confirm_package(
    *,
    organization_id,
    project_id,
    work_element_template_id,
    delivery,
    actor,
    plan_document_id=None,
    user_id=None,
):
    project = _project(organization_id, project_id)
    name = _require_actor(actor)
    if delivery not in DELIVERY_VALUES:
        raise ProjectWorkPackageError("Choose our crew or a subcontractor.")
    template = db.session.get(WorkElementTemplate, work_element_template_id)
    if template is None or template.status != WORK_STATUS_ACTIVE:
        raise ProjectWorkPackageError("Choose work from the work catalog.")
    if template.organization_id not in (None, organization_id):
        raise ProjectWorkPackageError("Choose work from the work catalog.")
    if template.work_type is None or template.work_type.status != WORK_STATUS_ACTIVE:
        raise ProjectWorkPackageError("Choose work from the work catalog.")
    source = SOURCE_CONTRACTOR
    plan_id = None
    if plan_document_id:
        document = db.session.get(PlanDocument, plan_document_id)
        if document is None or document.project_id != project.id or document.archived_at:
            raise ProjectWorkPackageError("That plan is not on this project.")
        source = SOURCE_PLAN
        plan_id = document.id
    now = datetime.utcnow()
    package = ProjectWorkPackage(
        organization_id=organization_id,
        project_id=project.id,
        work_element_template_id=template.id,
        delivery=delivery,
        status=STATUS_CONFIRMED,
        source_kind=source,
        plan_document_id=plan_id,
        user_id=user_id,
        actor_display_name=name,
        confirmed_at=now,
        created_at=now,
        updated_at=now,
    )
    db.session.add(package)
    db.session.commit()
    db.session.refresh(package)
    return package


def retire_package(*, organization_id, project_id, package_id, actor):
    _require_actor(actor)
    package = ProjectWorkPackage.query.filter_by(
        id=package_id,
        organization_id=organization_id,
        project_id=project_id,
        status=STATUS_CONFIRMED,
    ).first()
    if package is None:
        raise ProjectWorkPackageError("Project work not found.")
    now = datetime.utcnow()
    package.status = STATUS_RETIRED
    package.retired_at = now
    package.updated_at = now
    db.session.commit()
    return package
