"""Public supplier quotation link for the customer (Supplier PRO Desk, 20 Oct 2026).

Like /proposal/*: no account, no office chrome. The secret in the address is the only credential. The
customer reviews the issued quotation, downloads it, and accepts or declines by typing their name.
Accepting starts no contract.
"""

from __future__ import annotations

from flask import Blueprint, Response, render_template, request

from app.services import supplier_pro_desk as P

supplier_quote_link_bp = Blueprint("supplier_quote_link", __name__, url_prefix="/quote")

HEADERS = {"Cache-Control": "no-store", "Referrer-Policy": "no-referrer", "X-Content-Type-Options": "nosniff"}


def _unavailable(message):
    return render_template("supplier/pro_desk/link_unavailable.html", message=message), 410, HEADERS


@supplier_quote_link_bp.route("/<credential>", methods=["GET"])
def view(credential):
    try:
        link = P.resolve_link(credential)
    except P.ProDeskError as exc:
        return _unavailable(str(exc))
    q = link.quote
    return render_template("supplier/pro_desk/customer.html", q=q, frozen=q.issued_json or {}, credential=credential,
                           expired=P._expired(q)), 200, HEADERS


@supplier_quote_link_bp.route("/<credential>/quotation.pdf", methods=["GET"])
def pdf(credential):
    from app.routes.supplier_pro_desk import quote_pdf_bytes

    try:
        link = P.resolve_link(credential, record_view=False)
    except P.ProDeskError as exc:
        return _unavailable(str(exc))
    return Response(quote_pdf_bytes(link.quote), mimetype="application/pdf",
                    headers={**HEADERS, "Content-Disposition": f'inline; filename="{link.quote.number}-material-quotation.pdf"'})


@supplier_quote_link_bp.route("/<credential>/answer", methods=["POST"])
def answer(credential):
    try:
        link = P.resolve_link(credential, record_view=False)
    except P.ProDeskError as exc:
        return _unavailable(str(exc))
    accepted = request.form.get("answer") == "accept"
    if accepted and request.form.get("agree") != "yes":
        q = link.quote
        return render_template("supplier/pro_desk/customer.html", q=q, frozen=q.issued_json or {}, credential=credential,
                               expired=P._expired(q), error="Tick the box to confirm you accept this quotation.",
                               typed_name=request.form.get("customer_name", "")), 400, HEADERS
    try:
        q = P.accept_via_link(credential, name=request.form.get("customer_name", ""), accepted=accepted)
    except P.ProDeskError as exc:
        q = link.quote
        return render_template("supplier/pro_desk/customer.html", q=q, frozen=q.issued_json or {}, credential=credential,
                               expired=P._expired(q), error=str(exc), typed_name=request.form.get("customer_name", "")), 400, HEADERS
    return render_template("supplier/pro_desk/customer.html", q=q, frozen=q.issued_json or {}, credential=credential,
                           expired=False, answered=True), 200, HEADERS
