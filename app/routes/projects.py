from flask import Blueprint, abort, flash, redirect, render_template, request, send_file, url_for
from flask_login import current_user

from app import db
from app.models import Client, Project
from app.models.permit_intelligence import ADVISORY_AUTHORITY_LANGUAGE
from app.models.project import (
    DEFAULT_PERMIT_CONTEXT_CLASS,
    OPERATING_STATE_ACTIVE,
    OPERATING_STATE_CLOSED,
    PERMIT_CONTEXT_CLASSES,
)
from app.presentation import contractor_copy
from app.services.commercial_context import (
    DELIVERY_MODELS,
    ESTIMATE_STAGES,
    EXECUTION_RISKS,
    PRICING_POSTURES,
    PROJECT_TYPES,
    SCHEDULE_CONDITIONS,
    SITE_CONDITIONS,
    CommercialContextValidationError,
    create_initial_commercial_context,
    update_commercial_context,
)
from app.services.auth import current_actor_display_name, form_actor
from app.services.instance_authority import require_instance_owner_or_system_administrator
from app.services.organizations import get_current_organization_id
from app.services.project_operating_lifecycle import (
    ProjectLifecycleError,
    ProjectLifecycleUnauthorizedError,
    close_project,
    hub_operating_template_vars,
    reopen_project,
)
from app.services.project_final_walkthrough import hub_walkthrough_template_vars
from app.services.project_punch_list import hub_punch_list_template_vars
from app.services.permit_foundation import (
    PermitFoundationError,
    establish_project_location_and_profile,
    location_payload_from_form,
)
from app.services.permit_intelligence import (
    PermitIntelligenceError,
    assemble_permit_intelligence_state,
    current_analysis,
    record_project_permit_fact,
    run_permit_analysis as execute_permit_analysis,
)
from app.services.permit_report_pdf import generate_permit_report_pdf
from app.services.project_hub import assemble_project_hub
from app.services.shared_api import list_closed_projects, list_current_operating_projects

projects_bp = Blueprint("projects", __name__, url_prefix="/projects")


def _context_options():
    return {
        "project_types": PROJECT_TYPES,
        "pricing_postures": PRICING_POSTURES,
        "execution_risks": EXECUTION_RISKS,
        "schedule_conditions": SCHEDULE_CONDITIONS,
        "site_conditions": SITE_CONDITIONS,
        "estimate_stages": ESTIMATE_STAGES,
        "delivery_models": DELIVERY_MODELS,
        "permit_context_classes": PERMIT_CONTEXT_CLASSES,
        "default_permit_context_class": DEFAULT_PERMIT_CONTEXT_CLASS,
    }


@projects_bp.route("/")
def list_projects():
    org_id = get_current_organization_id()
    view = (request.args.get("view") or "current").strip().lower()
    if view not in ("current", "closed"):
        view = "current"
    if view == "closed":
        projects = list_closed_projects(org_id)
        empty_title = contractor_copy.PROJECT_LIST_CLOSED_EMPTY
        empty_help = "Closed Projects stay available from this list and from the Project Hub."
    else:
        projects = list_current_operating_projects(org_id)
        empty_title = contractor_copy.PROJECT_LIST_CURRENT_EMPTY
        empty_help = "Create a client first, then create the first construction project."
    return render_template(
        "projects/list.html",
        projects=projects,
        list_view=view,
        empty_title=empty_title,
        empty_help=empty_help,
    )


@projects_bp.route("/<int:id>")
def view_project(id):
    org_id = get_current_organization_id()
    project = Project.query.filter_by(id=id, organization_id=org_id).first_or_404()
    hub = assemble_project_hub(project, org_id)
    return render_template(
        "projects/detail.html",
        project=project,
        hub=hub,
        estimates=hub["estimates"],
        proposals=hub["proposals"],
        change_orders=hub["change_orders"],
        **hub_operating_template_vars(project, org_id, current_user),
        **hub_punch_list_template_vars(project, org_id, current_user),
        **hub_walkthrough_template_vars(project, org_id, current_user),
    )


def _lifecycle_gate():
    gate = require_instance_owner_or_system_administrator()
    if gate is not None:
        return gate
    return None


def _scoped_project(project_id):
    org_id = get_current_organization_id()
    return Project.query.filter_by(id=project_id, organization_id=org_id).first_or_404()


@projects_bp.route("/<int:id>/close", methods=["GET", "POST"], endpoint="close_project")
def close_project_action(id):
    denied = _lifecycle_gate()
    if denied is not None:
        return denied
    project = _scoped_project(id)
    if request.method == "GET":
        if project.operating_state != OPERATING_STATE_ACTIVE:
            flash(contractor_copy.PROJECT_ALREADY_CLOSED, "error")
            return redirect(url_for("projects.view_project", id=project.id))
        return render_template(
            "projects/close_confirm.html",
            project=project,
        )
    try:
        close_project(project, current_user)
    except ProjectLifecycleUnauthorizedError:
        abort(403)
    except ProjectLifecycleError as exc:
        flash(str(exc), "error")
        return redirect(url_for("projects.view_project", id=project.id))
    flash(contractor_copy.PROJECT_CLOSED_FLASH, "success")
    return redirect(url_for("projects.view_project", id=project.id))


@projects_bp.route("/<int:id>/reopen", methods=["GET", "POST"], endpoint="reopen_project")
def reopen_project_action(id):
    denied = _lifecycle_gate()
    if denied is not None:
        return denied
    project = _scoped_project(id)
    if request.method == "GET":
        if project.operating_state != OPERATING_STATE_CLOSED:
            flash(contractor_copy.PROJECT_ALREADY_CURRENT, "error")
            return redirect(url_for("projects.view_project", id=project.id))
        return render_template(
            "projects/reopen_confirm.html",
            project=project,
        )
    try:
        reopen_project(project, current_user)
    except ProjectLifecycleUnauthorizedError:
        abort(403)
    except ProjectLifecycleError as exc:
        flash(str(exc), "error")
        return redirect(url_for("projects.view_project", id=project.id))
    flash(contractor_copy.PROJECT_REOPENED_FLASH, "success")
    return redirect(url_for("projects.view_project", id=project.id))


@projects_bp.route("/new", methods=["GET", "POST"])
def create_project():
    org_id = get_current_organization_id()
    clients = Client.query.filter_by(organization_id=org_id).order_by(Client.name.asc()).all()
    options = _context_options()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        client_id = request.form.get("client_id", type=int)

        if not name or not client_id:
            flash("Project name and client are required.", "error")
            return render_template("projects/form.html", clients=clients, **options)

        # Verify client belongs to current organization
        client = Client.query.filter_by(id=client_id, organization_id=org_id).first()
        if not client:
            flash("Invalid client selection.", "error")
            return render_template("projects/form.html", clients=clients, **options)

        context_data = {
            "project_type": request.form.get("project_type", "").strip(),
            "pricing_posture": request.form.get("pricing_posture", "").strip(),
            "execution_risk": request.form.get("execution_risk", "").strip(),
            "schedule_condition": request.form.get("schedule_condition", "").strip(),
            "site_condition": request.form.get("site_condition", "").strip(),
            "estimate_stage": request.form.get("estimate_stage", "").strip(),
            "delivery_model": request.form.get("delivery_model", "").strip(),
            "justification_reason": request.form.get("justification_reason", "").strip(),
            "change_summary": "Initial project commercial decision gate",
        }

        try:
            project = Project(
                organization_id=org_id,
                name=name,
                project_number=request.form.get("project_number", "").strip() or None,
                address=request.form.get("address", "").strip(),
                status=request.form.get("status", "Lead"),
                description=request.form.get("description", "").strip(),
                client_id=client_id,
            )
            db.session.add(project)
            db.session.flush()

            created_by = form_actor("created_by")
            create_initial_commercial_context(
                project_id=project.id,
                data=context_data,
                created_by=created_by,
                organization_id=org_id,
                commit=False,
            )
            establish_project_location_and_profile(
                project.id,
                location_payload_from_form(request.form),
                request.form.get("permit_context_class"),
                organization_id=org_id,
                generated_by=created_by,
                commit=False,
            )

            db.session.commit()
            flash("Project created successfully with commercial decision context.", "success")
            return redirect(url_for("projects.view_project", id=project.id))

        except (CommercialContextValidationError, PermitFoundationError) as e:
            db.session.rollback()
            flash(str(e), "error")
            return render_template("projects/form.html", clients=clients, **options)
        except Exception as e:
            db.session.rollback()
            flash(f"Error creating project: {str(e)}", "error")
            return render_template("projects/form.html", clients=clients, **options)

    return render_template("projects/form.html", clients=clients, **options)


@projects_bp.route("/<int:id>/commercial-context/edit", methods=["GET", "POST"])
def edit_commercial_context(id):
    org_id = get_current_organization_id()
    project = Project.query.filter_by(id=id, organization_id=org_id).first_or_404()
    options = _context_options()
    current_context = project.current_commercial_context

    if request.method == "POST":
        context_data = {
            "project_type": request.form.get("project_type", "").strip(),
            "pricing_posture": request.form.get("pricing_posture", "").strip(),
            "execution_risk": request.form.get("execution_risk", "").strip(),
            "schedule_condition": request.form.get("schedule_condition", "").strip(),
            "site_condition": request.form.get("site_condition", "").strip(),
            "estimate_stage": request.form.get("estimate_stage", "").strip(),
            "delivery_model": request.form.get("delivery_model", "").strip(),
            "justification_reason": request.form.get("justification_reason", "").strip(),
            "change_summary": request.form.get("change_summary", "").strip() or "Updated commercial decision context",
        }

        try:
            update_commercial_context(
                project_id=project.id,
                data=context_data,
                updated_by=request.form.get("updated_by", "Estimator").strip() or "Estimator",
                change_summary=context_data["change_summary"],
                organization_id=org_id,
                commit=True,
            )
            flash("Project commercial decision context updated to new version.", "success")
            return redirect(url_for("projects.view_project", id=project.id))
        except CommercialContextValidationError as e:
            flash(str(e), "error")
            return render_template(
                "projects/edit_context.html",
                project=project,
                current_context=current_context,
                **options,
            )

    return render_template(
        "projects/edit_context.html",
        project=project,
        current_context=current_context,
        **options,
    )


@projects_bp.route("/<int:id>/location/edit", methods=["GET", "POST"])
def edit_project_location(id):
    org_id = get_current_organization_id()
    project = Project.query.filter_by(id=id, organization_id=org_id).first_or_404()
    options = _context_options()
    location = project.location
    profile = project.current_permit_profile

    if request.method == "POST":
        try:
            establish_project_location_and_profile(
                project.id,
                location_payload_from_form(request.form),
                request.form.get("permit_context_class"),
                organization_id=org_id,
                generated_by=request.form.get("updated_by", "Estimator").strip()
                or "Estimator",
                commit=True,
            )
            flash(
                "Structured location and preliminary permit profile updated.",
                "success",
            )
            return redirect(url_for("projects.view_project", id=project.id))
        except PermitFoundationError as e:
            flash(str(e), "error")
            return render_template(
                "projects/edit_location.html",
                project=project,
                location=location,
                profile=profile,
                **options,
            )

    return render_template(
        "projects/edit_location.html",
        project=project,
        location=location,
        profile=profile,
        **options,
    )


@projects_bp.route("/<int:id>/permit-report", methods=["GET"])
def view_permit_report(id):
    org_id = get_current_organization_id()
    project = Project.query.filter_by(id=id, organization_id=org_id).first_or_404()
    analysis = current_analysis(project)
    return render_template(
        "projects/permit_report.html",
        project=project,
        analysis=analysis,
        pi=assemble_permit_intelligence_state(project),
        advisory=ADVISORY_AUTHORITY_LANGUAGE,
    )


@projects_bp.route("/<int:id>/permit-report/run", methods=["POST"])
def run_permit_analysis(id):
    org_id = get_current_organization_id()
    project = Project.query.filter_by(id=id, organization_id=org_id).first_or_404()
    try:
        execute_permit_analysis(
            project.id,
            organization_id=org_id,
            generated_by=current_actor_display_name(),
            commit=True,
        )
        flash("Permit analysis snapshot created. Prior versions were not rewritten.", "success")
    except PermitIntelligenceError as exc:
        flash(str(exc), "error")
    return redirect(url_for("projects.view_permit_report", id=project.id))


@projects_bp.route("/<int:id>/permit-facts", methods=["POST"])
def add_permit_fact(id):
    org_id = get_current_organization_id()
    project = Project.query.filter_by(id=id, organization_id=org_id).first_or_404()
    raw_numeric = (request.form.get("value_numeric") or "").strip()
    value_numeric = None
    if raw_numeric:
        try:
            value_numeric = float(raw_numeric)
        except ValueError:
            flash("Numeric value must be a number.", "error")
            return redirect(url_for("projects.view_permit_report", id=project.id))
    try:
        record_project_permit_fact(
            project.id,
            organization_id=org_id,
            fact_type=(request.form.get("fact_type") or "").strip(),
            value_text=(request.form.get("value_text") or "").strip() or None,
            value_numeric=value_numeric,
            unit=(request.form.get("unit") or "").strip() or None,
            source_type=(request.form.get("source_type") or "MANUAL_REVIEWED").strip(),
            source_label=(request.form.get("source_label") or "").strip() or None,
            page_sheet_citation=(request.form.get("page_sheet_citation") or "").strip()
            or None,
            review_status=(request.form.get("review_status") or "REVIEWED").strip(),
            reviewed_by=current_actor_display_name(),
            commit=True,
        )
        flash("Reviewed project fact recorded.", "success")
    except PermitIntelligenceError as exc:
        flash(str(exc), "error")
    return redirect(url_for("projects.view_permit_report", id=project.id))


@projects_bp.route("/<int:id>/permit-report.pdf", methods=["GET"])
def download_permit_report_pdf(id):
    org_id = get_current_organization_id()
    project = Project.query.filter_by(id=id, organization_id=org_id).first_or_404()
    analysis = current_analysis(project)
    if analysis is None:
        flash("No Permit Report snapshot exists yet.", "error")
        return redirect(url_for("projects.view_permit_report", id=project.id))
    pdf = generate_permit_report_pdf(analysis)
    return send_file(
        pdf,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"permit-approvals-report-v{analysis.version_number}.pdf",
    )
