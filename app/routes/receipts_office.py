"""Suzanne's Receipts Inbox and the QuickBooks Online connection (25 Oct 2026), on the Accounting blueprint.

Accounting's own rule applies (accounting_bp.before_request: require_office_financial_access): the owner, System
Administrators and office members; a Field-only member never. Connecting or disconnecting QuickBooks is further
limited to the owner or a System Administrator (quickbooks_online.require_connect_authority).

/accounting/receipts                         the inbox, by status and job
/accounting/receipts/<id>                    the original image, review, approve, transfer result, retry, history
/accounting/quickbooks-online                connection status, Connect / Disconnect, the accounting mapping
/accounting/quickbooks/callback              Intuit's OAuth 2.0 redirect (state checked, code exchanged once)
/accounting/quickbooks-online/reconciliation  every confirmed receipt with its QuickBooks transaction and attachment
"""

from __future__ import annotations

import hmac

from flask import abort, flash, redirect, render_template, request, session, url_for
from flask_login import current_user

from app import db
from app.models.field_operations import RECEIPT_STATUS_LABELS, RECEIPT_STATUSES
from app.routes.accounting import accounting_bp
from app.services import quickbooks_online as qbo
from app.services import receipts as R
from app.services.field_operations import FieldOperationError
from app.services.organizations import get_current_organization_id


def _org():
    return get_current_organization_id()


def _receipt_or_404(receipt_id):
    row = R.receipt_for(_org(), receipt_id)
    if row is None:
        abort(404)
    return row


@accounting_bp.route("/receipts")
def receipts_inbox():
    org = _org()
    status = request.args.get("status") if request.args.get("status") in RECEIPT_STATUSES else None
    project_id = request.args.get("project_id", type=int)
    return render_template("accounting/receipts.html", rows=R.inbox(org, status=status, project_id=project_id),
                           counts=R.counts(org), status=status, labels=RECEIPT_STATUS_LABELS,
                           statuses=RECEIPT_STATUSES, project_id=project_id, projects=R.project_choices(org),
                           qbo=qbo.status(org))


@accounting_bp.route("/receipts/<int:receipt_id>", methods=["GET", "POST"])
def receipt_detail(receipt_id):
    row = _receipt_or_404(receipt_id)
    org = row.organization_id
    if request.method == "POST":
        action = request.form.get("action")
        transfer = row.qbo_transfer
        try:
            if action == "review":
                R.review(row, current_user, request.form)
                flash("Review saved. Approve it for QuickBooks when it is right.", "success")
            elif action == "flag":
                R.flag(row, current_user, request.form.get("reason", ""))
                flash("Marked Needs Attention.", "success")
            elif action == "approve":
                result = R.approve(row, current_user)
                flash(result["message"] or "Approved for QuickBooks.", "success")
            elif action == "retry" and transfer is not None:
                qbo.retry(transfer, current_user)
                flash(qbo.outcome_message(row) or "Retried.", "success")
            elif action == "choose" and transfer is not None:
                qbo.choose_candidate(transfer, current_user, txn_type=request.form.get("txn_type", ""),
                                     txn_id=request.form.get("txn_id", ""))
                flash(qbo.outcome_message(row), "success")
            elif action == "create_anyway" and transfer is not None:
                qbo.create_anyway(transfer, current_user, request.form.get("reason", ""))
                flash(qbo.outcome_message(row), "success")
            elif action == "link_vendor":
                qbo.link_vendor(org, current_user, row.vendor_name or "", request.form.get("qbo_name", ""))
                flash("QuickBooks vendor linked. Press Retry to send.", "success")
            elif action == "link_customer":
                qbo.link_customer(org, current_user, row.project, request.form.get("qbo_name", ""))
                flash("QuickBooks customer linked. Press Retry to send.", "success")
            else:
                abort(400)
        except (FieldOperationError, qbo.QuickBooksOnlineError) as exc:
            db.session.rollback()
            flash(str(exc), "error")
        return redirect(url_for("accounting.receipt_detail", receipt_id=row.id))
    db.session.refresh(row)
    return render_template("accounting/receipt.html", receipt=row, transfer=row.qbo_transfer,
                           projects=R.project_choices(org), orders=R.purchase_order_choices(row),
                           history=R.history(row), qbo_events=qbo.events(org, receipt_id=row.id),
                           qbo=qbo.status(org), blockers=R.approval_blockers(row),
                           outcome=qbo.outcome_message(row))


@accounting_bp.route("/quickbooks-online", methods=["GET", "POST"])
def quickbooks_online():
    org = _org()
    if request.method == "POST":
        action = request.form.get("action")
        try:
            if action == "mapping":
                qbo.save_mapping(org, current_user, request.form)
                flash("QuickBooks accounts saved.", "success")
            elif action == "send_waiting":
                summary = qbo.send_waiting(org, actor=current_user)
                flash(f"Sent {summary['tried']}: {summary['confirmed']} confirmed, {summary['review']} need review, "
                      f"{summary['failed']} failed, {summary['waiting']} still waiting.", "success")
            elif action == "disconnect":
                qbo.disconnect(org, current_user)
                flash("Disconnected from QuickBooks Online.", "success")
            else:
                abort(400)
        except qbo.QuickBooksOnlineError as exc:
            db.session.rollback()
            flash(str(exc), "error")
        return redirect(url_for("accounting.quickbooks_online"))
    from app.services.instance_authority import is_instance_owner, is_system_administrator

    return render_template("accounting/quickbooks_online.html", qbo=qbo.status(org), lists=qbo.lists(org),
                           counts=qbo.transfer_counts(org), events=qbo.events(org, limit=40),
                           can_connect=is_instance_owner(current_user, org) or is_system_administrator(current_user, org),
                           payment_types=("Cash", "Check", "CreditCard"))


@accounting_bp.route("/quickbooks-online/connect", methods=["POST"])
def quickbooks_online_connect():
    org = _org()
    try:
        url, state = qbo.authorization_url(org, current_user)
    except qbo.QuickBooksOnlineError as exc:
        flash(str(exc), "error")
        return redirect(url_for("accounting.quickbooks_online"))
    session[qbo.STATE_SESSION_KEY] = {"digest": qbo.state_digest(state), "org": org}
    return redirect(url)


@accounting_bp.route("/quickbooks/callback")
def quickbooks_callback():
    """Intuit sends the person back here with ?code&realmId&state (or ?error). One use; the state must match."""
    org = _org()
    expected = session.pop(qbo.STATE_SESSION_KEY, None) or {}
    state = request.args.get("state", "")
    if not expected or expected.get("org") != org or not hmac.compare_digest(expected.get("digest", ""),
                                                                            qbo.state_digest(state)):
        flash("That QuickBooks sign-in was not started here (or is out of date). Press Connect to QuickBooks again.",
              "error")
        return redirect(url_for("accounting.quickbooks_online"))
    if request.args.get("error"):
        flash("QuickBooks was not connected: access was not given on Intuit's page.", "error")
        return redirect(url_for("accounting.quickbooks_online"))
    try:
        conn = qbo.complete_authorization(org, current_user, code=request.args.get("code", ""),
                                          realm_id=request.args.get("realmId", ""))
        flash(f"Connected to QuickBooks Online: {conn.company_name or conn.realm_id}. Choose the accounts below.",
              "success")
    except qbo.QuickBooksOnlineError as exc:
        db.session.rollback()
        flash(str(exc), "error")
    except Exception:  # never show a token or a stack in the page
        db.session.rollback()
        flash("QuickBooks could not be connected. Nothing was saved. Try Connect to QuickBooks again.", "error")
    return redirect(url_for("accounting.quickbooks_online"))


@accounting_bp.route("/quickbooks-online/reconciliation")
def quickbooks_online_reconciliation():
    org = _org()
    return render_template("accounting/qbo_reconciliation.html", rows=qbo.reconciliation(org))
