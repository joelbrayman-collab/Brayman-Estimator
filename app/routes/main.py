from datetime import date

from flask import Blueprint, render_template, request
from flask_login import current_user

from app.services.home_planning import assemble_home_planning
from app.services.organizations import get_current_organization_id

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def dashboard():
    today = date.today()
    view = assemble_home_planning(
        get_current_organization_id(),
        year=request.args.get("year", type=int),
        month=request.args.get("month", type=int),
        selected_day=request.args.get("day", type=int),
        today=today,
        viewer=current_user,
    )
    return render_template("dashboard.html", view=view)
