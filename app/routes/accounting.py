"""Accounting pages: invoices, QuickBooks files, reconciliation (Joel, 21 Oct 2026).

/accounting                         overview: QuickBooks status, exports, last reconciliation, history
/accounting/invoices                every invoice; /accounting/projects/<id>/invoices/new makes one
/accounting/invoices/<id>           one invoice (void, record a correction)
/accounting/export/<kind>           preview (GET) and download (POST) a QuickBooks file
/accounting/reconcile               upload QuickBooks' Invoice List CSV

Office members only: a field-only member is refused (403) here as well as by the Field wall.
"""

from __future__ import annotations

from flask import Blueprint, Response, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user

from app import db
from app.models import Project
from app.models.accounting import INVOICE_KIND_LABELS, CustomerInvoice
from app.services import accounting as svc
from app.services import quickbooks_online_connector as qbo
from app.services.access_domains import require_office_financial_access
from app.services.organizations import get_current_organization_id

accounting_bp = Blueprint("accounting", __name__, url_prefix="/accounting")

EXPORTS = {
    "customers": ("Customers", "Settings → Import data → Customers"),
    "suppliers": ("Suppliers (vendors)", "Settings → Import data → Suppliers"),
    "invoices": ("Invoices", "Settings → Import data → Invoices"),
    "bills": ("Bills from purchase orders", "Settings → Import data → Bills (check each against the supplier's invoice first)"),
    "purchase_orders": ("Purchase orders (list to enter by hand)", "QuickBooks has no purchase-order import: + New → Purchase order"),
}


@accounting_bp.before_request
def _office_only():
    return require_office_financial_access()


def _org():
    return get_current_organization_id()


def _invoice_or_404(invoice_id):
    inv = db.session.get(CustomerInvoice, invoice_id)
    if inv is None or inv.organization_id != _org():
        abort(404)
    return inv


@accounting_bp.route("")
def index():
    org = _org()
    counts = {k: (lambda p: (len(p["fresh"]), len(p["again"])))(svc.preview(org, k)) for k in EXPORTS}
    return render_template("accounting/index.html", qbo=qbo.status(), exports=EXPORTS, counts=counts,
                           last=svc.last_reconciliation(org), events=svc.history(org, 30),
                           invoices=svc.invoices(org)[:10])


@accounting_bp.route("/invoices")
def invoices():
    return render_template("accounting/invoices.html", invoices=svc.invoices(_org()))


@accounting_bp.route("/projects/<int:project_id>/invoices/new", methods=["GET", "POST"])
def new_invoice(project_id):
    org = _org()
    project = db.session.get(Project, project_id)
    if project is None or project.organization_id != org:
        abort(404)
    if request.method == "POST":
        form = request.form
        try:
            inv = svc.create_invoice(org, project, user=current_user,
                                     proposal_id=form.get("proposal_id") or None,
                                     change_order_id=form.get("change_order_id") or None,
                                     kind=form.get("kind") or None, amount=form.get("amount") or None,
                                     percent=form.get("percent") or None, description=form.get("description", ""))
        except svc.AccountingError as exc:
            flash(str(exc), "error")
        else:
            flash(f"Invoice {inv.number} made: ${inv.total:,.2f} with HST. Export it on the Accounting page.", "success")
            return redirect(url_for("accounting.invoice", invoice_id=inv.id))
    return render_template("accounting/new_invoice.html", project=project, kinds=INVOICE_KIND_LABELS,
                           proposals=svc.accepted_proposals(org, project.id),
                           change_orders=svc.approved_change_orders(org, project.id),
                           existing=svc.invoices(org, project.id))


@accounting_bp.route("/invoices/<int:invoice_id>")
def invoice(invoice_id):
    inv = _invoice_or_404(invoice_id)
    events = [e for e in svc.history(_org(), 500) if e.record_key == inv.number]
    return render_template("accounting/invoice.html", invoice=inv, events=events, job=svc.job_reference(inv.project))


@accounting_bp.route("/invoices/<int:invoice_id>/void", methods=["POST"])
def void(invoice_id):
    inv = _invoice_or_404(invoice_id)
    try:
        svc.void_invoice(_org(), inv, user=current_user, reason=request.form.get("reason", ""))
    except svc.AccountingError as exc:
        flash(str(exc), "error")
    else:
        flash(f"Invoice {inv.number} is void. If it is already in QuickBooks, void it there too.", "success")
    return redirect(url_for("accounting.invoice", invoice_id=inv.id))


@accounting_bp.route("/invoices/<int:invoice_id>/correction", methods=["POST"])
def correction(invoice_id):
    inv = _invoice_or_404(invoice_id)
    try:
        svc.record_correction(_org(), inv, user=current_user, note=request.form.get("note", ""))
    except svc.AccountingError as exc:
        flash(str(exc), "error")
    else:
        flash("Correction recorded in the history.", "success")
    return redirect(url_for("accounting.invoice", invoice_id=inv.id))


@accounting_bp.route("/export/<kind>", methods=["GET", "POST"])
def export(kind):
    if kind not in EXPORTS:
        abort(404)
    org = _org()
    include = request.values.get("include_exported") == "1"
    if request.method == "POST":
        try:
            filename, content, _ = svc.export(org, kind, user=current_user, include_exported=include,
                                              reason=request.form.get("reason", ""))
        except svc.AccountingError as exc:
            flash(str(exc), "error")
            return redirect(url_for("accounting.export", kind=kind))
        return Response(content, mimetype="text/csv",
                        headers={"Content-Disposition": f'attachment; filename="{filename}"'})
    return render_template("accounting/export.html", kind=kind, label=EXPORTS[kind], include=include,
                           preview=svc.preview(org, kind, include_exported=include))


@accounting_bp.route("/reconcile", methods=["GET", "POST"])
def reconcile():
    result = None
    if request.method == "POST":
        upload = request.files.get("report")
        try:
            if upload is None or not upload.filename:
                raise svc.AccountingError("Choose the CSV you exported from QuickBooks.")
            if not upload.filename.lower().endswith(".csv"):
                raise svc.AccountingError("Choose a .csv file (QuickBooks: Export to CSV).")
            result = svc.reconcile(_org(), filename=upload.filename, content=upload.read(svc.MAX_REPORT_BYTES + 1),
                                   user=current_user)
        except svc.AccountingError as exc:
            flash(str(exc), "error")
    return render_template("accounting/reconcile.html", result=result)
