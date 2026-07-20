from flask import Blueprint, flash, redirect, render_template, request, url_for

from app import db
from app.models import Client, Project

projects_bp = Blueprint("projects", __name__, url_prefix="/projects")


@projects_bp.route("/")
def list_projects():
    projects = Project.query.order_by(Project.created_at.desc()).all()
    return render_template("projects/list.html", projects=projects)


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
        return redirect(url_for("projects.list_projects"))

    return render_template("projects/form.html", clients=clients)
