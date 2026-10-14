"""Construction drawings: generate from the construction model, preview,
download PDF and DXF, save to Project Plans, and attach to an estimate
version, a proposal or a BMR supplier request."""

from __future__ import annotations

import json
from io import BytesIO

from flask import Blueprint, abort, flash, redirect, render_template, request, send_file, url_for

from app.models import Project
from app.models.construction_drawing import (
    ATTACH_ESTIMATE_VERSION,
    ATTACH_PROPOSAL,
    ATTACH_SUPPLIER_REQUEST,
)
from app.models.estimate import Estimate, EstimateVersion
from app.models.proposal import Proposal
from app.services import construction_drawings as drawings
from app.services.auth import form_actor
from app.services.deck_takeoff import storage
from app.services.organizations import get_current_organization_id

construction_drawings_bp = Blueprint("construction_drawings", __name__, url_prefix="/projects")


def _project(project_id: int):
    org_id = get_current_organization_id()
    project = Project.query.filter_by(id=project_id, organization_id=org_id).first_or_404()
    return project, org_id


def _set_or_404(org_id, project_id, set_id):
    try:
        return drawings.get_drawing_set(org_id, project_id, set_id)
    except drawings.DrawingError:
        abort(404)


def _targets(org_id, project):
    estimates = Estimate.query.filter_by(project_id=project.id, organization_id=org_id).order_by(Estimate.id).all()
    versions = []
    for est in estimates:
        for v in EstimateVersion.query.filter_by(estimate_id=est.id).order_by(EstimateVersion.id).all():
            versions.append((est, v))
    est_ids = [e.id for e in estimates]
    proposals = Proposal.query.filter(Proposal.organization_id == org_id, Proposal.estimate_id.in_(est_ids)).order_by(Proposal.id).all() if est_ids else []
    return versions, proposals, storage.list_requests(org_id, project.id)


@construction_drawings_bp.route("/<int:project_id>/drawings")
def index(project_id):
    project, org_id = _project(project_id)
    sets = drawings.drawing_sets(org_id, project.id)
    rows = []
    for s in sets:
        rows.append({
            "set": s,
            "state": drawings.drawing_state(s),
            "attachments": drawings.attachments_for_set(s),
            "sheets": json.loads(s.sheet_index_json or "[]"),
        })
    versions, proposals, requests = _targets(org_id, project)
    return render_template(
        "projects/construction_drawings.html",
        project=project,
        rows=rows,
        revisions=drawings.model_revisions(org_id, project.id),
        facts=storage.current_product_facts(org_id, project.id),
        versions=versions,
        proposals=proposals,
        requests=requests,
        attachable_statuses=drawings.ATTACHABLE_PROPOSAL_STATUSES,
        engine_version=drawings.ENGINE_VERSION,
    )


@construction_drawings_bp.route("/<int:project_id>/drawings/generate", methods=["POST"])
def generate(project_id):
    project, org_id = _project(project_id)
    actor = form_actor("actor_display_name")
    try:
        record, created = drawings.generate_drawing_set(
            organization_id=org_id,
            project_id=project.id,
            actor=actor or "",
            revision_id=request.form.get("revision_id", type=int),
        )
    except drawings.DrawingError as exc:
        flash(str(exc), "error")
        return redirect(url_for("construction_drawings.index", project_id=project.id))
    if created:
        flash(f"Drawing revision {record.label} generated from model revision R{record.model_revision_number}.", "success")
    else:
        flash(f"These inputs already produced drawing revision {record.label}. Nothing was regenerated.", "success")
    return redirect(url_for("construction_drawings.preview", project_id=project.id, set_id=record.id))


@construction_drawings_bp.route("/<int:project_id>/drawings/<int:set_id>")
def preview(project_id, set_id):
    project, org_id = _project(project_id)
    record = _set_or_404(org_id, project.id, set_id)
    return render_template(
        "projects/construction_drawing_preview.html",
        project=project,
        record=record,
        state=drawings.drawing_state(record),
        sheets=json.loads(record.sheet_index_json or "[]"),
    )


@construction_drawings_bp.route("/<int:project_id>/drawings/<int:set_id>.pdf")
def pdf(project_id, set_id):
    project, org_id = _project(project_id)
    record = _set_or_404(org_id, project.id, set_id)
    inline = request.args.get("inline") == "1"
    return send_file(BytesIO(record.pdf_bytes), mimetype="application/pdf", as_attachment=not inline,
                     download_name=f"project-{project.id}-construction-drawings-{record.label}.pdf")


@construction_drawings_bp.route("/<int:project_id>/drawings/<int:set_id>.dxf")
def dxf(project_id, set_id):
    project, org_id = _project(project_id)
    record = _set_or_404(org_id, project.id, set_id)
    return send_file(BytesIO(record.dxf_bytes), mimetype="application/dxf", as_attachment=True,
                     download_name=f"project-{project.id}-construction-drawings-{record.label}.dxf")


@construction_drawings_bp.route("/<int:project_id>/drawings/<int:set_id>/save-to-plans", methods=["POST"])
def save_to_plans(project_id, set_id):
    project, org_id = _project(project_id)
    record = _set_or_404(org_id, project.id, set_id)
    try:
        plan_id, created = drawings.save_to_plans(record)
    except drawings.DrawingError as exc:
        flash(str(exc), "error")
        return redirect(url_for("construction_drawings.index", project_id=project.id))
    flash(f"Drawing revision {record.label} {'saved to' if created else 'is already in'} Project Plans (plan {plan_id}).", "success")
    return redirect(url_for("construction_drawings.index", project_id=project.id))


@construction_drawings_bp.route("/<int:project_id>/drawings/<int:set_id>/attach", methods=["POST"])
def attach(project_id, set_id):
    project, org_id = _project(project_id)
    record = _set_or_404(org_id, project.id, set_id)
    kind = request.form.get("target_kind", "")
    target = {
        ATTACH_ESTIMATE_VERSION: request.form.get("estimate_version_id"),
        ATTACH_PROPOSAL: request.form.get("proposal_id"),
        ATTACH_SUPPLIER_REQUEST: request.form.get("supplier_request_id"),
    }.get(kind)
    if not target:
        flash("Choose where to attach the drawings.", "error")
        return redirect(url_for("construction_drawings.index", project_id=project.id))
    actor = form_actor("actor_display_name")
    try:
        _row, created = drawings.attach(record, kind, target, actor or "")
    except (drawings.DrawingError, ValueError) as exc:
        flash(str(exc), "error")
        return redirect(url_for("construction_drawings.index", project_id=project.id))
    label = {ATTACH_ESTIMATE_VERSION: "the estimate version", ATTACH_PROPOSAL: "the proposal", ATTACH_SUPPLIER_REQUEST: "the supplier request"}[kind]
    flash(f"Drawing revision {record.label} {'attached to' if created else 'is already attached to'} {label}.", "success")
    return redirect(url_for("construction_drawings.index", project_id=project.id))


@construction_drawings_bp.route("/<int:project_id>/deck-takeoff/requests/<request_id>/package.pdf")
def supplier_package(project_id, request_id):
    """The issued supplier request (unchanged) followed by its attached drawing sheets."""
    project, org_id = _project(project_id)
    try:
        base = storage.request_pdf(org_id, project.id, request_id)
    except storage.TakeoffStorageError:
        abort(404)
    if base is None:
        abort(404)
    attachment = drawings.current_attachment(ATTACH_SUPPLIER_REQUEST, request_id)
    if attachment is None or attachment.project_id != project.id:
        abort(404)
    try:
        payload = drawings.append_drawings(base, attachment)
    except drawings.DrawingError:
        abort(409)
    return send_file(BytesIO(payload), mimetype="application/pdf", as_attachment=True,
                     download_name=f"supplier-request-{project.id}-{request_id}-with-drawings-{attachment.drawing_set.label}.pdf")
