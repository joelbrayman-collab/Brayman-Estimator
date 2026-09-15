"""FG-035 TAX/WBS work-structure catalog and Project seed.

Projects owns this service. Estimating remains owner of LabourTask snapshots.
"""

from __future__ import annotations

import re
from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import or_

from app import db
from app.models.estimate import EstimateVersion
from app.models.labour_engine import EstimateLabourSnapshot, LabourTask
from app.models.project import Project
from app.models.work_structure import (
    SCOPE_EXTRA_WORK,
    SCOPE_ORIGINAL,
    SEED_ELIGIBLE_VERSION_STATUSES,
    SOURCE_BASELINE,
    SOURCE_ESTIMATE_SEED,
    SOURCE_ORGANIZATION,
    SOURCE_PROJECT,
    WORK_STATUS_ACTIVE,
    WORK_STATUS_INACTIVE,
    ProjectWorkActivity,
    ProjectWorkElement,
    ProjectWorkStructureSeed,
    WorkActivityTemplate,
    WorkElementTemplate,
    WorkType,
)
from app.services.organizations import get_current_organization_id


class WorkStructureError(ValueError):
    """Raised when a work-structure operation cannot complete."""


def _org_id(organization_id: Optional[str] = None) -> str:
    return organization_id or get_current_organization_id()


def _code(value: str) -> str:
    text = re.sub(r"[^A-Za-z0-9]+", "-", (value or "").strip().upper()).strip("-")
    return text[:80]


def _project_or_404(project_id: int, organization_id: Optional[str] = None) -> Project:
    org_id = _org_id(organization_id)
    project = Project.query.filter_by(id=project_id, organization_id=org_id).first()
    if not project:
        raise WorkStructureError("Project not found.")
    return project


def catalog_visible_filter(model, organization_id: str):
    return or_(model.organization_id.is_(None), model.organization_id == organization_id)


def list_work_types(*, organization_id: Optional[str] = None, include_inactive: bool = False):
    org_id = _org_id(organization_id)
    query = WorkType.query.filter(catalog_visible_filter(WorkType, org_id))
    if not include_inactive:
        query = query.filter_by(status=WORK_STATUS_ACTIVE)
    return query.order_by(WorkType.sort_order.asc(), WorkType.display_name.asc()).all()


def list_element_templates(
    *,
    work_type_id: Optional[int] = None,
    organization_id: Optional[str] = None,
    include_inactive: bool = False,
):
    org_id = _org_id(organization_id)
    query = WorkElementTemplate.query.filter(
        catalog_visible_filter(WorkElementTemplate, org_id)
    )
    if work_type_id is not None:
        query = query.filter_by(work_type_id=work_type_id)
    if not include_inactive:
        query = query.filter_by(status=WORK_STATUS_ACTIVE)
    return query.order_by(
        WorkElementTemplate.sort_order.asc(), WorkElementTemplate.display_name.asc()
    ).all()


def list_activity_templates(
    *,
    element_template_id: Optional[int] = None,
    organization_id: Optional[str] = None,
    include_inactive: bool = False,
):
    org_id = _org_id(organization_id)
    query = WorkActivityTemplate.query.filter(
        catalog_visible_filter(WorkActivityTemplate, org_id)
    )
    if element_template_id is not None:
        query = query.filter_by(work_element_template_id=element_template_id)
    if not include_inactive:
        query = query.filter_by(status=WORK_STATUS_ACTIVE)
    return query.order_by(
        WorkActivityTemplate.sort_order.asc(), WorkActivityTemplate.display_name.asc()
    ).all()


def _require_org_owned(row, label: str) -> None:
    if getattr(row, "organization_id", None) is None:
        raise WorkStructureError(f"CalibraytAI {label} cannot be changed by an organization.")


def create_org_work_type(
    *,
    display_name: str,
    code: Optional[str] = None,
    sort_order: int = 100,
    organization_id: Optional[str] = None,
) -> WorkType:
    org_id = _org_id(organization_id)
    name = (display_name or "").strip()
    if not name:
        raise WorkStructureError("Name is required.")
    type_code = _code(code or name)
    if not type_code:
        raise WorkStructureError("A short code is required.")
    existing = WorkType.query.filter_by(organization_id=org_id, code=type_code).first()
    if existing:
        raise WorkStructureError("That work type already exists for this organization.")
    row = WorkType(
        organization_id=org_id,
        code=type_code,
        display_name=name,
        status=WORK_STATUS_ACTIVE,
        sort_order=int(sort_order or 100),
    )
    db.session.add(row)
    db.session.commit()
    return row


def create_org_element_template(
    *,
    work_type_id: int,
    display_name: str,
    code: Optional[str] = None,
    sort_order: int = 100,
    organization_id: Optional[str] = None,
) -> WorkElementTemplate:
    org_id = _org_id(organization_id)
    work_type = WorkType.query.filter(
        WorkType.id == work_type_id,
        catalog_visible_filter(WorkType, org_id),
    ).first()
    if not work_type:
        raise WorkStructureError("Work type not found.")
    name = (display_name or "").strip()
    if not name:
        raise WorkStructureError("Name is required.")
    element_code = _code(code or name)
    if not element_code:
        raise WorkStructureError("A short code is required.")
    existing = WorkElementTemplate.query.filter_by(
        organization_id=org_id,
        work_type_id=work_type.id,
        code=element_code,
    ).first()
    if existing:
        raise WorkStructureError("That element already exists for this work type.")
    row = WorkElementTemplate(
        organization_id=org_id,
        work_type_id=work_type.id,
        code=element_code,
        display_name=name,
        status=WORK_STATUS_ACTIVE,
        sort_order=int(sort_order or 100),
    )
    db.session.add(row)
    db.session.commit()
    return row


def create_org_activity_template(
    *,
    element_template_id: int,
    display_name: str,
    code: Optional[str] = None,
    labour_task_id: Optional[int] = None,
    sort_order: int = 100,
    organization_id: Optional[str] = None,
) -> WorkActivityTemplate:
    org_id = _org_id(organization_id)
    element = WorkElementTemplate.query.filter(
        WorkElementTemplate.id == element_template_id,
        catalog_visible_filter(WorkElementTemplate, org_id),
    ).first()
    if not element:
        raise WorkStructureError("Element not found.")
    name = (display_name or "").strip()
    if not name:
        raise WorkStructureError("Name is required.")
    activity_code = _code(code or name)
    if not activity_code:
        raise WorkStructureError("A short code is required.")
    task = None
    if labour_task_id:
        task = LabourTask.query.filter_by(id=labour_task_id, organization_id=org_id).first()
        if not task:
            raise WorkStructureError("Labour rate item not found.")
    existing = WorkActivityTemplate.query.filter_by(
        organization_id=org_id,
        work_element_template_id=element.id,
        code=activity_code,
    ).first()
    if existing:
        raise WorkStructureError("That activity already exists for this element.")
    row = WorkActivityTemplate(
        organization_id=org_id,
        work_element_template_id=element.id,
        labour_task_id=task.id if task else None,
        code=activity_code,
        display_name=name,
        status=WORK_STATUS_ACTIVE,
        sort_order=int(sort_order or 100),
    )
    db.session.add(row)
    db.session.commit()
    return row


def deactivate_catalog_row(row, *, organization_id: Optional[str] = None) -> None:
    org_id = _org_id(organization_id)
    _require_org_owned(row, "catalog item")
    if row.organization_id != org_id:
        raise WorkStructureError("Catalog item not found.")
    row.status = WORK_STATUS_INACTIVE
    db.session.commit()


def list_project_work_elements(project_id: int, *, organization_id: Optional[str] = None):
    org_id = _org_id(organization_id)
    return (
        ProjectWorkElement.query.filter_by(project_id=project_id, organization_id=org_id)
        .order_by(ProjectWorkElement.sort_order.asc(), ProjectWorkElement.id.asc())
        .all()
    )


def get_project_seed(project_id: int, *, organization_id: Optional[str] = None):
    org_id = _org_id(organization_id)
    return ProjectWorkStructureSeed.query.filter_by(
        project_id=project_id, organization_id=org_id
    ).first()


def eligible_seed_versions(project: Project, *, organization_id: Optional[str] = None):
    org_id = _org_id(organization_id)
    versions = []
    for estimate in project.estimates:
        version = estimate.current_version
        if version is None:
            continue
        if version.estimate.project.organization_id != org_id:
            continue
        if not _version_is_seed_eligible(version):
            continue
        snapshots = EstimateLabourSnapshot.query.filter_by(
            estimate_version_id=version.id, organization_id=org_id
        ).count()
        if snapshots < 1:
            continue
        versions.append(version)
    return versions


def _version_is_seed_eligible(version: EstimateVersion) -> bool:
    if version.status not in SEED_ELIGIBLE_VERSION_STATUSES:
        return False
    return bool(version.is_locked)


def seed_project_work_structure(
    *,
    project_id: int,
    estimate_version_id: int,
    seeded_by: Optional[str] = None,
    organization_id: Optional[str] = None,
) -> ProjectWorkStructureSeed:
    org_id = _org_id(organization_id)
    project = _project_or_404(project_id, org_id)
    if get_project_seed(project.id, organization_id=org_id):
        raise WorkStructureError("This project's work plan is already built.")

    version = EstimateVersion.query.get(estimate_version_id)
    if not version or version.estimate.project_id != project.id:
        raise WorkStructureError("That estimate cannot be used for this project.")
    if version.estimate.project.organization_id != org_id:
        raise WorkStructureError("That estimate cannot be used for this project.")
    if not _version_is_seed_eligible(version):
        raise WorkStructureError(
            "Build project work from a locked issued or accepted estimate that has labour hours."
        )

    snapshots = (
        EstimateLabourSnapshot.query.filter_by(
            estimate_version_id=version.id, organization_id=org_id
        )
        .order_by(EstimateLabourSnapshot.id.asc())
        .all()
    )
    if not snapshots:
        raise WorkStructureError(
            "This estimate has no labour hours to build a work plan from."
        )

    grouped: dict[str, list[EstimateLabourSnapshot]] = defaultdict(list)
    for snapshot in snapshots:
        task = snapshot.labour_task
        label = (task.category or task.trade or "General").strip() or "General"
        grouped[label].append(snapshot)

    for element_order, (label, rows) in enumerate(grouped.items(), start=1):
        hours = sum((row.calculated_man_hours or Decimal("0")) for row in rows)
        element = ProjectWorkElement(
            organization_id=org_id,
            project_id=project.id,
            display_name=label,
            status=WORK_STATUS_ACTIVE,
            sort_order=element_order * 10,
            source_kind=SOURCE_ESTIMATE_SEED,
            estimated_hours=hours,
            scope_origin=SCOPE_ORIGINAL,
        )
        db.session.add(element)
        db.session.flush()
        for activity_order, snapshot in enumerate(rows, start=1):
            task = snapshot.labour_task
            db.session.add(
                ProjectWorkActivity(
                    organization_id=org_id,
                    project_work_element_id=element.id,
                    display_name=task.canonical_name,
                    status=WORK_STATUS_ACTIVE,
                    sort_order=activity_order * 10,
                    source_kind=SOURCE_ESTIMATE_SEED,
                    labour_task_id=task.id,
                    source_estimate_version_id=version.id,
                    source_estimate_labour_snapshot_id=snapshot.id,
                    estimated_hours=snapshot.calculated_man_hours,
                    quantity=snapshot.quantity,
                    unit=snapshot.unit,
                    production_rate=snapshot.resolved_production_rate,
                    scope_origin=SCOPE_ORIGINAL,
                )
            )

    seed = ProjectWorkStructureSeed(
        organization_id=org_id,
        project_id=project.id,
        estimate_version_id=version.id,
        seeded_by=(seeded_by or "").strip() or None,
        seeded_at=datetime.utcnow(),
    )
    db.session.add(seed)
    db.session.commit()
    return seed


def add_project_element(
    *,
    project_id: int,
    display_name: str,
    organization_id: Optional[str] = None,
) -> ProjectWorkElement:
    org_id = _org_id(organization_id)
    project = _project_or_404(project_id, org_id)
    name = (display_name or "").strip()
    if not name:
        raise WorkStructureError("Name is required.")
    max_order = (
        db.session.query(db.func.max(ProjectWorkElement.sort_order))
        .filter_by(project_id=project.id, organization_id=org_id)
        .scalar()
        or 0
    )
    row = ProjectWorkElement(
        organization_id=org_id,
        project_id=project.id,
        display_name=name,
        status=WORK_STATUS_ACTIVE,
        sort_order=int(max_order) + 10,
        source_kind=SOURCE_PROJECT,
        scope_origin=SCOPE_EXTRA_WORK,
    )
    db.session.add(row)
    db.session.commit()
    return row


def add_project_activity(
    *,
    project_work_element_id: int,
    display_name: str,
    labour_task_id: Optional[int] = None,
    organization_id: Optional[str] = None,
) -> ProjectWorkActivity:
    org_id = _org_id(organization_id)
    element = ProjectWorkElement.query.filter_by(
        id=project_work_element_id, organization_id=org_id
    ).first()
    if not element:
        raise WorkStructureError("Work item not found.")
    name = (display_name or "").strip()
    if not name:
        raise WorkStructureError("Name is required.")
    task = None
    if labour_task_id:
        task = LabourTask.query.filter_by(id=labour_task_id, organization_id=org_id).first()
        if not task:
            raise WorkStructureError("Labour rate item not found.")
    max_order = (
        db.session.query(db.func.max(ProjectWorkActivity.sort_order))
        .filter_by(project_work_element_id=element.id, organization_id=org_id)
        .scalar()
        or 0
    )
    row = ProjectWorkActivity(
        organization_id=org_id,
        project_work_element_id=element.id,
        display_name=name,
        status=WORK_STATUS_ACTIVE,
        sort_order=int(max_order) + 10,
        source_kind=SOURCE_PROJECT,
        labour_task_id=task.id if task else None,
        scope_origin=SCOPE_EXTRA_WORK,
    )
    db.session.add(row)
    db.session.commit()
    return row


def rename_project_work_row(row, display_name: str, *, organization_id: Optional[str] = None):
    org_id = _org_id(organization_id)
    if row.organization_id != org_id:
        raise WorkStructureError("Work item not found.")
    name = (display_name or "").strip()
    if not name:
        raise WorkStructureError("Name is required.")
    row.display_name = name
    db.session.commit()
    return row


def set_project_work_sort_order(row, sort_order: int, *, organization_id: Optional[str] = None):
    org_id = _org_id(organization_id)
    if row.organization_id != org_id:
        raise WorkStructureError("Work item not found.")
    row.sort_order = int(sort_order)
    db.session.commit()
    return row


def deactivate_project_work_row(row, *, organization_id: Optional[str] = None):
    org_id = _org_id(organization_id)
    if row.organization_id != org_id:
        raise WorkStructureError("Work item not found.")
    row.status = WORK_STATUS_INACTIVE
    db.session.commit()
    return row


def source_label(source_kind: str) -> str:
    return {
        SOURCE_BASELINE: "CalibraytAI",
        SOURCE_ORGANIZATION: "Organization",
        SOURCE_ESTIMATE_SEED: "From estimate",
        SOURCE_PROJECT: "This project",
    }.get(source_kind, source_kind)


def catalog_layer_label(row) -> str:
    if getattr(row, "organization_id", None) is None:
        return "CalibraytAI"
    return "This organization"


def ensure_baseline_work_catalog() -> WorkType:
    """Idempotent baseline for in-memory tests (migration seeds live DBs)."""
    existing = WorkType.query.filter_by(organization_id=None, code="GEN").first()
    if existing:
        return existing
    work_type = WorkType(
        organization_id=None,
        code="GEN",
        display_name="General construction",
        status=WORK_STATUS_ACTIVE,
        sort_order=10,
    )
    db.session.add(work_type)
    db.session.flush()
    for order, (code, name) in enumerate(
        (("SITE", "Site work"), ("FOUND", "Foundation"), ("STRUCT", "Structure")),
        start=1,
    ):
        element = WorkElementTemplate(
            organization_id=None,
            work_type_id=work_type.id,
            code=code,
            display_name=name,
            status=WORK_STATUS_ACTIVE,
            sort_order=order * 10,
        )
        db.session.add(element)
        db.session.flush()
        activities = {
            "SITE": (("CLEAR", "Clearing"),),
            "FOUND": (
                ("LAYOUT", "Layout"),
                ("EXCAV", "Excavation"),
                ("FORM", "Forms"),
                ("PLACE", "Placement"),
            ),
            "STRUCT": (("FRAME", "Framing"),),
        }
        for act_order, (act_code, act_name) in enumerate(activities[code], start=1):
            db.session.add(
                WorkActivityTemplate(
                    organization_id=None,
                    work_element_template_id=element.id,
                    code=act_code,
                    display_name=act_name,
                    status=WORK_STATUS_ACTIVE,
                    sort_order=act_order * 10,
                )
            )
    db.session.commit()
    return work_type
