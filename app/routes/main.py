from datetime import date
from app.services.local_time import local_today

from flask import Blueprint, render_template, request
from flask_login import current_user

from app.services.home_planning import assemble_home_planning
from app.services.organizations import get_current_organization_id

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def dashboard():
    today = local_today()
    view = assemble_home_planning(
        get_current_organization_id(),
        year=request.args.get("year", type=int),
        month=request.args.get("month", type=int),
        selected_day=request.args.get("day", type=int),
        today=today,
        viewer=current_user,
    )
    from app.services.needs_attention import assemble

    try:
        # Company Attention facts stay in the briefing below (no repeat); the full page lists everything.
        attention = assemble(get_current_organization_id(), current_user, today=today, include_company_facts=False)
    except Exception:  # Home must always open; the attention list is read again on the next visit
        import logging

        from flask import current_app

        if current_app.testing:
            raise

        logging.getLogger(__name__).exception("needs attention could not be read")
        attention = None
    return render_template("dashboard.html", view=view, attention=attention)
