"""Cost and margin control, actuals and closeout by work package (Joel, 30 Oct 2026). Office only."""

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user

from app.models.project import Project
from app.routes.projects import projects_bp
from app.services.organizations import get_current_organization_id


def _project(project_id):
    return Project.query.filter_by(id=project_id, organization_id=get_current_organization_id()).first_or_404()


@projects_bp.route("/<int:id>/package-controls", methods=["GET", "POST"])
def package_controls(id):
    from app.services import package_controls as PC

    project = _project(id)
    if request.method == "POST":
        actor = (getattr(current_user, "display_name", None) or getattr(current_user, "email", "") or "").strip()
        try:
            PC.record_closeout(project, actor=actor, note=request.form.get("note", ""))
        except ValueError as exc:
            flash(str(exc), "error")
        else:
            flash("Closeout recorded. Its calibration factors are proposals for future estimates; nothing is "
                  "changed automatically.", "success")
        return redirect(url_for("projects.package_controls", id=project.id))
    from app.models.closeout import ProjectCloseoutRecord

    return render_template("projects/package_controls.html", project=project, report=PC.closeout_report(project),
                           closeouts=ProjectCloseoutRecord.query.filter_by(project_id=project.id)
                           .order_by(ProjectCloseoutRecord.id.desc()).all(),
                           calibration=PC.calibration_proposals(project.organization_id))
