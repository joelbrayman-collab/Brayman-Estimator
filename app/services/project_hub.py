"""Read-only Project Hub assembly (FG-011).

Projects owns this UX. The hub reads and links to records owned by other
modules. It does not write, recompute selling price, map take-off into
estimates, or invent lifecycle/health state.
"""

from __future__ import annotations

from sqlalchemy import func

from app import db
from app.models import Proposal
from app.models.labour_engine import EstimateLabourSnapshot
from app.plan_intelligence.models import (
    DrawingPackage,
    DrawingRevision,
    PlanMeasurement,
    PlanScaleCalibration,
    PlanSheet,
)
from app.plan_intelligence.services import list_plan_documents
from app.plan_intelligence.takeoff import list_packages_for_project, list_runs_for_project
from app.project_controls import repository as change_order_repo
from app.services.permit_foundation import assemble_permit_foundation_state


def assemble_project_hub(project, organization_id: str) -> dict:
    """Return stored facts and navigation context for `/projects/<id>`.

    Organization-scoped. Does not create drawing packages, revisions, snapshots,
    take-off records, or estimates. Does not commit.
    """
    estimates = sorted(project.estimates, key=lambda row: row.updated_at, reverse=True)
    estimate_ids = [row.id for row in estimates]
    proposals = []
    if estimate_ids:
        proposals = (
            Proposal.query.filter(Proposal.estimate_id.in_(estimate_ids))
            .order_by(Proposal.updated_at.desc())
            .all()
        )

    version_ids = [
        estimate.current_version_id
        for estimate in estimates
        if estimate.current_version_id
    ]
    labour_presence = _labour_snapshot_presence(organization_id, version_ids)

    estimate_rows = []
    for estimate in estimates:
        version = estimate.current_version
        snapshot = None
        if version is not None:
            snapshot = version.pricing_snapshot
            if snapshot is not None and snapshot.organization_id != organization_id:
                snapshot = None
        estimate_rows.append(
            {
                "estimate": estimate,
                "current_version": version,
                "pricing_snapshot_present": snapshot is not None,
                "pricing_method": snapshot.method if snapshot is not None else None,
                "labour_snapshot_present": bool(
                    version and labour_presence.get(version.id)
                ),
            }
        )

    plan_documents = list_plan_documents(project.id, include_archived=False)
    revision = _existing_active_revision(project)
    sheets = []
    if revision is not None:
        sheets = (
            PlanSheet.query.filter_by(drawing_revision_id=revision.id)
            .order_by(PlanSheet.number.asc().nullslast(), PlanSheet.id.asc())
            .all()
        )
    sheet_ids = [sheet.id for sheet in sheets]
    measure_sheet = next((sheet for sheet in sheets if not sheet.is_void), None)

    calibration_count = 0
    measurement_count = 0
    if sheet_ids:
        calibration_count = (
            PlanScaleCalibration.query.filter(
                PlanScaleCalibration.sheet_id.in_(sheet_ids),
                PlanScaleCalibration.calibration_status != "void",
            ).count()
        )
        measurement_count = (
            PlanMeasurement.query.filter(
                PlanMeasurement.sheet_id.in_(sheet_ids),
                PlanMeasurement.status != "void",
            ).count()
        )

    takeoff_runs = list_runs_for_project(organization_id, project.id)
    takeoff_packages = list_packages_for_project(organization_id, project.id)
    approved_packages = [
        package for package in takeoff_packages if package.status == "approved"
    ]

    return {
        "permit_foundation": assemble_permit_foundation_state(project),
        "estimates": estimates,
        "estimate_rows": estimate_rows,
        "proposals": proposals,
        "change_orders": change_order_repo.list_change_orders_for_project(project.id),
        "plan_documents": plan_documents,
        "active_revision": revision,
        "sheets": sheets,
        "sheet_count": len(sheets),
        "measure_sheet": measure_sheet,
        "calibration_count": calibration_count,
        "measurement_count": measurement_count,
        "takeoff_runs": takeoff_runs,
        "latest_takeoff_run": takeoff_runs[0] if takeoff_runs else None,
        "takeoff_packages": takeoff_packages,
        "approved_takeoff_packages": approved_packages,
    }


def _existing_active_revision(project):
    """Read an existing default active revision. Never create package/revision."""
    package = (
        DrawingPackage.query.filter_by(
            project_id=project.id,
            package_type="default",
        )
        .order_by(DrawingPackage.id.asc())
        .first()
    )
    if package is None:
        return None
    return (
        DrawingRevision.query.filter_by(package_id=package.id, is_active=True)
        .order_by(DrawingRevision.id.asc())
        .first()
    )


def _labour_snapshot_presence(organization_id, version_ids):
    if not version_ids:
        return {}
    rows = (
        db.session.query(
            EstimateLabourSnapshot.estimate_version_id,
            func.count(EstimateLabourSnapshot.id),
        )
        .filter(
            EstimateLabourSnapshot.organization_id == organization_id,
            EstimateLabourSnapshot.estimate_version_id.in_(version_ids),
        )
        .group_by(EstimateLabourSnapshot.estimate_version_id)
        .all()
    )
    return {version_id: count for version_id, count in rows if count}
