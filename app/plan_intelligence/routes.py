"""Plan Intelligence Phase A routes — project-scoped PDF upload."""

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
from app.plan_intelligence.services import (
    PlanIntelligenceServiceError,
    delete_plan_document,
    get_plan_document,
    list_plan_documents,
    open_plan_document_file,
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
    documents = list_plan_documents(project.id)
    return render_template(
        "plan_intelligence/list.html",
        project=project,
        documents=documents,
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

        if not document.has_text_layer:
            flash(
                "PDF stored, but no text layer was detected. "
                "Searchable PDFs are preferred for future take-off.",
                "error",
            )
        else:
            flash("Plan PDF uploaded.", "success")
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
    return render_template(
        "plan_intelligence/detail.html",
        project=project,
        document=document,
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
    "/projects/<int:project_id>/plans/<int:document_id>/delete",
    methods=["POST"],
)
def delete_plan(project_id, document_id):
    project = Project.query.get_or_404(project_id)
    document = get_plan_document(project.id, document_id)
    if document is None:
        abort(404)
    try:
        delete_plan_document(document)
    except PlanIntelligenceServiceError as exc:
        flash(str(exc), "error")
        return redirect(
            url_for(
                "plan_intelligence.view_plan",
                project_id=project.id,
                document_id=document_id,
            )
        )
    flash("Plan document deleted.", "success")
    return redirect(url_for("plan_intelligence.list_plans", project_id=project.id))
