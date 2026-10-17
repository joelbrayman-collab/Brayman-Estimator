"""Public client proposal link (Joel, 17 Oct 2026).

Narrow /proposal/* exemption like /sign/*: no office chrome, no client account.
The client reviews the issued proposal, may download it, and ticks Accept Proposal.
"""

from __future__ import annotations

from flask import Blueprint, abort, render_template, request, send_file, url_for

from app.services.brand_profile import (
    BrandProfileServiceError,
    brand_logo_filesystem_path,
    brand_logo_mimetype,
    get_proposal_brand_render_context,
)
from app.services.proposal_acceptance import (
    ProposalAcceptanceError,
    accept_via_link,
    acceptance_for,
    resolve_link,
)

proposal_link_bp = Blueprint("proposal_link", __name__, url_prefix="/proposal")


def _section_rows(proposal):
    rows = []
    for section in proposal.sections:
        items = [item for item in section.line_items
                 if proposal.show_allowances or item.item_type != "Allowance"]
        rows.append({"section": section, "line_items": items})
    return rows


def _unavailable(message, status=410):
    return render_template("proposals/link_unavailable.html", message=message), status


def _render(link, credential, *, error=None, typed_name=None, status=200):
    proposal = link.proposal
    try:
        brand = get_proposal_brand_render_context(proposal)
    except BrandProfileServiceError:
        abort(404)
    logo_url = None
    if brand.has_logo and brand_logo_filesystem_path(brand) is not None:
        logo_url = url_for("proposal_link.logo", credential=credential)
    response = render_template(
        "proposals/preview.html",
        proposal=proposal,
        template=proposal.proposal_template,
        brand=brand,
        logo_url=logo_url,
        section_rows=_section_rows(proposal),
        client_view=True,
        client_pdf_url=url_for("proposal_link.pdf", credential=credential),
        accept_url=url_for("proposal_link.accept", credential=credential),
        acceptance=acceptance_for(proposal),
        error=error,
        typed_name=typed_name,
    )
    return response, status, {"Cache-Control": "no-store", "Referrer-Policy": "no-referrer"}


@proposal_link_bp.route("/<credential>", methods=["GET"])
def view(credential):
    try:
        link = resolve_link(credential)
    except ProposalAcceptanceError as exc:
        return _unavailable(str(exc))
    return _render(link, credential)


@proposal_link_bp.route("/<credential>/accept", methods=["POST"])
def accept(credential):
    name = request.form.get("confirmed_name", "")
    try:
        accept_via_link(
            credential,
            confirmed_name=name,
            accepted=request.form.get("accept") == "yes",
            client_ip=request.remote_addr,
            user_agent=request.headers.get("User-Agent", ""),
        )
    except ProposalAcceptanceError as exc:
        try:
            link = resolve_link(credential, record_view=False)
        except ProposalAcceptanceError as inner:
            return _unavailable(str(inner))
        return _render(link, credential, error=str(exc), typed_name=name, status=400)
    link = resolve_link(credential, record_view=False)
    return _render(link, credential)


@proposal_link_bp.route("/<credential>/pdf", methods=["GET"])
def pdf(credential):
    try:
        link = resolve_link(credential, record_view=False)
    except ProposalAcceptanceError as exc:
        return _unavailable(str(exc))
    from app.services.proposal_pdf import generate_proposal_pdf, sanitize_pdf_filename

    proposal = link.proposal
    buffer = generate_proposal_pdf(proposal)
    return send_file(buffer, mimetype="application/pdf", as_attachment=True,
                     download_name=sanitize_pdf_filename(proposal))


@proposal_link_bp.route("/<credential>/logo", methods=["GET"])
def logo(credential):
    try:
        link = resolve_link(credential, record_view=False)
        brand = get_proposal_brand_render_context(link.proposal)
    except (ProposalAcceptanceError, BrandProfileServiceError):
        abort(404)
    path = brand_logo_filesystem_path(brand)
    if path is None:
        abort(404)
    return send_file(path, mimetype=brand_logo_mimetype(brand), as_attachment=False, max_age=0)
