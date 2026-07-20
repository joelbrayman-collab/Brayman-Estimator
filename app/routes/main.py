from flask import Blueprint, render_template

from app.models import Client, CostItem, Estimate, Project

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def dashboard():
    client_count = Client.query.count()
    project_count = Project.query.count()
    cost_item_count = CostItem.query.filter_by(is_active=True).count()
    estimate_count = Estimate.query.count()

    return render_template(
        "dashboard.html",
        client_count=client_count,
        project_count=project_count,
        cost_item_count=cost_item_count,
        estimate_count=estimate_count,
    )
