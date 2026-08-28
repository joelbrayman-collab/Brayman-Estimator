"""Plan Intelligence routes — upload, indexing, search, archive, and Sheet Intelligence (M009)."""

from flask import (
    Blueprint,
    abort,
    flash,
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

plan_intelligence_bp = Blueprint(
    "plan_intelligence",
    __name__,
    url_prefix="",
)


@plan_intelligence_bp.route("/projects/<int:project_id>/plans")
def list_plans(project_id):
    project = Project.query.get_or_404(project_id)
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
    project = Project.query.get_or_404(project_id)
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
    project = Project.query.get_or_404(project_id)
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
    project = Project.query.get_or_404(project_id)
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
    project = Project.query.get_or_404(project_id)
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
    project = Project.query.get_or_404(project_id)
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
    project = Project.query.get_or_404(project_id)
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
    project = Project.query.get_or_404(project_id)
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
    project = Project.query.get_or_404(project_id)
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
    project = Project.query.get_or_404(project_id)
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
    project = Project.query.get_or_404(project_id)
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
    project = Project.query.get_or_404(project_id)
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
    project = Project.query.get_or_404(project_id)
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
    project = Project.query.get_or_404(project_id)
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
    project = Project.query.get_or_404(project_id)
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
    project = Project.query.get_or_404(project_id)
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
    project = Project.query.get_or_404(project_id)
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
    project = Project.query.get_or_404(project_id)
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
    project = Project.query.get_or_404(project_id)
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
