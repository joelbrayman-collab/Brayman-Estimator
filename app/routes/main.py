from flask import Blueprint, render_template

from app.models import Client, Project

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def dashboard():
    client_count = Client.query.count()
    project_count = Project.query.count()

    return render_template(
        "dashboard.html",
        client_count=client_count,
        project_count=project_count,
    )
