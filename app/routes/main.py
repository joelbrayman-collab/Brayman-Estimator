from datetime import date
from app.services.local_time import local_today

from flask import Blueprint, jsonify, render_template, request
from flask_login import current_user

from app.services.home_planning import assemble_home_planning
from app.services.organizations import get_current_organization_id

main_bp = Blueprint("main", __name__)

HOME_ATTENTION_SHOWN = 5  # Task-First UX (31 Oct 2026): the top 5 items, each with one task button; Start stays above the fold


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
        # ONE attention list (Task-First UX, 31 Oct 2026): Home shows the same items as the full list, including the
        # Company Attention facts for the people who may see them (COMPANY_MANAGEMENT).
        attention = assemble(get_current_organization_id(), current_user, today=today)
    except Exception:  # Home must always open; the attention list is read again on the next visit
        import logging

        from flask import current_app

        if current_app.testing:
            raise

        logging.getLogger(__name__).exception("needs attention could not be read")
        attention = None
    return render_template("dashboard.html", view=view, attention=attention, attention_shown=HOME_ATTENTION_SHOWN)


@main_bp.route("/attention/count")
def attention_count():
    """The header bell: how many items are waiting on you. Never fails the page that asked."""
    from app.services.needs_attention import count_for

    try:
        count = count_for(get_current_organization_id(), current_user)
    except Exception:
        from flask import current_app

        if current_app.testing:
            raise
        current_app.logger.exception("attention count could not be read")
        count = 0
    response = jsonify({"count": count})
    response.headers["Cache-Control"] = "no-store"
    return response


def _attention_of(kinds):
    from app.services.needs_attention import assemble

    view = assemble(get_current_organization_id(), current_user)
    return [i for i in view["items"] if i["kind"] in kinds]


@main_bp.route("/more")
def more():
    """More: every reference page that is not one of the six primary destinations (Task-First UX, 31 Oct 2026)."""
    from app.shell import more_sections

    return render_template("more.html", sections=more_sections(), heading="More",
                           purpose="Calculators, prices and costs, lists of every record, past jobs and help.")


@main_bp.route("/admin")
def admin():
    """Admin (the header gear): company settings, people, pricing policy, templates and catalogues. Each page keeps
    its own permission check; this page only lists what the person may open."""
    from app.shell import admin_sections

    return render_template("more.html", sections=admin_sections(), heading="Admin",
                           purpose="How the company is set up: profile, people, crews, pricing policy, templates and "
                                   "catalogues.", admin=True)


@main_bp.route("/purchasing")
def purchasing():
    """Purchasing: what has to be bought, priced, approved or delivered, across every job (Buy What's Needed)."""
    from app.models.supplier_portal import SHARE_OPENED, SHARE_RETURNED, SHARE_SENT, SupplierRequestShare
    from app.models import Project

    org = get_current_organization_id()
    items = _attention_of({"quotes", "deliveries", "materials", "purchasing"})
    open_by_project = {}
    for share in SupplierRequestShare.query.filter(SupplierRequestShare.organization_id == org,
                                                   SupplierRequestShare.status.in_((SHARE_SENT, SHARE_OPENED,
                                                                                    SHARE_RETURNED))).all():
        open_by_project[share.project_id] = open_by_project.get(share.project_id, 0) + 1
    projects = {p.id: p for p in Project.query.filter(Project.organization_id == org,
                                                      Project.id.in_(list(open_by_project) or [0])).all()}
    jobs = [{"project": projects[pid], "open": n} for pid, n in sorted(open_by_project.items()) if pid in projects]
    from app.navigation import PURCHASING_LINKS as links

    return render_template("task_landing.html", heading="Purchasing", landing="purchasing",
                           purpose="Buy what's needed",
                           why="Prices to review, orders to place and deliveries to answer, across every job. "
                               "Each one opens the job's purchasing screen.",
                           items=items, links=links, jobs=jobs)


@main_bp.route("/time-and-money")
def time_and_money():
    """Time & Money: time to approve, receipts, invoices and QuickBooks, in one place."""
    items = _attention_of({"time", "receipts", "quickbooks"})
    from app.navigation import TIME_AND_MONEY_LINKS as links

    return render_template("task_landing.html", heading="Time & Money", landing="time-and-money",
                           purpose="Keep time and money up to date",
                           why="Approve the crew's time, review receipts, send invoices and keep QuickBooks matched.",
                           items=items, links=links, jobs=[])
