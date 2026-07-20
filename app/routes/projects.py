from flask import Blueprint, flash, redirect, render_template, request, url_for

from app import db
from app.models import Client, Project, Proposal
from app.project_controls import repository as change_order_repo

projects_bp = Blueprint("projects", __name__, url_prefix="/projects")


@projects_bp.route("/")
def list_projects():
    projects = Project.query.order_by(Project.created_at.desc()).all()
    return render_template("projects/list.html", projects=projects)


@projects_bp.route("/<int:id>")
def view_project(id):
    project = Project.query.get_or_404(id)
    estimates = sorted(
        project.estimates,
        key=lambda row: row.updated_at,
        reverse=True,
    )
    proposals = (
        Proposal.query.filter(
            Proposal.estimate_id.in_([e.id for e in estimates] or [-1])
        )
        .order_by(Proposal.updated_at.desc())
        .all()
        if estimates
        else []
    )
    # Also include proposals linked only by project snapshot via estimate
    change_orders = change_order_repo.list_change_orders_for_project(project.id)
    return render_template(
        "projects/detail.html",
        project=project,
        estimates=estimates,
        proposals=proposals,
        change_orders=change_orders,
    )


@projects_bp.route("/new", methods=["GET", "POST"])
def create_project():
    clients = Client.query.order_by(Client.name.asc()).all()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        client_id = request.form.get("client_id", type=int)

        if not name or not client_id:
            flash("Project name and client are required.", "error")
            return render_template("projects/form.html", clients=clients)

        project = Project(
            name=name,
            project_number=request.form.get("project_number", "").strip() or None,
            address=request.form.get("address", "").strip(),
            status=request.form.get("status", "Lead"),
            description=request.form.get("description", "").strip(),
            client_id=client_id,
        )

        db.session.add(project)
        db.session.commit()

        flash("Project created successfully.", "success")
        return redirect(url_for("projects.view_project", id=project.id))

    return render_template("projects/form.html", clients=clients)
