"""Plan Intelligence routes — upload, indexing, search, archive."""

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
from app.plan_intelligence.models import PlanAuditEvent, ProcessingAttempt
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

    return render_template(
        "plan_intelligence/list.html",
        project=project,
        documents=documents,
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
    return render_template(
        "plan_intelligence/detail.html",
        project=project,
        document=document,
        pages=document.pages,
        attempts=attempts,
        audit_events=audit_events,
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
