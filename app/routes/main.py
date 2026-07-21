from flask import Blueprint, render_template

from app.models import Client, CostItem, Estimate, Project, Proposal
from app.project_controls import repository as change_order_repo
from app.project_controls.models import OPEN_CHANGE_ORDER_STATUSES

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def dashboard():
    client_count = Client.query.count()
    project_count = Project.query.count()
    cost_item_count = CostItem.query.filter_by(is_active=True).count()
    estimate_count = Estimate.query.count()
    proposal_count = Proposal.query.count()
    draft_proposal_count = Proposal.query.filter_by(status="Draft").count()
    issued_proposal_count = Proposal.query.filter_by(status="Issued").count()

    open_change_order_count = change_order_repo.count_open_change_orders()
    pending_change_order_count = change_order_repo.count_pending_approval()
    approved_change_orders_month = change_order_repo.count_approved_this_month()
    change_order_value = change_order_repo.sum_change_order_value(
        statuses=tuple(OPEN_CHANGE_ORDER_STATUSES) + ("Approved",)
    )

    return render_template(
        "dashboard.html",
        client_count=client_count,
        project_count=project_count,
        cost_item_count=cost_item_count,
        estimate_count=estimate_count,
        proposal_count=proposal_count,
        draft_proposal_count=draft_proposal_count,
        issued_proposal_count=issued_proposal_count,
        open_change_order_count=open_change_order_count,
        pending_change_order_count=pending_change_order_count,
        approved_change_orders_month=approved_change_orders_month,
        change_order_value=change_order_value,
    )


@main_bp.route("/contracts")
def contracts():
    return render_template("contracts.html")
