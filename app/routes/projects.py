from flask import Blueprint, flash, redirect, render_template, request, url_for

from app import db
from app.models import Client, Project
from app.models.project import DEFAULT_PERMIT_CONTEXT_CLASS, PERMIT_CONTEXT_CLASSES
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
from app.services.organizations import get_current_organization_id
from app.services.permit_foundation import (
    PermitFoundationError,
    establish_project_location_and_profile,
    location_payload_from_form,
)
from app.services.project_hub import assemble_project_hub

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
    projects = Project.query.filter_by(organization_id=org_id).order_by(Project.created_at.desc()).all()
    return render_template("projects/list.html", projects=projects)


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
    )


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

            created_by = request.form.get("created_by", "Estimator").strip() or "Estimator"
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
