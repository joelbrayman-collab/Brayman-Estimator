from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.models.proposal import ProposalTemplate
from app.services.proposals import (
    ProposalServiceError,
    create_proposal_template,
    set_default_template,
    toggle_template_active,
    update_proposal_template,
)

proposal_templates_bp = Blueprint(
    "proposal_templates",
    __name__,
    url_prefix="/proposal-templates",
)


def _bool_field(name, default=False):
    if request.method != "POST":
        return default
    return request.form.get(name) == "on" or request.form.get(name) == "1"


def _template_form_values(template=None):
    if request.method == "POST":
        return {
            "name": request.form.get("name", "").strip(),
            "description": request.form.get("description", "").strip(),
            "company_name": request.form.get("company_name", "").strip(),
            "company_address": request.form.get("company_address", "").strip(),
            "company_phone": request.form.get("company_phone", "").strip(),
            "company_email": request.form.get("company_email", "").strip(),
            "company_website": request.form.get("company_website", "").strip(),
            "logo_path": request.form.get("logo_path", "").strip(),
            "primary_color": request.form.get("primary_color", "").strip(),
            "accent_color": request.form.get("accent_color", "").strip(),
            "default_intro_text": request.form.get("default_intro_text", "").strip(),
            "default_scope_intro": request.form.get("default_scope_intro", "").strip(),
            "default_exclusions": request.form.get("default_exclusions", "").strip(),
            "default_clarifications": request.form.get(
                "default_clarifications", ""
            ).strip(),
            "default_schedule_text": request.form.get(
                "default_schedule_text", ""
            ).strip(),
            "default_payment_terms": request.form.get(
                "default_payment_terms", ""
            ).strip(),
            "default_warranty_text": request.form.get(
                "default_warranty_text", ""
            ).strip(),
            "default_acceptance_text": request.form.get(
                "default_acceptance_text", ""
            ).strip(),
            "show_detailed_pricing": _bool_field("show_detailed_pricing"),
            "show_section_totals": _bool_field("show_section_totals"),
            "show_allowances": _bool_field("show_allowances"),
            "show_tax": _bool_field("show_tax"),
            "is_default": _bool_field("is_default"),
            "is_active": _bool_field("is_active", default=True),
        }

    if template is None:
        return {
            "name": "",
            "description": "",
            "company_name": "Brayman Construction Co.",
            "company_address": "",
            "company_phone": "",
            "company_email": "",
            "company_website": "",
            "logo_path": "",
            "primary_color": "#c79a2b",
            "accent_color": "#181818",
            "default_intro_text": "",
            "default_scope_intro": "",
            "default_exclusions": "",
            "default_clarifications": "",
            "default_schedule_text": "",
            "default_payment_terms": "",
            "default_warranty_text": "",
            "default_acceptance_text": "",
            "show_detailed_pricing": True,
            "show_section_totals": True,
            "show_allowances": True,
            "show_tax": True,
            "is_default": False,
            "is_active": True,
        }

    return {
        "name": template.name or "",
        "description": template.description or "",
        "company_name": template.company_name or "",
        "company_address": template.company_address or "",
        "company_phone": template.company_phone or "",
        "company_email": template.company_email or "",
        "company_website": template.company_website or "",
        "logo_path": template.logo_path or "",
        "primary_color": template.primary_color or "",
        "accent_color": template.accent_color or "",
        "default_intro_text": template.default_intro_text or "",
        "default_scope_intro": template.default_scope_intro or "",
        "default_exclusions": template.default_exclusions or "",
        "default_clarifications": template.default_clarifications or "",
        "default_schedule_text": template.default_schedule_text or "",
        "default_payment_terms": template.default_payment_terms or "",
        "default_warranty_text": template.default_warranty_text or "",
        "default_acceptance_text": template.default_acceptance_text or "",
        "show_detailed_pricing": template.show_detailed_pricing,
        "show_section_totals": template.show_section_totals,
        "show_allowances": template.show_allowances,
        "show_tax": template.show_tax,
        "is_default": template.is_default,
        "is_active": template.is_active,
    }


@proposal_templates_bp.route("/")
@proposal_templates_bp.route("")
def list_templates():
    templates = ProposalTemplate.query.order_by(ProposalTemplate.name.asc()).all()
    return render_template(
        "proposal_templates/list.html",
        templates=templates,
    )


@proposal_templates_bp.route("/new", methods=["GET", "POST"])
def create_template():
    form = _template_form_values()

    if request.method == "POST":
        try:
            create_proposal_template(**form)
        except ProposalServiceError as exc:
            flash(str(exc), "error")
            return render_template(
                "proposal_templates/form.html",
                form=form,
                template=None,
            )

        flash("Proposal template created.", "success")
        return redirect(url_for("proposal_templates.list_templates"))

    return render_template(
        "proposal_templates/form.html",
        form=form,
        template=None,
    )


@proposal_templates_bp.route("/<int:id>/edit", methods=["GET", "POST"])
def edit_template(id):
    template = ProposalTemplate.query.get_or_404(id)
    form = _template_form_values(template)

    if request.method == "POST":
        try:
            update_proposal_template(template, **form)
        except ProposalServiceError as exc:
            flash(str(exc), "error")
            return render_template(
                "proposal_templates/form.html",
                form=form,
                template=template,
            )

        flash("Proposal template updated.", "success")
        return redirect(url_for("proposal_templates.list_templates"))

    return render_template(
        "proposal_templates/form.html",
        form=form,
        template=template,
    )


@proposal_templates_bp.route("/<int:id>/set-default", methods=["POST"])
def set_default(id):
    template = ProposalTemplate.query.get_or_404(id)
    try:
        set_default_template(template)
    except ProposalServiceError as exc:
        flash(str(exc), "error")
    else:
        flash(f'"{template.name}" is now the default template.', "success")
    return redirect(url_for("proposal_templates.list_templates"))


@proposal_templates_bp.route("/<int:id>/toggle-active", methods=["POST"])
def toggle_active(id):
    template = ProposalTemplate.query.get_or_404(id)
    try:
        toggle_template_active(template)
    except ProposalServiceError as exc:
        flash(str(exc), "error")
    else:
        state = "activated" if template.is_active else "deactivated"
        flash(f'Template "{template.name}" {state}.', "success")
    return redirect(url_for("proposal_templates.list_templates"))
