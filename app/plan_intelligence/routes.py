"""Plan Intelligence routes — upload, indexing, search, archive, and Sheet Intelligence (M009)."""

from flask import (
    Blueprint,
    abort,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)

from app.models import Project
from app.plan_intelligence.models import (
    DrawingRevision,
    PlanAuditEvent,
    PlanDocument,
    PlanSheet,
    PlanSheetSuggestion,
    ProcessingAttempt,
)
from app.services.organizations import get_current_organization_id
from app.plan_intelligence.packages import ensure_default_revision
from app.plan_intelligence.services import (
    PlanIntelligenceServiceError,
    archive_plan_document,
    delete_plan_document,
    get_plan_document,
    list_plan_documents,
    open_plan_document_file,
    reprocess_plan_document,
    search_plan_documents,
    upload_plan_pdf,
)
from app.plan_intelligence.sheets import (
    DISCIPLINE_CODES,
    DRAWING_STATUSES,
    REVIEW_STATUSES,
    accept_suggestion,
    create_sheet,
    edit_sheet,
    finalize_revision_sheet_index,
    generate_default_sheets_for_revision,
    generate_suggestions_for_sheet,
    get_sheet_or_404,
    list_sheets_for_revision,
    map_page_to_sheet,
    reject_suggestion,
    unmap_page_from_sheet,
    validate_revision_sheet_index,
    void_sheet,
)
from app.plan_intelligence.takeoff import (
    approve_package,
    create_draft_package,
    get_package_or_404,
    get_run_or_404,
    list_packages_for_project,
    list_runs_for_project,
    review_candidate,
    start_extraction_run,
)
from app.plan_intelligence.scale_measurement import (
    CALIBRATION_STATUSES,
    CALIBRATION_TYPES,
    LINEAR_UNITS,
    MEASUREMENT_TYPES,
    PRESET_SCALES,
    confirm_calibration,
    create_measurement,
    create_preset_calibration,
    create_two_point_calibration,
    list_calibrations_for_sheet,
    list_measurements_for_sheet,
    mark_sheet_nts,
    void_calibration,
    void_measurement,
)

plan_intelligence_bp = Blueprint(
    "plan_intelligence",
    __name__,
    url_prefix="",
)


def _get_project_or_404(project_id):
    org_id = get_current_organization_id()
    return Project.query.filter_by(id=project_id, organization_id=org_id).first_or_404()


@plan_intelligence_bp.route("/projects/<int:project_id>/plans")
def list_plans(project_id):
    project = _get_project_or_404(project_id)
    include_archived = request.args.get("show_archived") == "1"
    q = request.args.get("q", "").strip()
    processing_status = request.args.get("processing_status", "").strip() or None
    has_text_raw = request.args.get("has_text", "").strip()
    has_text = None
    if has_text_raw == "1":
        has_text = True
    elif has_text_raw == "0":
        has_text = False

    if q or processing_status or has_text is not None:
        documents = search_plan_documents(
            project.id,
            q=q or None,
            processing_status=processing_status,
            has_text=has_text,
            include_archived=include_archived,
        )
    else:
        documents = list_plan_documents(
            project.id, include_archived=include_archived
        )

    revision = ensure_default_revision(project)

    return render_template(
        "plan_intelligence/list.html",
        project=project,
        documents=documents,
        revision=revision,
        q=q,
        processing_status=processing_status or "",
        has_text=has_text_raw,
        show_archived=include_archived,
    )


@plan_intelligence_bp.route(
    "/projects/<int:project_id>/plans/upload",
    methods=["GET", "POST"],
)
def upload_plan(project_id):
    project = _get_project_or_404(project_id)
    if request.method == "POST":
        notes = request.form.get("notes", "")
        file_storage = request.files.get("plan_file")
        try:
            document = upload_plan_pdf(project, file_storage, notes=notes)
        except PlanIntelligenceServiceError as exc:
            flash(str(exc), "error")
            return render_template(
                "plan_intelligence/upload.html",
                project=project,
                notes=notes,
            )

        if document.processing_status == "failed":
            flash(
                "PDF uploaded, but deterministic indexing failed. "
                "You can retry processing from the document page.",
                "error",
            )
        elif not document.has_text_layer:
            flash(
                "PDF indexed, but no embedded text was detected. "
                "Searchable PDFs are preferred for future take-off.",
                "error",
            )
        else:
            flash("Plan PDF uploaded and indexed.", "success")
        return redirect(
            url_for(
                "plan_intelligence.view_plan",
                project_id=project.id,
                document_id=document.id,
            )
        )

    return render_template(
        "plan_intelligence/upload.html",
        project=project,
        notes="",
    )


@plan_intelligence_bp.route(
    "/projects/<int:project_id>/plans/<int:document_id>"
)
def view_plan(project_id, document_id):
    project = _get_project_or_404(project_id)
    document = get_plan_document(project.id, document_id)
    if document is None:
        abort(404)
    attempts = (
        ProcessingAttempt.query.filter_by(plan_document_id=document.id)
        .order_by(ProcessingAttempt.created_at.desc())
        .limit(10)
        .all()
    )
    audit_events = (
        PlanAuditEvent.query.filter_by(plan_document_id=document.id)
        .order_by(PlanAuditEvent.created_at.desc())
        .limit(20)
        .all()
    )
    revision = ensure_default_revision(project)
    return render_template(
        "plan_intelligence/detail.html",
        project=project,
        document=document,
        pages=document.pages,
        attempts=attempts,
        audit_events=audit_events,
        revision=revision,
    )


@plan_intelligence_bp.route(
    "/projects/<int:project_id>/plans/<int:document_id>/download"
)
def download_plan(project_id, document_id):
    project = _get_project_or_404(project_id)
    document = get_plan_document(project.id, document_id)
    if document is None:
        abort(404)
    try:
        path = open_plan_document_file(document)
    except PlanIntelligenceServiceError as exc:
        flash(str(exc), "error")
        return redirect(
            url_for("plan_intelligence.list_plans", project_id=project.id)
        )
    return send_file(
        path,
        mimetype=document.content_type or "application/pdf",
        as_attachment=True,
        download_name=document.original_filename,
    )


@plan_intelligence_bp.route(
    "/projects/<int:project_id>/plans/<int:document_id>/reprocess",
    methods=["POST"],
)
def reprocess_plan(project_id, document_id):
    project = _get_project_or_404(project_id)
    document = get_plan_document(project.id, document_id)
    if document is None:
        abort(404)
    force = request.form.get("force") == "1"
    try:
        attempt, skipped = reprocess_plan_document(document, force=force)
    except PlanIntelligenceServiceError as exc:
        flash(str(exc), "error")
        return redirect(
            url_for(
                "plan_intelligence.view_plan",
                project_id=project.id,
                document_id=document.id,
            )
        )
    if skipped:
        flash("Indexing skipped (idempotent — identical content already processed).", "success")
    else:
        flash(f"Indexing completed (attempt #{attempt.id}).", "success")
    return redirect(
        url_for(
            "plan_intelligence.view_plan",
            project_id=project.id,
            document_id=document.id,
        )
    )


@plan_intelligence_bp.route(
    "/projects/<int:project_id>/plans/<int:document_id>/delete",
    methods=["POST"],
)
def delete_plan(project_id, document_id):
    """Archive the document (hard delete blocked when indexing data exists)."""
    project = _get_project_or_404(project_id)
    document = get_plan_document(project.id, document_id)
    if document is None:
        abort(404)
    try:
        archive_plan_document(document)
    except PlanIntelligenceServiceError as exc:
        flash(str(exc), "error")
        return redirect(
            url_for(
                "plan_intelligence.view_plan",
                project_id=project.id,
                document_id=document_id,
            )
        )
    flash("Plan document archived.", "success")
    return redirect(url_for("plan_intelligence.list_plans", project_id=project.id))


# =========================================================================
# Sheet Intelligence routes (Milestone 009)
# =========================================================================

@plan_intelligence_bp.route("/projects/<int:project_id>/plans/sheets")
def project_sheets(project_id):
    """Shortcut redirect to default revision sheets."""
    project = _get_project_or_404(project_id)
    revision = ensure_default_revision(project)
    return redirect(
        url_for(
            "plan_intelligence.revision_sheets",
            project_id=project.id,
            revision_id=revision.id,
        )
    )


@plan_intelligence_bp.route(
    "/projects/<int:project_id>/plans/revisions/<int:revision_id>/sheets"
)
def revision_sheets(project_id, revision_id):
    """Sheet index and validation overview for a specific DrawingRevision."""
    project = _get_project_or_404(project_id)
    revision = DrawingRevision.query.filter_by(id=revision_id).first_or_404()
    if revision.package.project_id != project.id:
        abort(404)

    sheets = list_sheets_for_revision(revision.id, include_void=True)
    validation = validate_revision_sheet_index(revision)

    return render_template(
        "plan_intelligence/sheets_index.html",
        project=project,
        revision=revision,
        sheets=sheets,
        validation=validation,
    )


@plan_intelligence_bp.route(
    "/projects/<int:project_id>/plans/revisions/<int:revision_id>/sheets/new",
    methods=["GET", "POST"],
)
def new_sheet(project_id, revision_id):
    """Manual Sheet creation."""
    project = _get_project_or_404(project_id)
    revision = DrawingRevision.query.filter_by(id=revision_id).first_or_404()
    if revision.package.project_id != project.id:
        abort(404)

    plan_document_id = request.args.get("document_id", type=int)
    page_index = request.args.get("page_index", type=int)

    if request.method == "POST":
        number = request.form.get("number", "").strip()
        title = request.form.get("title", "").strip()
        discipline_code = request.form.get("discipline_code", "OTHER").strip()
        doc_id_form = request.form.get("plan_document_id", type=int)
        page_idx_form = request.form.get("page_index", type=int)

        try:
            sheet = create_sheet(
                revision=revision,
                number=number or None,
                title=title or None,
                discipline_code=discipline_code,
                drawing_status="unreviewed",
                review_status="draft",
                plan_document_id=doc_id_form,
                page_index=page_idx_form,
            )
            flash(f"Sheet created (ID {sheet.id}).", "success")
            return redirect(
                url_for(
                    "plan_intelligence.review_sheet",
                    project_id=project.id,
                    sheet_id=sheet.id,
                )
            )
        except PlanIntelligenceServiceError as exc:
            flash(str(exc), "error")

    documents = list_plan_documents(project.id, include_archived=False)
    return render_template(
        "plan_intelligence/sheet_create.html",
        project=project,
        revision=revision,
        documents=documents,
        discipline_codes=DISCIPLINE_CODES,
        pre_document_id=plan_document_id,
        pre_page_index=page_index,
    )


@plan_intelligence_bp.route(
    "/projects/<int:project_id>/plans/sheets/<int:sheet_id>"
)
def review_sheet(project_id, sheet_id):
    """Review screen for an individual Sheet (Accept/Edit/Reject suggestions, page maps)."""
    project = _get_project_or_404(project_id)
    sheet = get_sheet_or_404(project.id, sheet_id)
    revision = sheet.revision
    documents = list_plan_documents(project.id, include_archived=False)

    open_suggestions = [s for s in sheet.suggestions if s.is_open]
    past_suggestions = [s for s in sheet.suggestions if not s.is_open]

    audit_events = (
        PlanAuditEvent.query.filter_by(sheet_id=sheet.id)
        .order_by(PlanAuditEvent.created_at.desc())
        .limit(20)
        .all()
    )

    return render_template(
        "plan_intelligence/sheet_review.html",
        project=project,
        revision=revision,
        sheet=sheet,
        documents=documents,
        discipline_codes=DISCIPLINE_CODES,
        review_statuses=REVIEW_STATUSES,
        drawing_statuses=DRAWING_STATUSES,
        open_suggestions=open_suggestions,
        past_suggestions=past_suggestions,
        audit_events=audit_events,
    )


@plan_intelligence_bp.route(
    "/projects/<int:project_id>/plans/sheets/<int:sheet_id>/edit",
    methods=["POST"],
)
def edit_sheet_action(project_id, sheet_id):
    """Human Edit+Save action (ADR-017)."""
    project = _get_project_or_404(project_id)
    sheet = get_sheet_or_404(project.id, sheet_id)

    number = request.form.get("number", "").strip()
    title = request.form.get("title", "").strip()
    discipline_code = request.form.get("discipline_code", "OTHER").strip()
    review_status = request.form.get("review_status", "reviewed").strip()
    drawing_status = request.form.get("drawing_status", "reviewed").strip()

    try:
        edit_sheet(
            sheet=sheet,
            number=number or None,
            title=title or None,
            discipline_code=discipline_code,
            drawing_status=drawing_status,
            review_status=review_status,
        )
        flash("Sheet metadata saved.", "success")
    except PlanIntelligenceServiceError as exc:
        flash(str(exc), "error")

    return redirect(
        url_for(
            "plan_intelligence.review_sheet",
            project_id=project.id,
            sheet_id=sheet.id,
        )
    )


@plan_intelligence_bp.route(
    "/projects/<int:project_id>/plans/sheets/<int:sheet_id>/void",
    methods=["POST"],
)
def void_sheet_action(project_id, sheet_id):
    """Void a sheet."""
    project = _get_project_or_404(project_id)
    sheet = get_sheet_or_404(project.id, sheet_id)

    void_sheet(sheet)
    flash(f"Sheet {sheet.number or sheet.id} marked as void.", "success")
    return redirect(
        url_for(
            "plan_intelligence.revision_sheets",
            project_id=project.id,
            revision_id=sheet.drawing_revision_id,
        )
    )


@plan_intelligence_bp.route(
    "/projects/<int:project_id>/plans/sheets/<int:sheet_id>/suggestions/<int:suggestion_id>/accept",
    methods=["POST"],
)
def accept_suggestion_action(project_id, sheet_id, suggestion_id):
    """Human Accept suggestion action (ADR-017)."""
    project = _get_project_or_404(project_id)
    sheet = get_sheet_or_404(project.id, sheet_id)
    suggestion = PlanSheetSuggestion.query.filter_by(
        id=suggestion_id, sheet_id=sheet.id
    ).first_or_404()

    override_number = request.form.get("override_number", "").strip() or None
    override_title = request.form.get("override_title", "").strip() or None
    override_disc = request.form.get("override_discipline_code", "").strip() or None

    try:
        accept_suggestion(
            suggestion,
            number=override_number,
            title=override_title,
            discipline_code=override_disc,
        )
        flash("Suggestion accepted as authoritative Sheet metadata.", "success")
    except PlanIntelligenceServiceError as exc:
        flash(str(exc), "error")

    return redirect(
        url_for(
            "plan_intelligence.review_sheet",
            project_id=project.id,
            sheet_id=sheet.id,
        )
    )


@plan_intelligence_bp.route(
    "/projects/<int:project_id>/plans/sheets/<int:sheet_id>/suggestions/<int:suggestion_id>/reject",
    methods=["POST"],
)
def reject_suggestion_action(project_id, sheet_id, suggestion_id):
    """Human Reject suggestion action (ADR-017)."""
    project = _get_project_or_404(project_id)
    sheet = get_sheet_or_404(project.id, sheet_id)
    suggestion = PlanSheetSuggestion.query.filter_by(
        id=suggestion_id, sheet_id=sheet.id
    ).first_or_404()

    try:
        reject_suggestion(suggestion)
        flash("Suggestion rejected.", "success")
    except PlanIntelligenceServiceError as exc:
        flash(str(exc), "error")

    return redirect(
        url_for(
            "plan_intelligence.review_sheet",
            project_id=project.id,
            sheet_id=sheet.id,
        )
    )


@plan_intelligence_bp.route(
    "/projects/<int:project_id>/plans/sheets/<int:sheet_id>/suggestions/generate",
    methods=["POST"],
)
def generate_sheet_suggestions_action(project_id, sheet_id):
    """Generate or re-run suggestion extraction for a sheet."""
    project = _get_project_or_404(project_id)
    sheet = get_sheet_or_404(project.id, sheet_id)

    suggestion = generate_suggestions_for_sheet(sheet, force=True)
    if suggestion:
        flash(
            f"Suggestion generated: {suggestion.suggested_number or '—'} ({suggestion.suggested_discipline_code})",
            "success",
        )
    else:
        flash("No metadata suggestion could be extracted from mapped pages.", "info")

    return redirect(
        url_for(
            "plan_intelligence.review_sheet",
            project_id=project.id,
            sheet_id=sheet.id,
        )
    )


@plan_intelligence_bp.route(
    "/projects/<int:project_id>/plans/revisions/<int:revision_id>/sheets/generate-all",
    methods=["POST"],
)
def generate_all_sheets_action(project_id, revision_id):
    """Ensure all pages have a draft/suggested sheet in this revision."""
    project = _get_project_or_404(project_id)
    revision = DrawingRevision.query.filter_by(id=revision_id).first_or_404()
    if revision.package.project_id != project.id:
        abort(404)

    created = generate_default_sheets_for_revision(revision)
    if created:
        flash(f"Created {len(created)} draft/suggested sheet(s) for unmapped pages.", "success")
    else:
        flash("All pages already have sheets mapped in this revision.", "info")

    return redirect(
        url_for(
            "plan_intelligence.revision_sheets",
            project_id=project.id,
            revision_id=revision.id,
        )
    )


@plan_intelligence_bp.route(
    "/projects/<int:project_id>/plans/revisions/<int:revision_id>/sheets/finalize",
    methods=["POST"],
)
def finalize_sheet_index_action(project_id, revision_id):
    """Finalize/mark sheet index complete (ADR-018). Fails closed on errors."""
    project = _get_project_or_404(project_id)
    revision = DrawingRevision.query.filter_by(id=revision_id).first_or_404()
    if revision.package.project_id != project.id:
        abort(404)

    try:
        validation = finalize_revision_sheet_index(revision)
        flash(
            f"Sheet index finalized successfully ({validation['total_sheets']} sheets).",
            "success",
        )
    except PlanIntelligenceServiceError as exc:
        flash(str(exc), "error")

    return redirect(
        url_for(
            "plan_intelligence.revision_sheets",
            project_id=project.id,
            revision_id=revision.id,
        )
    )


@plan_intelligence_bp.route(
    "/projects/<int:project_id>/plans/sheets/<int:sheet_id>/map-page",
    methods=["POST"],
)
def map_page_action(project_id, sheet_id):
    """Add a page mapping to a sheet."""
    project = _get_project_or_404(project_id)
    sheet = get_sheet_or_404(project.id, sheet_id)

    doc_id = request.form.get("plan_document_id", type=int)
    page_idx = request.form.get("page_index", type=int)

    if doc_id is None or page_idx is None:
        flash("Document and page index are required.", "error")
    else:
        try:
            map_page_to_sheet(sheet, plan_document_id=doc_id, page_index=page_idx)
            flash(f"Page {page_idx + 1} mapped to sheet.", "success")
        except PlanIntelligenceServiceError as exc:
            flash(str(exc), "error")

    return redirect(
        url_for(
            "plan_intelligence.review_sheet",
            project_id=project.id,
            sheet_id=sheet.id,
        )
    )


@plan_intelligence_bp.route(
    "/projects/<int:project_id>/plans/sheets/<int:sheet_id>/unmap-page",
    methods=["POST"],
)
def unmap_page_action(project_id, sheet_id):
    """Remove a page mapping from a sheet."""
    project = _get_project_or_404(project_id)
    sheet = get_sheet_or_404(project.id, sheet_id)

    doc_id = request.form.get("plan_document_id", type=int)
    page_idx = request.form.get("page_index", type=int)

    if doc_id is None or page_idx is None:
        flash("Document and page index are required.", "error")
    else:
        unmap_page_from_sheet(sheet, plan_document_id=doc_id, page_index=page_idx)
        flash(f"Page mapping removed.", "success")

    return redirect(
        url_for(
            "plan_intelligence.review_sheet",
            project_id=project.id,
            sheet_id=sheet.id,
        )
    )


# =========================================================================
# Milestone 010 — Scale Calibration & Measurement Routes
# =========================================================================


@plan_intelligence_bp.route(
    "/projects/<int:project_id>/plans/sheets/<int:sheet_id>/measure"
)
def measure_sheet(project_id, sheet_id):
    """Interactive measurement and scale calibration workspace for a Sheet (M010)."""
    project = _get_project_or_404(project_id)
    sheet = get_sheet_or_404(project.id, sheet_id)
    revision = sheet.revision

    calibrations = list_calibrations_for_sheet(project.id, sheet.id)
    measurements = list_measurements_for_sheet(project.id, sheet.id)

    # First mapped document/page for viewing
    first_map = sheet.page_mappings[0] if sheet.page_mappings else None

    # Determine active confirmed calibration
    active_cal = None
    for c in calibrations:
        if c.is_confirmed and c.calibration_type != "viewport_region":
            active_cal = c
            break

    return render_template(
        "plan_intelligence/sheet_measure.html",
        project=project,
        revision=revision,
        sheet=sheet,
        first_map=first_map,
        calibrations=calibrations,
        active_cal=active_cal,
        measurements=measurements,
        preset_scales=PRESET_SCALES,
        linear_units=LINEAR_UNITS,
        measurement_types=MEASUREMENT_TYPES,
    )


@plan_intelligence_bp.route(
    "/projects/<int:project_id>/plans/sheets/<int:sheet_id>/measurements/data"
)
def sheet_measurement_data(project_id, sheet_id):
    """JSON API returning current calibrations and measurements for client rendering."""
    project = _get_project_or_404(project_id)
    sheet = get_sheet_or_404(project.id, sheet_id)

    calibrations = list_calibrations_for_sheet(project.id, sheet.id)
    measurements = list_measurements_for_sheet(project.id, sheet.id)

    cal_data = [
        {
            "id": c.id,
            "calibration_type": c.calibration_type,
            "status": c.calibration_status,
            "source_type": c.source_type,
            "label": c.label,
            "region_box": c.region_box,
            "point_a": {"x": c.point_a_x, "y": c.point_a_y} if c.point_a_x is not None else None,
            "point_b": {"x": c.point_b_x, "y": c.point_b_y} if c.point_b_x is not None else None,
            "known_distance": c.known_distance_value,
            "known_unit": c.known_distance_unit,
            "scale_ratio": c.scale_ratio,
            "page_index": c.page_index,
            "is_confirmed": c.is_confirmed,
            "is_nts": c.is_nts,
        }
        for c in calibrations
    ]

    meas_data = [
        {
            "id": m.id,
            "measurement_type": m.measurement_type,
            "label": m.label,
            "geometry_data": m.geometry_data,
            "computed_value": m.computed_value,
            "display_unit": m.display_unit,
            "perimeter_value": m.perimeter_value,
            "calibration_id": m.scale_calibration_id,
            "page_index": m.page_index,
            "status": m.status,
            "created_at": m.created_at.strftime("%Y-%m-%d %H:%M") if m.created_at else "",
        }
        for m in measurements
    ]

    return jsonify(
        {
            "sheet_id": sheet.id,
            "sheet_number": sheet.number,
            "calibrations": cal_data,
            "measurements": meas_data,
        }
    )


@plan_intelligence_bp.route(
    "/projects/<int:project_id>/plans/sheets/<int:sheet_id>/calibrations/two-point",
    methods=["POST"],
)
def create_two_point_calibration_action(project_id, sheet_id):
    """Create a 2-point scale calibration."""
    project = _get_project_or_404(project_id)
    sheet = get_sheet_or_404(project.id, sheet_id)

    is_json = request.is_json
    data = request.get_json() if is_json else request.form

    doc_id = int(data.get("plan_document_id", sheet.page_mappings[0].plan_document_id if sheet.page_mappings else 0))
    page_idx = int(data.get("page_index", sheet.page_mappings[0].page_index if sheet.page_mappings else 0))
    known_dist = str(data.get("known_distance", "")).strip()
    label = data.get("label", "").strip() or None
    is_viewport = bool(data.get("is_viewport", False))
    auto_confirm = bool(data.get("auto_confirm", False) or request.form.get("auto_confirm"))

    if is_json:
        p1 = data.get("point_a", {})
        p2 = data.get("point_b", {})
        region_box = data.get("region_box")
    else:
        p1 = {"x": float(data.get("point_a_x", 0)), "y": float(data.get("point_a_y", 0))}
        p2 = {"x": float(data.get("point_b_x", 0)), "y": float(data.get("point_b_y", 0))}
        r_x1 = data.get("region_x1")
        if r_x1 is not None and str(r_x1).strip():
            region_box = {
                "x1": float(data.get("region_x1")),
                "y1": float(data.get("region_y1")),
                "x2": float(data.get("region_x2")),
                "y2": float(data.get("region_y2")),
            }
        else:
            region_box = None

    cal_type = "viewport_region" if is_viewport else "sheet_default"

    try:
        cal = create_two_point_calibration(
            project_id=project.id,
            sheet_id=sheet.id,
            plan_document_id=doc_id,
            page_index=page_idx,
            point_a=p1,
            point_b=p2,
            known_distance_str=known_dist,
            label=label,
            calibration_type=cal_type,
            region_box=region_box,
            auto_confirm=auto_confirm,
        )
        if is_json:
            return jsonify({"success": True, "calibration_id": cal.id, "ratio": cal.scale_ratio, "status": cal.calibration_status})
        flash("Scale calibration created.", "success")
    except PlanIntelligenceServiceError as exc:
        if is_json:
            return jsonify({"success": False, "error": str(exc)}), 400
        flash(str(exc), "error")

    return redirect(url_for("plan_intelligence.measure_sheet", project_id=project.id, sheet_id=sheet.id))


@plan_intelligence_bp.route(
    "/projects/<int:project_id>/plans/sheets/<int:sheet_id>/calibrations/preset",
    methods=["POST"],
)
def create_preset_calibration_action(project_id, sheet_id):
    """Create a preset scale ratio calibration."""
    project = _get_project_or_404(project_id)
    sheet = get_sheet_or_404(project.id, sheet_id)

    is_json = request.is_json
    data = request.get_json() if is_json else request.form

    doc_id = int(data.get("plan_document_id", sheet.page_mappings[0].plan_document_id if sheet.page_mappings else 0))
    page_idx = int(data.get("page_index", sheet.page_mappings[0].page_index if sheet.page_mappings else 0))
    preset_key = str(data.get("preset_key", "")).strip()
    page_width_pts = float(data.get("page_width_points", 2592.0))
    auto_confirm = bool(data.get("auto_confirm", False) or request.form.get("auto_confirm"))

    try:
        cal = create_preset_calibration(
            project_id=project.id,
            sheet_id=sheet.id,
            plan_document_id=doc_id,
            page_index=page_idx,
            preset_key=preset_key,
            page_width_points=page_width_pts,
            auto_confirm=auto_confirm,
        )
        if is_json:
            return jsonify({"success": True, "calibration_id": cal.id, "ratio": cal.scale_ratio, "status": cal.calibration_status})
        flash(f"Preset scale '{preset_key}' applied.", "success")
    except PlanIntelligenceServiceError as exc:
        if is_json:
            return jsonify({"success": False, "error": str(exc)}), 400
        flash(str(exc), "error")

    return redirect(url_for("plan_intelligence.measure_sheet", project_id=project.id, sheet_id=sheet.id))


@plan_intelligence_bp.route(
    "/projects/<int:project_id>/plans/sheets/<int:sheet_id>/calibrations/<int:calibration_id>/confirm",
    methods=["POST"],
)
def confirm_calibration_action(project_id, sheet_id, calibration_id):
    """Explicit human confirmation action for a calibration."""
    project = _get_project_or_404(project_id)
    try:
        cal = confirm_calibration(project.id, sheet_id, calibration_id)
        if request.is_json:
            return jsonify({"success": True, "calibration_id": cal.id, "status": "confirmed"})
        flash("Calibration confirmed.", "success")
    except PlanIntelligenceServiceError as exc:
        if request.is_json:
            return jsonify({"success": False, "error": str(exc)}), 400
        flash(str(exc), "error")

    return redirect(url_for("plan_intelligence.measure_sheet", project_id=project.id, sheet_id=sheet_id))


@plan_intelligence_bp.route(
    "/projects/<int:project_id>/plans/sheets/<int:sheet_id>/calibrations/<int:calibration_id>/void",
    methods=["POST"],
)
def void_calibration_action(project_id, sheet_id, calibration_id):
    """Void a calibration record."""
    project = _get_project_or_404(project_id)
    try:
        cal = void_calibration(project.id, sheet_id, calibration_id)
        if request.is_json:
            return jsonify({"success": True, "calibration_id": cal.id, "status": "void"})
        flash("Calibration voided.", "success")
    except PlanIntelligenceServiceError as exc:
        if request.is_json:
            return jsonify({"success": False, "error": str(exc)}), 400
        flash(str(exc), "error")

    return redirect(url_for("plan_intelligence.measure_sheet", project_id=project.id, sheet_id=sheet_id))


@plan_intelligence_bp.route(
    "/projects/<int:project_id>/plans/sheets/<int:sheet_id>/calibrations/nts",
    methods=["POST"],
)
def mark_sheet_nts_action(project_id, sheet_id):
    """Flag sheet as Not To Scale (NTS)."""
    project = _get_project_or_404(project_id)
    sheet = get_sheet_or_404(project.id, sheet_id)
    doc_id = sheet.page_mappings[0].plan_document_id if sheet.page_mappings else 0
    page_idx = sheet.page_mappings[0].page_index if sheet.page_mappings else 0
    notes = request.form.get("notes") or (request.get_json().get("notes") if request.is_json else None)

    try:
        cal = mark_sheet_nts(project.id, sheet.id, doc_id, page_idx, notes=notes)
        if request.is_json:
            return jsonify({"success": True, "calibration_id": cal.id, "status": "nts"})
        flash("Sheet flagged as Not To Scale (NTS).", "info")
    except PlanIntelligenceServiceError as exc:
        if request.is_json:
            return jsonify({"success": False, "error": str(exc)}), 400
        flash(str(exc), "error")

    return redirect(url_for("plan_intelligence.measure_sheet", project_id=project.id, sheet_id=sheet.id))


@plan_intelligence_bp.route(
    "/projects/<int:project_id>/plans/sheets/<int:sheet_id>/measurements",
    methods=["POST"],
)
def create_measurement_action(project_id, sheet_id):
    """Save a manual measurement."""
    project = _get_project_or_404(project_id)
    sheet = get_sheet_or_404(project.id, sheet_id)

    is_json = request.is_json
    data = request.get_json() if is_json else request.form

    doc_id = int(data.get("plan_document_id", sheet.page_mappings[0].plan_document_id if sheet.page_mappings else 0))
    page_idx = int(data.get("page_index", sheet.page_mappings[0].page_index if sheet.page_mappings else 0))
    meas_type = str(data.get("measurement_type", "")).strip()
    label = data.get("label", "").strip() or None
    notes = data.get("notes", "").strip() or None
    explicit_cal_id = data.get("calibration_id")
    if explicit_cal_id is not None and str(explicit_cal_id).strip():
        explicit_cal_id = int(explicit_cal_id)
    else:
        explicit_cal_id = None

    if is_json:
        geometry_data = data.get("geometry_data", [])
    else:
        import json
        geom_str = data.get("geometry_data_json", "[]")
        try:
            geometry_data = json.loads(geom_str)
        except Exception:
            geometry_data = []

    try:
        meas = create_measurement(
            project_id=project.id,
            sheet_id=sheet.id,
            plan_document_id=doc_id,
            page_index=page_idx,
            measurement_type=meas_type,
            geometry_data=geometry_data,
            label=label,
            notes=notes,
            explicit_calibration_id=explicit_cal_id,
        )
        if is_json:
            return jsonify(
                {
                    "success": True,
                    "measurement_id": meas.id,
                    "computed_value": meas.computed_value,
                    "display_unit": meas.display_unit,
                    "perimeter_value": meas.perimeter_value,
                }
            )
        flash(f"Measurement '{meas.label}' saved: {meas.computed_value} {meas.display_unit}", "success")
    except PlanIntelligenceServiceError as exc:
        if is_json:
            return jsonify({"success": False, "error": str(exc)}), 400
        flash(str(exc), "error")

    return redirect(url_for("plan_intelligence.measure_sheet", project_id=project.id, sheet_id=sheet.id))


@plan_intelligence_bp.route(
    "/projects/<int:project_id>/plans/sheets/<int:sheet_id>/measurements/<int:measurement_id>/void",
    methods=["POST"],
)
def void_measurement_action(project_id, sheet_id, measurement_id):
    """Void a saved measurement."""
    project = _get_project_or_404(project_id)
    try:
        meas = void_measurement(project.id, sheet_id, measurement_id)
        if request.is_json:
            return jsonify({"success": True, "measurement_id": meas.id, "status": "void"})
        flash(f"Measurement '{meas.label}' voided.", "info")
    except PlanIntelligenceServiceError as exc:
        if request.is_json:
            return jsonify({"success": False, "error": str(exc)}), 400
        flash(str(exc), "error")

    return redirect(url_for("plan_intelligence.measure_sheet", project_id=project.id, sheet_id=sheet_id))


@plan_intelligence_bp.route("/projects/<int:project_id>/plans/takeoff")
def takeoff_index(project_id):
    """List take-off runs and packages for a project."""
    project = _get_project_or_404(project_id)
    org_id = get_current_organization_id()
    revision = ensure_default_revision(project)
    runs = list_runs_for_project(org_id, project.id)
    packages = list_packages_for_project(org_id, project.id)
    documents = [d for d in list_plan_documents(project.id) if not d.is_archived]
    return render_template(
        "plan_intelligence/takeoff_index.html",
        project=project,
        revision=revision,
        runs=runs,
        packages=packages,
        documents=documents,
    )


@plan_intelligence_bp.route("/projects/<int:project_id>/plans/takeoff/runs", methods=["POST"])
def takeoff_start_run(project_id):
    """Start a provider-neutral mock extraction run."""
    project = _get_project_or_404(project_id)
    org_id = get_current_organization_id()
    try:
        document_id = int(request.form.get("plan_document_id") or 0)
        revision_id = int(request.form.get("drawing_revision_id") or 0)
        created_by = request.form.get("created_by", "").strip()
        sheet_raw = request.form.get("sheet_ids", "").strip()
        sheet_ids = None
        if sheet_raw:
            sheet_ids = [int(s) for s in sheet_raw.split(",") if s.strip()]
        run = start_extraction_run(
            organization_id=org_id,
            project_id=project.id,
            plan_document_id=document_id,
            drawing_revision_id=revision_id,
            created_by=created_by,
            sheet_ids=sheet_ids,
        )
        flash(f"Take-off run #{run.id} {run.status} ({run.candidate_count} candidates).", "success")
        return redirect(
            url_for("plan_intelligence.takeoff_run_detail", project_id=project.id, run_id=run.id)
        )
    except (TypeError, ValueError):
        flash("Invalid take-off run request.", "error")
    except PlanIntelligenceServiceError as exc:
        flash(str(exc), "error")
    return redirect(url_for("plan_intelligence.takeoff_index", project_id=project.id))


@plan_intelligence_bp.route("/projects/<int:project_id>/plans/takeoff/runs/<int:run_id>")
def takeoff_run_detail(project_id, run_id):
    project = _get_project_or_404(project_id)
    org_id = get_current_organization_id()
    try:
        run = get_run_or_404(org_id, run_id)
    except PlanIntelligenceServiceError:
        abort(404)
    if run.project_id != project.id:
        abort(404)
    return render_template(
        "plan_intelligence/takeoff_run.html",
        project=project,
        run=run,
        candidates=run.candidates,
    )


@plan_intelligence_bp.route(
    "/projects/<int:project_id>/plans/takeoff/candidates/<int:candidate_id>/review",
    methods=["POST"],
)
def takeoff_review_candidate(project_id, candidate_id):
    project = _get_project_or_404(project_id)
    org_id = get_current_organization_id()
    try:
        reviewed_qty = request.form.get("reviewed_quantity", "").strip()
        qty = float(reviewed_qty) if reviewed_qty else None
        geom = None
        if request.form.get("x1"):
            geom = {
                "x1": request.form.get("x1"),
                "y1": request.form.get("y1"),
                "x2": request.form.get("x2"),
                "y2": request.form.get("y2"),
            }
        canonical = request.form.get("canonical_candidate_id", "").strip()
        cand = review_candidate(
            organization_id=org_id,
            candidate_id=candidate_id,
            action=request.form.get("action", ""),
            reviewed_by=request.form.get("reviewed_by", ""),
            review_reason=request.form.get("review_reason") or None,
            reviewed_quantity=qty,
            reviewed_geometry=geom,
            canonical_candidate_id=int(canonical) if canonical else None,
        )
        flash(f"Candidate #{cand.id} marked {cand.status}.", "success")
        return redirect(
            url_for(
                "plan_intelligence.takeoff_run_detail",
                project_id=project.id,
                run_id=cand.takeoff_run_id,
            )
        )
    except PlanIntelligenceServiceError as exc:
        flash(str(exc), "error")
    return redirect(url_for("plan_intelligence.takeoff_index", project_id=project.id))


@plan_intelligence_bp.route(
    "/projects/<int:project_id>/plans/takeoff/runs/<int:run_id>/packages",
    methods=["POST"],
)
def takeoff_create_package(project_id, run_id):
    project = _get_project_or_404(project_id)
    org_id = get_current_organization_id()
    try:
        package = create_draft_package(
            organization_id=org_id,
            run_id=run_id,
            created_by=request.form.get("created_by", ""),
            notes=request.form.get("notes") or None,
        )
        flash(f"Draft take-off package v{package.version_number} created.", "success")
        return redirect(
            url_for(
                "plan_intelligence.takeoff_package_detail",
                project_id=project.id,
                package_id=package.id,
            )
        )
    except PlanIntelligenceServiceError as exc:
        flash(str(exc), "error")
        return redirect(
            url_for("plan_intelligence.takeoff_run_detail", project_id=project.id, run_id=run_id)
        )


@plan_intelligence_bp.route(
    "/projects/<int:project_id>/plans/takeoff/packages/<int:package_id>"
)
def takeoff_package_detail(project_id, package_id):
    project = _get_project_or_404(project_id)
    org_id = get_current_organization_id()
    try:
        package = get_package_or_404(org_id, package_id)
    except PlanIntelligenceServiceError:
        abort(404)
    if package.project_id != project.id:
        abort(404)
    return render_template(
        "plan_intelligence/takeoff_package.html",
        project=project,
        package=package,
    )


@plan_intelligence_bp.route(
    "/projects/<int:project_id>/plans/takeoff/packages/<int:package_id>/approve",
    methods=["POST"],
)
def takeoff_approve_package(project_id, package_id):
    project = _get_project_or_404(project_id)
    org_id = get_current_organization_id()
    try:
        package = approve_package(
            organization_id=org_id,
            package_id=package_id,
            approved_by=request.form.get("approved_by", ""),
        )
        flash(
            f"Take-off package v{package.version_number} approved. Total {package.approved_total} {package.approved_unit}.",
            "success",
        )
        return redirect(
            url_for(
                "plan_intelligence.takeoff_package_detail",
                project_id=project.id,
                package_id=package.id,
            )
        )
    except PlanIntelligenceServiceError as exc:
        flash(str(exc), "error")
        return redirect(
            url_for(
                "plan_intelligence.takeoff_package_detail",
                project_id=project.id,
                package_id=package_id,
            )
        )
