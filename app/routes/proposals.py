from datetime import datetime

from flask import Blueprint, abort, flash, redirect, render_template, request, send_file, url_for

from app.models.proposal import (
    PROPOSAL_STATUSES,
    Proposal,
    ProposalLineItem,
    ProposalSection,
    ProposalTemplate,
)
from app.services.proposal_pdf import (
    generate_proposal_pdf,
    resolve_preview_logo_url,
    sanitize_pdf_filename,
)
from app.services.proposals import (
    ProposalServiceError,
    build_proposal_snapshot,
    create_proposal,
    get_active_templates,
    get_default_template,
    get_estimate_and_version,
    suggest_next_proposal_number,
    update_proposal,
    update_proposal_line_item,
    update_proposal_status,
)

proposals_bp = Blueprint("proposals", __name__)


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


@proposals_bp.route("/proposals/")
@proposals_bp.route("/proposals")
def list_proposals():
    proposals = Proposal.query.order_by(Proposal.created_at.desc()).all()
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
                statuses=PROPOSAL_STATUSES,
                proposal=None,
            )

        flash("Proposal created.", "success")
        return redirect(url_for("proposals.view_proposal", id=proposal.id))

    template = default_template or templates[0]
    form = _proposal_form_from_snapshot(
        estimate,
        version,
        template,
        suggest_next_proposal_number(),
    )
    return render_template(
        "proposals/form.html",
        form=form,
        estimate=estimate,
        version=version,
        templates=templates,
        statuses=PROPOSAL_STATUSES,
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
    proposal = Proposal.query.get_or_404(id)
    editing_item_id = request.args.get("edit_item", type=int)
    item_edit_form = None

    if editing_item_id is not None:
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

    return render_template(
        "proposals/detail.html",
        proposal=proposal,
        editing_item_id=editing_item_id,
        item_edit_form=item_edit_form,
    )


@proposals_bp.route("/proposals/<int:id>/preview")
def preview_proposal(id):
    proposal = Proposal.query.get_or_404(id)
    template = proposal.proposal_template
    return render_template(
        "proposals/preview.html",
        proposal=proposal,
        template=template,
        logo_url=resolve_preview_logo_url(
            template.logo_path if template else None,
            url_for,
        ),
        section_rows=_preview_section_rows(proposal),
    )


@proposals_bp.route("/proposals/<int:id>/pdf")
def download_proposal_pdf(id):
    proposal = Proposal.query.get_or_404(id)
    pdf_buffer = generate_proposal_pdf(proposal)
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
    proposal = Proposal.query.get_or_404(id)
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
            editing_item_id=item.id,
            item_edit_form=form,
        )

    flash("Proposal line item updated.", "success")
    return redirect(url_for("proposals.view_proposal", id=proposal.id))


@proposals_bp.route("/proposals/<int:id>/edit", methods=["GET", "POST"])
def edit_proposal(id):
    proposal = Proposal.query.get_or_404(id)
    templates = get_active_templates()
    if proposal.proposal_template not in templates:
        templates = list(templates) + [proposal.proposal_template]

    if request.method == "POST":
        form = _proposal_form_from_request()
        try:
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
                statuses=PROPOSAL_STATUSES,
                proposal=proposal,
            )

        flash("Proposal updated.", "success")
        return redirect(url_for("proposals.view_proposal", id=proposal.id))

    form = _proposal_form_from_model(proposal)
    return render_template(
        "proposals/form.html",
        form=form,
        estimate=proposal.estimate,
        version=proposal.estimate_version,
        templates=templates,
        statuses=PROPOSAL_STATUSES,
        proposal=proposal,
    )


@proposals_bp.route("/proposals/<int:id>/status", methods=["POST"])
def update_status(id):
    proposal = Proposal.query.get_or_404(id)
    status = request.form.get("status", "").strip()
    try:
        update_proposal_status(proposal, status)
    except ProposalServiceError as exc:
        flash(str(exc), "error")
    else:
        flash(f'Proposal status set to "{proposal.status}".', "success")
    return redirect(url_for("proposals.view_proposal", id=proposal.id))
