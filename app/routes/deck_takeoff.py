"""Pool-deck material takeoff, supplier request, and supplier price return.

Brayman calculates. The supplier prices. CalibraytAI connects the two.
Nothing on these pages writes an estimate line.
"""

from __future__ import annotations

from datetime import datetime
from io import BytesIO

from flask import Blueprint, abort, flash, redirect, render_template, request, send_file, url_for

from app.models import Project
from app.models.canonical_material import CanonicalMaterial
from app.models.supplier_catalogue import ContractorSupplierAccount
from app.services.auth import form_actor
from app.services.brayman_supplier_estimate import render_supplier_response_request
from app.services.contractor_cost_approval import (
    ContractorCostApprovalError,
    record_contractor_cost_approval,
)
from app.services.deck_takeoff import storage
from app.services.deck_takeoff.intake import (
    FIELDS,
    READY_TO_RECORD,
    SupplierResponseError,
    answers_from_values,
    read_response_pdf,
    reconcile,
    record_ready_lines,
)
from app.services.deck_takeoff.product_facts import SCHEMA, ProductFactError, clean_product_facts
from app.services.deck_takeoff.project import project_takeoff
from app.services.deck_takeoff.supplier_request import build_request
from app.services.organizations import get_current_organization_id
from app.services.supplier_catalogue import resolve_effective_contractor_cost
from app.models.contractor_cost_approval import ContractorCostApproval

deck_takeoff_bp = Blueprint("deck_takeoff", __name__, url_prefix="/projects")

MAX_UPLOAD = 15 * 1024 * 1024


def _project(project_id: int):
    org_id = get_current_organization_id()
    project = Project.query.filter_by(id=project_id, organization_id=org_id).first_or_404()
    return project, org_id


def _accounts(org_id):
    return (
        ContractorSupplierAccount.query.filter_by(organization_id=org_id, status="ACTIVE")
        .order_by(ContractorSupplierAccount.id)
        .all()
    )


def _catalogue_codes():
    return frozenset(code for (code,) in CanonicalMaterial.query.with_entities(CanonicalMaterial.code).all())


@deck_takeoff_bp.route("/<int:project_id>/deck-takeoff")
def review(project_id):
    project, org_id = _project(project_id)
    state = project_takeoff(organization_id=org_id, project_id=project.id)
    return render_template(
        "projects/deck_takeoff.html",
        project=project,
        state=state,
        takeoff=state["takeoff"],
        schema=SCHEMA,
        facts=((state["product_facts_record"] or {}).get("facts") or {}),
        accounts=_accounts(org_id),
        requests=storage.list_requests(org_id, project.id),
        responses=storage.list_responses(org_id, project.id),
    )


@deck_takeoff_bp.route("/<int:project_id>/deck-takeoff/product-facts", methods=["POST"])
def save_facts(project_id):
    project, org_id = _project(project_id)
    raw = {}
    for category, fields in SCHEMA.items():
        for name in fields:
            value = request.form.get(f"{category}.{name}")
            if value is not None and value.strip():
                raw.setdefault(category, {})[name] = value
    try:
        facts = clean_product_facts(raw)
    except ProductFactError as exc:
        flash(str(exc), "error")
        return redirect(url_for("deck_takeoff.review", project_id=project.id))
    actor = form_actor("actor_display_name")
    if not actor:
        flash("The person entering the product facts is required.", "error")
        return redirect(url_for("deck_takeoff.review", project_id=project.id))
    stored = storage.save_product_facts(
        org_id,
        project.id,
        {
            "facts": facts,
            "entered_by": actor,
            "entered_at": datetime.utcnow().isoformat(timespec="seconds"),
            "source": (request.form.get("facts_source") or "").strip()[:200],
        },
    )
    flash(f"Product facts saved as version {stored['version']}. Earlier versions are kept.", "success")
    return redirect(url_for("deck_takeoff.review", project_id=project.id))


@deck_takeoff_bp.route("/<int:project_id>/deck-takeoff/request", methods=["POST"])
def issue_request(project_id):
    project, org_id = _project(project_id)
    state = project_takeoff(organization_id=org_id, project_id=project.id)
    if state["takeoff"] is None:
        flash("The takeoff cannot be calculated yet. See the missing project facts.", "error")
        return redirect(url_for("deck_takeoff.review", project_id=project.id))
    account_id = request.form.get("contractor_supplier_account_id", type=int)
    account = ContractorSupplierAccount.query.filter_by(id=account_id, organization_id=org_id, status="ACTIVE").first()
    if account is None:
        flash("Choose a supplier account before the supplier request.", "error")
        return redirect(url_for("deck_takeoff.review", project_id=project.id))
    actor = form_actor("actor_display_name")
    built = build_request(
        takeoff=state["takeoff"],
        project_id=project.id,
        organization_id=org_id,
        project_name=project.name,
        project_address=project.address or "",
        supplier_name=account.supplier.legal_name,
        contractor_supplier_account_id=account.id,
        supplier_id=account.supplier_id,
        supplier_location_id=account.supplier_location_id,
        issued_by=actor or "Office",
    )
    existing = storage.load_request(org_id, project.id, built["manifest"]["request_id"])
    if existing is None:
        pdf = render_supplier_response_request(**built["document"])
        storage.save_request(org_id, project.id, built["manifest"], pdf)
    else:
        pdf = storage.request_pdf(org_id, project.id, existing["request_id"])
    return send_file(
        BytesIO(pdf),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"supplier-request-{project.id}-{built['manifest']['request_id']}.pdf",
    )


@deck_takeoff_bp.route("/<int:project_id>/deck-takeoff/requests/<request_id>.pdf")
def download_request(project_id, request_id):
    project, org_id = _project(project_id)
    try:
        pdf = storage.request_pdf(org_id, project.id, request_id)
    except storage.TakeoffStorageError:
        abort(404)
    if pdf is None:
        abort(404)
    return send_file(BytesIO(pdf), mimetype="application/pdf", as_attachment=True, download_name=f"supplier-request-{project.id}-{request_id}.pdf")


@deck_takeoff_bp.route("/<int:project_id>/deck-takeoff/requests/<request_id>/enter")
def enter_response(project_id, request_id):
    project, org_id = _project(project_id)
    try:
        manifest = storage.load_request(org_id, project.id, request_id)
    except storage.TakeoffStorageError:
        abort(404)
    if manifest is None:
        abort(404)
    return render_template("projects/deck_takeoff_enter.html", project=project, manifest=manifest, fields=FIELDS)


@deck_takeoff_bp.route("/<int:project_id>/deck-takeoff/responses", methods=["POST"])
def import_response(project_id):
    project, org_id = _project(project_id)
    upload = request.files.get("response_pdf")
    pdf = None
    try:
        if upload is not None and upload.filename:
            pdf = upload.read(MAX_UPLOAD + 1)
            if len(pdf) > MAX_UPLOAD:
                raise SupplierResponseError("The returned PDF is too large.")
            values = read_response_pdf(pdf)
            source = "returned PDF"
        else:
            values = {key: value for key, value in request.form.items()}
            if not values.get("request_id"):
                raise SupplierResponseError("Choose the returned PDF, or enter the response by hand.")
            source = "entered by hand"
        answers = answers_from_values(values)
        manifest = storage.load_request(org_id, project.id, answers["request_id"])
        if manifest is None:
            raise SupplierResponseError("This response is not for a supplier request issued on this project.")
        reconciliation = reconcile(
            manifest,
            answers,
            project_id=project.id,
            organization_id=org_id,
            catalogue_codes=_catalogue_codes(),
        )
    except (SupplierResponseError, storage.TakeoffStorageError) as exc:
        flash(str(exc), "error")
        return redirect(url_for("deck_takeoff.review", project_id=project.id))
    actor = form_actor("actor_display_name") or "Office"
    record = {
        **reconciliation,
        "stage": "IMPORTED",
        "source": source,
        "imported_by": actor,
        "imported_at": datetime.utcnow().isoformat(timespec="seconds"),
    }
    stored = storage.save_response(org_id, project.id, record, pdf)
    flash("Supplier response imported. Nothing has been recorded yet.", "success")
    return redirect(url_for("deck_takeoff.view_response", project_id=project.id, response_id=stored["response_id"]))


@deck_takeoff_bp.route("/<int:project_id>/deck-takeoff/responses/<response_id>")
def view_response(project_id, response_id):
    project, org_id = _project(project_id)
    try:
        record = storage.load_response(org_id, project.id, response_id)
    except storage.TakeoffStorageError:
        abort(404)
    if record is None:
        abort(404)
    followups = [r for r in storage.list_responses(org_id, project.id) if r.get("records_response") == response_id]
    review = {}
    approvals = {}
    for follow in followups:
        for result in follow.get("results") or []:
            material_id = result.get("canonical_material_id")
            if not result.get("recorded") or material_id in review:
                continue
            # Contractor cost review: the cost the existing resolver would approve now.
            review[material_id] = resolve_effective_contractor_cost(
                canonical_material_id=material_id,
                contractor_supplier_account_id=record["contractor_supplier_account_id"],
                as_of=datetime.utcnow(),
            )
            latest = (
                ContractorCostApproval.query.filter_by(
                    organization_id=org_id,
                    canonical_material_id=material_id,
                    supplier_id=record["supplier_id"],
                )
                .order_by(ContractorCostApproval.id.desc())
                .first()
            )
            approvals[material_id] = latest
    return render_template(
        "projects/deck_takeoff_response.html",
        project=project,
        record=record,
        followups=followups,
        ready=READY_TO_RECORD,
        review=review,
        approvals=approvals,
    )


@deck_takeoff_bp.route("/<int:project_id>/deck-takeoff/responses/<response_id>/record", methods=["POST"])
def record_response(project_id, response_id):
    project, org_id = _project(project_id)
    record = storage.load_response(org_id, project.id, response_id)
    if record is None or record.get("stage") != "IMPORTED":
        abort(404)
    if any(r.get("records_response") == response_id and r.get("stage") == "RECORDED" for r in storage.list_responses(org_id, project.id)):
        flash("This response has already been recorded.", "error")
        return redirect(url_for("deck_takeoff.view_response", project_id=project.id, response_id=response_id))
    actor = form_actor("actor_display_name")
    try:
        results = record_ready_lines(record, actor_display_name=actor, demo_synthetic=bool(getattr(project, "demo_synthetic", False)))
    except SupplierResponseError as exc:
        flash(str(exc), "error")
        return redirect(url_for("deck_takeoff.view_response", project_id=project.id, response_id=response_id))
    storage.save_response(
        org_id,
        project.id,
        {
            "stage": "RECORDED",
            "records_response": response_id,
            "organization_id": org_id,
            "project_id": project.id,
            "request_id": record["request_id"],
            "recorded_by": actor,
            "recorded_at": datetime.utcnow().isoformat(timespec="seconds"),
            "results": results,
        },
        None,
    )
    done = sum(1 for r in results if r.get("recorded"))
    flash(f"{done} supplier prices recorded as evidence. No estimate line was created. Costs still need Brayman approval.", "success")
    return redirect(url_for("deck_takeoff.view_response", project_id=project.id, response_id=response_id))


@deck_takeoff_bp.route("/<int:project_id>/deck-takeoff/responses/<response_id>/approve", methods=["POST"])
def approve_cost(project_id, response_id):
    project, org_id = _project(project_id)
    record = storage.load_response(org_id, project.id, response_id)
    if record is None:
        abort(404)
    material_id = request.form.get("canonical_material_id", type=int)
    decision = (request.form.get("status") or "").strip().upper()
    try:
        approval = record_contractor_cost_approval(
            organization_id=org_id,
            canonical_material_id=material_id,
            contractor_supplier_account_id=record["contractor_supplier_account_id"],
            as_of=datetime.utcnow(),
            approved_by=form_actor("actor_display_name"),
            status=decision,
        )
    except ContractorCostApprovalError as exc:
        flash(str(exc), "error")
    else:
        flash(f"Contractor cost {approval.status.lower()} at {approval.resolved_amount} {approval.currency} per {approval.unit}. No estimate line was created.", "success")
    return redirect(url_for("deck_takeoff.view_response", project_id=project.id, response_id=response_id))
