from datetime import datetime

from flask import Blueprint, abort, flash, redirect, render_template, request, send_file, session, url_for

from app import db
from app.models.estimate import Estimate
from app.models.project import Project
from app.models.proposal import (
    PROPOSAL_STATUSES,
    Proposal,
    ProposalLineItem,
    ProposalSection,
    ProposalTemplate,
)
from app.services.brand_profile import (
    BrandProfileServiceError,
    brand_logo_filesystem_path,
    brand_logo_mimetype,
    get_proposal_brand_render_context,
)
from app.services.organizations import get_current_organization_id
from app.services.proposal_pdf import (
    generate_proposal_pdf,
    sanitize_pdf_filename,
)
from app.services.proposals import (
    ProposalServiceError,
    build_proposal_snapshot,
    create_proposal,
    get_active_templates,
    get_default_template,
    get_estimate_and_version,
    is_proposal_immutable,
    suggest_next_proposal_number,
    update_proposal,
    update_proposal_line_item,
    update_proposal_status,
)
from app.services.proposal_acceptance import (
    ProposalAcceptanceError,
    acceptance_for,
    decline_for,
    current_link,
    estimate_sign_off_blockers,
    proposal_content_sha256,
    proposal_send_blockers,
    record_office_acceptance,
    send_proposal_to_client,
    sign_off_estimate,
    withdraw_link_after_change,
)
from app.models.proposal_acceptance import OFFICE_ACCEPTANCE_CHANNELS

proposals_bp = Blueprint("proposals", __name__)

# Joel, 17 Oct 2026: a proposal is issued only by sending it to the client from
# CalibraytAI, and accepted only by the client (or recorded by the office).
ISSUED_BY_FLOW_ONLY = ("Issued", "Accepted")
ISSUED_BY_FLOW_MESSAGE = (
    "A proposal is issued by sending it to the client from CalibraytAI, and accepted when the "
    "client accepts it. Use Send proposal to client on the proposal page."
)
OFFICE_STATUSES = tuple(s for s in PROPOSAL_STATUSES if s not in ISSUED_BY_FLOW_ONLY)


def _parse_date(value):
    value = (value or "").strip()
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d").date()


def _bool_field(name, default=False):
    if request.method != "POST":
        return default
    return request.form.get(name) == "on" or request.form.get(name) == "1"


def _proposal_form_from_request():
    return {
        "proposal_number": request.form.get("proposal_number", "").strip(),
        "proposal_template_id": request.form.get("proposal_template_id", "").strip(),
        "title": request.form.get("title", "").strip(),
        "status": request.form.get("status", "Draft").strip(),
        "client_name": request.form.get("client_name", "").strip(),
        "client_company": request.form.get("client_company", "").strip(),
        "client_address": request.form.get("client_address", "").strip(),
        "client_email": request.form.get("client_email", "").strip(),
        "client_phone": request.form.get("client_phone", "").strip(),
        "project_name": request.form.get("project_name", "").strip(),
        "project_address": request.form.get("project_address", "").strip(),
        "intro_text": request.form.get("intro_text", "").strip(),
        "scope_intro": request.form.get("scope_intro", "").strip(),
        "exclusions": request.form.get("exclusions", "").strip(),
        "clarifications": request.form.get("clarifications", "").strip(),
        "schedule_text": request.form.get("schedule_text", "").strip(),
        "payment_terms": request.form.get("payment_terms", "").strip(),
        "warranty_text": request.form.get("warranty_text", "").strip(),
        "acceptance_text": request.form.get("acceptance_text", "").strip(),
        "show_detailed_pricing": _bool_field("show_detailed_pricing"),
        "show_section_totals": _bool_field("show_section_totals"),
        "show_allowances": _bool_field("show_allowances"),
        "show_tax": _bool_field("show_tax"),
        "valid_until": request.form.get("valid_until", "").strip(),
    }


def _proposal_form_from_snapshot(estimate, version, template, proposal_number):
    snapshot = build_proposal_snapshot(estimate, version, template)
    return {
        "proposal_number": proposal_number,
        "proposal_template_id": str(template.id),
        "title": snapshot["title"],
        "status": "Draft",
        "client_name": snapshot["client_name"] or "",
        "client_company": snapshot.get("client_company") or "",
        "client_address": snapshot.get("client_address") or "",
        "client_email": snapshot.get("client_email") or "",
        "client_phone": snapshot.get("client_phone") or "",
        "project_name": snapshot["project_name"] or "",
        "project_address": snapshot.get("project_address") or "",
        "intro_text": snapshot.get("intro_text") or "",
        "scope_intro": snapshot.get("scope_intro") or "",
        "exclusions": snapshot.get("exclusions") or "",
        "clarifications": snapshot.get("clarifications") or "",
        "schedule_text": snapshot.get("schedule_text") or "",
        "payment_terms": snapshot.get("payment_terms") or "",
        "warranty_text": snapshot.get("warranty_text") or "",
        "acceptance_text": snapshot.get("acceptance_text") or "",
        "show_detailed_pricing": snapshot.get("show_detailed_pricing", True),
        "show_section_totals": snapshot.get("show_section_totals", True),
        "show_allowances": snapshot.get("show_allowances", True),
        "show_tax": snapshot.get("show_tax", True),
        "valid_until": "",
        "subtotal": snapshot["subtotal"],
        "overhead_amount": snapshot["overhead_amount"],
        "profit_amount": snapshot["profit_amount"],
        "tax_amount": snapshot["tax_amount"],
        "total": snapshot["total"],
        "estimate_number": snapshot["estimate_number"],
        "estimate_version_number": snapshot["estimate_version_number"],
        "estimate_version_label": snapshot.get("estimate_version_label") or "",
    }


def _proposal_form_from_model(proposal):
    return {
        "proposal_number": proposal.proposal_number,
        "proposal_template_id": str(proposal.proposal_template_id),
        "title": proposal.title,
        "status": proposal.status,
        "client_name": proposal.client_name or "",
        "client_company": proposal.client_company or "",
        "client_address": proposal.client_address or "",
        "client_email": proposal.client_email or "",
        "client_phone": proposal.client_phone or "",
        "project_name": proposal.project_name or "",
        "project_address": proposal.project_address or "",
        "intro_text": proposal.intro_text or "",
        "scope_intro": proposal.scope_intro or "",
        "exclusions": proposal.exclusions or "",
        "clarifications": proposal.clarifications or "",
        "schedule_text": proposal.schedule_text or "",
        "payment_terms": proposal.payment_terms or "",
        "warranty_text": proposal.warranty_text or "",
        "acceptance_text": proposal.acceptance_text or "",
        "show_detailed_pricing": proposal.show_detailed_pricing,
        "show_section_totals": proposal.show_section_totals,
        "show_allowances": proposal.show_allowances,
        "show_tax": proposal.show_tax,
        "valid_until": proposal.valid_until.isoformat() if proposal.valid_until else "",
        "subtotal": proposal.subtotal,
        "overhead_amount": proposal.overhead_amount,
        "profit_amount": proposal.profit_amount,
        "tax_amount": proposal.tax_amount,
        "total": proposal.total,
        "estimate_number": proposal.estimate_number,
        "estimate_version_number": proposal.estimate_version_number,
        "estimate_version_label": proposal.estimate_version_label or "",
    }


def _stamp_office_copy(pdf_bytes):
    """Mark every page of a proposal that has not been sent to the client."""
    from io import BytesIO

    from pypdf import PdfReader, PdfWriter
    from reportlab.pdfgen import canvas

    reader = PdfReader(BytesIO(pdf_bytes))
    writer = PdfWriter()
    for page in reader.pages:
        width, height = float(page.mediabox.width), float(page.mediabox.height)
        mark = BytesIO()
        sheet = canvas.Canvas(mark, pagesize=(width, height))
        sheet.setFillColorRGB(0.75, 0.1, 0.1)
        sheet.setFont("Helvetica-Bold", 9)
        sheet.drawCentredString(width / 2, height - 14,
                                "OFFICE COPY — NOT ISSUED. Proposals go to clients only through CalibraytAI.")
        sheet.save()
        page.merge_page(PdfReader(BytesIO(mark.getvalue())).pages[0])
        writer.add_page(page)
    out = BytesIO()
    writer.write(out)
    return out.getvalue()


def _flow_context(proposal):
    """Send-to-client and acceptance state for the proposal page."""
    link_url = None
    if session.get("proposal_link_for") == proposal.id:
        link_url = session.get("proposal_link_url")
    return {
        "send_blockers": proposal_send_blockers(proposal),
        "client_link": current_link(proposal),
        "client_link_url": link_url,
        "acceptance": acceptance_for(proposal),
        "decline": decline_for(proposal),
        "acceptance_channels": OFFICE_ACCEPTANCE_CHANNELS,
        "signed_off": bool(proposal.estimate_version and proposal.estimate_version.signed_off_at),
    }


def _get_scoped_proposal_or_404(id):
    org_id = get_current_organization_id()
    proposal = Proposal.query.get_or_404(id)
    if proposal.estimate and proposal.estimate.project:
        if proposal.estimate.project.organization_id != org_id:
            abort(404)
    elif proposal.proposal_template and proposal.proposal_template.organization_id != org_id:
        abort(404)
    return proposal


@proposals_bp.route("/proposals/")
@proposals_bp.route("/proposals")
def list_proposals():
    org_id = get_current_organization_id()
    proposals = (
        Proposal.query.outerjoin(Estimate, Proposal.estimate_id == Estimate.id)
        .outerjoin(Project, Estimate.project_id == Project.id)
        .outerjoin(ProposalTemplate, Proposal.proposal_template_id == ProposalTemplate.id)
        .filter(
            db.or_(
                Project.organization_id == org_id,
                ProposalTemplate.organization_id == org_id,
            )
        )
        .order_by(Proposal.created_at.desc())
        .all()
    )
    return render_template("proposals/list.html", proposals=proposals)


@proposals_bp.route(
    "/estimates/<int:estimate_id>/versions/<int:version_id>/proposals/new",
    methods=["GET", "POST"],
)
def create_proposal_route(estimate_id, version_id):
    estimate, version = get_estimate_and_version(estimate_id, version_id)
    if estimate is None or version is None:
        abort(404)

    templates = get_active_templates()
    default_template = get_default_template()

    if not templates:
        flash("Create an active proposal template before creating a proposal.", "error")
        return redirect(url_for("proposal_templates.create_template"))

    if request.method == "POST":
        form = _proposal_form_from_request()
        template_id = request.form.get("proposal_template_id", type=int)
        template = ProposalTemplate.query.filter_by(
            id=template_id,
            is_active=True,
        ).first()

        try:
            if template is None:
                raise ProposalServiceError(
                    "Select an active proposal template."
                )
            if form["status"] in ISSUED_BY_FLOW_ONLY:
                raise ProposalServiceError(ISSUED_BY_FLOW_MESSAGE)
            proposal = create_proposal(
                estimate=estimate,
                version=version,
                template=template,
                title=form["title"],
                proposal_number=form["proposal_number"],
                status=form["status"] or "Draft",
                valid_until=_parse_date(form["valid_until"]),
                overrides={
                    "client_name": form["client_name"],
                    "client_company": form["client_company"] or None,
                    "client_address": form["client_address"] or None,
                    "client_email": form["client_email"] or None,
                    "client_phone": form["client_phone"] or None,
                    "project_name": form["project_name"],
                    "project_address": form["project_address"] or None,
                    "intro_text": form["intro_text"] or None,
                    "scope_intro": form["scope_intro"] or None,
                    "exclusions": form["exclusions"] or None,
                    "clarifications": form["clarifications"] or None,
                    "schedule_text": form["schedule_text"] or None,
                    "payment_terms": form["payment_terms"] or None,
                    "warranty_text": form["warranty_text"] or None,
                    "acceptance_text": form["acceptance_text"] or None,
                    "show_detailed_pricing": form["show_detailed_pricing"],
                    "show_section_totals": form["show_section_totals"],
                    "show_allowances": form["show_allowances"],
                    "show_tax": form["show_tax"],
                    "title": form["title"],
                },
            )
        except (ProposalServiceError, ValueError) as exc:
            flash(str(exc), "error")
            form["subtotal"] = version.subtotal
            form["overhead_amount"] = version.overhead_amount
            form["profit_amount"] = version.profit_amount
            form["tax_amount"] = version.tax_amount
            form["total"] = version.total
            form["estimate_number"] = estimate.estimate_number
            form["estimate_version_number"] = version.version_number
            form["estimate_version_label"] = version.version_label or ""
            return render_template(
                "proposals/form.html",
                form=form,
                estimate=estimate,
                version=version,
                templates=templates,
                statuses=OFFICE_STATUSES,
                proposal=None,
            )

        flash("Proposal created.", "success")
        return redirect(url_for("proposals.view_proposal", id=proposal.id))

    template = default_template or templates[0]
    form = _proposal_form_from_snapshot(
        estimate,
        version,
        template,
        suggest_next_proposal_number(
            organization_id=estimate.project.organization_id
        ),
    )
    return render_template(
        "proposals/form.html",
        form=form,
        estimate=estimate,
        version=version,
        templates=templates,
        statuses=OFFICE_STATUSES,
        proposal=None,
    )


def _preview_section_rows(proposal):
    rows = []
    for section in proposal.sections:
        line_items = [
            item
            for item in section.line_items
            if proposal.show_allowances or item.item_type != "Allowance"
        ]
        rows.append({"section": section, "line_items": line_items})
    return rows


@proposals_bp.route("/proposals/<int:id>")
def view_proposal(id):
    proposal = _get_scoped_proposal_or_404(id)
    editing_item_id = request.args.get("edit_item", type=int)
    item_edit_form = None
    immutable = is_proposal_immutable(proposal)

    if editing_item_id is not None and not immutable:
        item = (
            ProposalLineItem.query.join(ProposalSection)
            .filter(
                ProposalLineItem.id == editing_item_id,
                ProposalSection.proposal_id == proposal.id,
            )
            .first()
        )
        if item is not None:
            item_edit_form = {
                "description": item.description,
                "quantity": f"{item.quantity}",
                "unit": item.unit,
                "unit_cost": f"{item.unit_cost}",
                "markup_percent": f"{item.markup_percent:.2f}",
                "notes": item.notes or "",
            }
        else:
            editing_item_id = None
    else:
        editing_item_id = None

    return render_template(
        "proposals/detail.html",
        proposal=proposal,
        editing_item_id=editing_item_id,
        item_edit_form=item_edit_form,
        proposal_immutable=immutable,
        **_flow_context(proposal),
    )


@proposals_bp.route("/proposals/<int:id>/preview")
def preview_proposal(id):
    proposal = _get_scoped_proposal_or_404(id)
    try:
        brand = get_proposal_brand_render_context(proposal)
    except BrandProfileServiceError:
        abort(404)
    logo_url = None
    if brand.has_logo and brand_logo_filesystem_path(brand) is not None:
        logo_url = url_for("proposals.proposal_brand_logo", id=proposal.id)
    return render_template(
        "proposals/preview.html",
        proposal=proposal,
        template=proposal.proposal_template,
        brand=brand,
        logo_url=logo_url,
        section_rows=_preview_section_rows(proposal),
    )


@proposals_bp.route("/proposals/<int:id>/brand-logo")
def proposal_brand_logo(id):
    proposal = _get_scoped_proposal_or_404(id)
    try:
        brand = get_proposal_brand_render_context(proposal)
    except BrandProfileServiceError:
        abort(404)
    path = brand_logo_filesystem_path(brand)
    if path is None:
        abort(404)
    return send_file(
        path,
        mimetype=brand_logo_mimetype(brand),
        as_attachment=False,
        max_age=0,
    )


@proposals_bp.route("/proposals/<int:id>/pdf")
def download_proposal_pdf(id):
    proposal = _get_scoped_proposal_or_404(id)
    pdf_buffer = generate_proposal_pdf(proposal)
    from io import BytesIO as _BytesIO

    from app.models.construction_drawing import ATTACH_PROPOSAL
    from app.services.construction_drawings import append_drawings, current_attachment

    attachment = current_attachment(ATTACH_PROPOSAL, proposal.id)
    if attachment is not None:
        pdf_buffer = _BytesIO(append_drawings(pdf_buffer.getvalue(), attachment))
    if proposal.status not in ISSUED_BY_FLOW_ONLY:
        # Joel, 17 Oct 2026: only a proposal sent from CalibraytAI goes to a client.
        pdf_buffer = _BytesIO(_stamp_office_copy(pdf_buffer.getvalue()))
    filename = sanitize_pdf_filename(proposal)
    return send_file(
        pdf_buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename,
    )


@proposals_bp.route(
    "/proposals/<int:id>/sections/<int:section_id>/items/<int:item_id>/edit",
    methods=["POST"],
)
def edit_proposal_line_item(id, section_id, item_id):
    proposal = _get_scoped_proposal_or_404(id)
    section = ProposalSection.query.filter_by(
        id=section_id,
        proposal_id=proposal.id,
    ).first_or_404()
    item = ProposalLineItem.query.filter_by(
        id=item_id,
        proposal_section_id=section.id,
    ).first_or_404()

    form = {
        "description": request.form.get("description", "").strip(),
        "quantity": request.form.get("quantity", "").strip(),
        "unit": request.form.get("unit", "").strip(),
        "unit_cost": request.form.get("unit_cost", "").strip(),
        "markup_percent": request.form.get("markup_percent", "").strip(),
        "notes": request.form.get("notes", "").strip(),
    }

    content_before = proposal_content_sha256(proposal)
    try:
        update_proposal_line_item(
            item,
            description=form["description"],
            quantity=form["quantity"],
            unit=form["unit"],
            unit_cost=form["unit_cost"],
            markup_percent=form["markup_percent"],
            notes=form["notes"],
        )
    except ProposalServiceError as exc:
        flash(str(exc), "error")
        return render_template(
            "proposals/detail.html",
            proposal=proposal,
            editing_item_id=item.id if not is_proposal_immutable(proposal) else None,
            item_edit_form=form if not is_proposal_immutable(proposal) else None,
            proposal_immutable=is_proposal_immutable(proposal),
            **_flow_context(proposal),
        )

    if withdraw_link_after_change(proposal, content_before=content_before):
        flash("Line item updated. The client link was withdrawn because the proposal changed. "
              "Send it to the client again.", "success")
    else:
        flash("Proposal line item updated.", "success")
    return redirect(url_for("proposals.view_proposal", id=proposal.id))


@proposals_bp.route("/proposals/<int:id>/edit", methods=["GET", "POST"])
def edit_proposal(id):
    proposal = _get_scoped_proposal_or_404(id)
    if is_proposal_immutable(proposal):
        flash(
            "This proposal is Accepted and is locked. It cannot be edited.",
            "error",
        )
        return redirect(url_for("proposals.view_proposal", id=proposal.id))

    templates = get_active_templates()
    if proposal.proposal_template not in templates:
        templates = list(templates) + [proposal.proposal_template]

    if request.method == "POST":
        form = _proposal_form_from_request()
        try:
            if form["status"] in ISSUED_BY_FLOW_ONLY and form["status"] != proposal.status:
                raise ProposalServiceError(ISSUED_BY_FLOW_MESSAGE)
            content_before = proposal_content_sha256(proposal)
            update_proposal(
                proposal,
                proposal_number=form["proposal_number"],
                proposal_template_id=request.form.get(
                    "proposal_template_id",
                    type=int,
                ),
                title=form["title"],
                status=form["status"],
                valid_until=_parse_date(form["valid_until"]),
                client_name=form["client_name"],
                client_company=form["client_company"],
                client_address=form["client_address"],
                client_email=form["client_email"],
                client_phone=form["client_phone"],
                project_name=form["project_name"],
                project_address=form["project_address"],
                intro_text=form["intro_text"],
                scope_intro=form["scope_intro"],
                exclusions=form["exclusions"],
                clarifications=form["clarifications"],
                schedule_text=form["schedule_text"],
                payment_terms=form["payment_terms"],
                warranty_text=form["warranty_text"],
                acceptance_text=form["acceptance_text"],
                show_detailed_pricing=form["show_detailed_pricing"],
                show_section_totals=form["show_section_totals"],
                show_allowances=form["show_allowances"],
                show_tax=form["show_tax"],
            )
        except (ProposalServiceError, ValueError) as exc:
            flash(str(exc), "error")
            form.update(
                {
                    "subtotal": proposal.subtotal,
                    "overhead_amount": proposal.overhead_amount,
                    "profit_amount": proposal.profit_amount,
                    "tax_amount": proposal.tax_amount,
                    "total": proposal.total,
                    "estimate_number": proposal.estimate_number,
                    "estimate_version_number": proposal.estimate_version_number,
                    "estimate_version_label": proposal.estimate_version_label or "",
                }
            )
            return render_template(
                "proposals/form.html",
                form=form,
                estimate=proposal.estimate,
                version=proposal.estimate_version,
                templates=templates,
                statuses=OFFICE_STATUSES,
                proposal=proposal,
            )

        if withdraw_link_after_change(proposal, content_before=content_before):
            flash("Proposal updated. The client link was withdrawn because the proposal changed. "
                  "Send it to the client again.", "success")
        else:
            flash("Proposal updated.", "success")
        return redirect(url_for("proposals.view_proposal", id=proposal.id))

    form = _proposal_form_from_model(proposal)
    return render_template(
        "proposals/form.html",
        form=form,
        estimate=proposal.estimate,
        version=proposal.estimate_version,
        templates=templates,
        statuses=OFFICE_STATUSES,
        proposal=proposal,
    )


@proposals_bp.route("/proposals/<int:id>/status", methods=["POST"])
def update_status(id):
    proposal = _get_scoped_proposal_or_404(id)
    status = request.form.get("status", "").strip()
    try:
        if status in ISSUED_BY_FLOW_ONLY and status != proposal.status and not is_proposal_immutable(proposal):
            raise ProposalServiceError(ISSUED_BY_FLOW_MESSAGE)
        update_proposal_status(proposal, status)
    except ProposalServiceError as exc:
        flash(str(exc), "error")
    else:
        flash(f'Proposal status set to "{proposal.status}".', "success")
    return redirect(url_for("proposals.view_proposal", id=proposal.id))


@proposals_bp.route("/estimates/<int:estimate_id>/versions/<int:version_id>/sign-off", methods=["POST"])
def sign_off_estimate_route(estimate_id, version_id):
    from flask_login import current_user

    estimate, version = get_estimate_and_version(estimate_id, version_id)
    if estimate is None or version is None:
        abort(404)
    try:
        proposal = sign_off_estimate(version, user=current_user)
    except ProposalServiceError as exc:
        flash(str(exc), "error")
        return redirect(url_for("estimates.view_version", id=estimate.id, version_id=version.id))
    flash("Estimate signed off and locked. Its proposal is ready: review it, then send it to the client.", "success")
    return redirect(url_for("proposals.view_proposal", id=proposal.id))


@proposals_bp.route("/proposals/<int:id>/send-to-client", methods=["POST"])
def send_to_client(id):
    from flask_login import current_user

    proposal = _get_scoped_proposal_or_404(id)
    try:
        days = int(request.form.get("valid_days") or 30)
    except ValueError:
        days = 30
    try:
        sent = send_proposal_to_client(
            proposal,
            user=current_user,
            client_name=request.form.get("client_name", ""),
            client_email=request.form.get("client_email", ""),
            days=days,
        )
    except ProposalServiceError as exc:
        flash(str(exc), "error")
        return redirect(url_for("proposals.view_proposal", id=proposal.id))
    from app.services.signing_mail import public_signing_url

    session["proposal_link_for"] = proposal.id
    session["proposal_link_url"] = public_signing_url(sent.path)
    flash(f"Proposal sent to {sent.link.sent_to_name} ({sent.link.sent_to_email}).", "success")
    return redirect(url_for("proposals.view_proposal", id=proposal.id) + "#client-acceptance")


@proposals_bp.route("/proposals/<int:id>/record-acceptance", methods=["POST"])
def record_acceptance(id):
    from flask_login import current_user

    proposal = _get_scoped_proposal_or_404(id)
    try:
        record_office_acceptance(
            proposal,
            user=current_user,
            channel=request.form.get("channel", ""),
            client_name=request.form.get("client_name", ""),
            note=request.form.get("note", ""),
        )
    except ProposalServiceError as exc:
        flash(str(exc), "error")
    else:
        flash("Acceptance recorded. The contract was generated and is ready to send.", "success")
    return redirect(url_for("proposals.view_proposal", id=proposal.id) + "#client-acceptance")
