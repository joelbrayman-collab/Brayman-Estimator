"""Confirm project scope. Does not price or request quotes.

Confirmed project work is selected work (Joel, 30 Oct 2026: Selected Work is the single scope owner; no third
table). The former project_work_packages table is kept for history and is no longer written.
"""

from __future__ import annotations

from app import db
from app.models.project import Project
from app.models.project_work_package import (
    DELIVERY_INTERNAL,
    DELIVERY_LABELS,
    DELIVERY_SUBCONTRACT,
    DELIVERY_VALUES,
    SOURCE_CONTRACTOR,
    SOURCE_PLAN,
    STATUS_CONFIRMED,
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


class ConfirmedWork:
    """A confirmed piece of project scope, read from selected work (the single scope owner, Joel 30 Oct 2026).

    Project work used to be a separate ProjectWorkPackage row. It is now the selected-work package itself, with its
    catalogue element and plan recorded on it, so the scope, the estimate and the project plan cannot disagree."""

    status = STATUS_CONFIRMED

    def __init__(self, stage, project_id):
        self.stage = stage
        self.id = stage.id
        self.organization_id = stage.organization_id
        self.project_id = project_id
        self.work_element_template_id = stage.work_element_template_id
        self.plan_document_id = stage.plan_document_id
        self.actor_display_name = stage.decided_by or ""
        self.confirmed_at = stage.decided_at or stage.created_at

    @property
    def work_element_template(self):
        if self.work_element_template_id is None:
            return None
        return db.session.get(WorkElementTemplate, self.work_element_template_id)

    @property
    def plan_document(self):
        if self.plan_document_id is None:
            return None
        return db.session.get(PlanDocument, self.plan_document_id)

    @property
    def source_kind(self):
        return SOURCE_PLAN if self.plan_document_id else SOURCE_CONTRACTOR

    @property
    def delivery(self):
        from app.models.guided_estimating import RESP_SUBCONTRACTED

        return DELIVERY_SUBCONTRACT if self.stage.responsibility == RESP_SUBCONTRACTED else DELIVERY_INTERNAL

    @property
    def delivery_label(self):
        return DELIVERY_LABELS.get(self.delivery, self.delivery)

    @property
    def work_name(self):
        return self.stage.display_name


def _scope_rows(organization_id, project_id):
    from app.services import guided_estimating as G
    from app.services import selected_work as SW

    guided = G.get_guided(organization_id, project_id)
    if guided is None or not SW.is_selected_work(guided):
        return guided, []
    return guided, SW.work_items(guided)


def list_confirmed(organization_id, project_id):
    _project(organization_id, project_id)
    _guided, rows = _scope_rows(organization_id, project_id)
    return [ConfirmedWork(row, project_id) for row in rows]


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
    plan_id = None
    if plan_document_id:
        document = db.session.get(PlanDocument, plan_document_id)
        if document is None or document.project_id != project.id or document.archived_at:
            raise ProjectWorkPackageError("That plan is not on this project.")
        plan_id = document.id
    from app.models.guided_estimating import RESP_INTERNAL, RESP_SUBCONTRACTED
    from app.services import guided_estimating as G
    from app.services import selected_work as SW

    try:
        guided = SW.ensure_scope(organization_id, project.id, actor=name, user_id=user_id)
        if not SW.is_selected_work(guided):
            raise ProjectWorkPackageError("This project's estimate uses the earlier stage list. Add work from the "
                                          "estimate's work page.")
        existing = next((r for r in SW.work_items(guided) if r.work_element_template_id == template.id), None)
        if existing is None:
            added = SW.add_work(guided, custom_name=template.display_name, actor=name, user_id=user_id,
                                defer_estimate=True)
            row = added[0] if added else next(
                r for r in SW.work_items(guided) if r.display_name == " ".join(template.display_name.split())[:120])
        else:
            row = existing
        row.work_element_template_id = template.id
        if plan_id is not None:
            row.plan_document_id = plan_id
        db.session.commit()
        wanted = RESP_SUBCONTRACTED if delivery == DELIVERY_SUBCONTRACT else RESP_INTERNAL
        if not row.is_split and row.responsibility != wanted:
            SW.set_responsibility(guided, row, wanted, actor=name, user_id=user_id, defer_estimate=True)
    except (SW.SelectedWorkError, G.GuidedEstimatingError) as exc:
        db.session.rollback()
        raise ProjectWorkPackageError(str(exc)) from exc
    db.session.refresh(row)
    return ConfirmedWork(row, project.id)


def retire_package(*, organization_id, project_id, package_id, actor):
    name = _require_actor(actor)
    _project(organization_id, project_id)
    from app.services import guided_estimating as G
    from app.services import selected_work as SW

    guided, rows = _scope_rows(organization_id, project_id)
    row = next((r for r in rows if r.id == package_id), None)
    if row is None:
        raise ProjectWorkPackageError("Project work not found.")
    try:
        SW.remove_work(guided, row, actor=name, confirmed=True, defer_estimate=True)
    except (SW.SelectedWorkError, G.GuidedEstimatingError) as exc:
        db.session.rollback()
        raise ProjectWorkPackageError(str(exc)) from exc
    return ConfirmedWork(row, project_id)
