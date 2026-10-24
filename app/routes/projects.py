from io import BytesIO

from flask import Blueprint, abort, flash, redirect, render_template, request, send_file, url_for
from flask_login import current_user

from app.services.local_time import local_today
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
from app.presentation.workflow_documents import workflow_document_groups
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
from app.services.construction_model_entry import current_revision_for_project
from app.services.organizations import get_current_organization_id
from app.services.project_operating_lifecycle import (
    ProjectLifecycleError,
    ProjectLifecycleUnauthorizedError,
    close_project,
    hub_operating_template_vars,
    reopen_project,
)
from app.services.project_final_walkthrough import hub_walkthrough_template_vars
from app.services.project_punch_list import (
    hub_punch_list_template_vars,
    list_open_punch_list_items,
)
from app.services.project_client import ProjectClientError, correct_project_client
from app.services.project_drawing_requirement import (
    DRAWING_STATE_PRESENT,
    DRAWING_STATE_REQUIRED_MISSING,
    ProjectDrawingRequirementError,
    derive_drawing_state,
    set_project_drawing_requirement,
)
from app.services.project_work_package import project_plans
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
    if view == "closed":
        current_count = len(list_current_operating_projects(org_id))
        closed_count = len(projects)
    else:
        current_count = len(projects)
        closed_count = len(list_closed_projects(org_id))
    return render_template(
        "projects/list.html",
        projects=projects,
        list_view=view,
        current_count=current_count,
        closed_count=closed_count,
        empty_title=empty_title,
        empty_help=empty_help,
    )


@projects_bp.before_app_request
def _shop_and_company_work_is_not_a_job():
    """Every /projects/<id>/... page (hub, estimates, proposals, contract, change orders, supplier requests…)
    treats the internal Shop / Company Work record as what it is: not a customer job. Its office page is
    /time/company; crew use Shop / Company Work on Field (Joel, 22 Oct 2026)."""
    rule = getattr(request.url_rule, "rule", "") or ""
    if not rule.startswith("/projects/<"):
        return None
    args = request.view_args or {}
    pid = args.get("id", args.get("project_id"))
    if pid is None:
        return None
    from app.services.time_entry import company_time_project_number

    try:
        org_id = get_current_organization_id()
    except Exception:  # noqa: BLE001 - no organization: the page's own checks answer
        return None
    if Project.query.filter_by(id=pid, organization_id=org_id,
                               project_number=company_time_project_number(org_id)).first() is not None:
        return redirect(url_for("payroll_time.company_work"))
    return None


@projects_bp.route("/<int:id>")
def view_project(id):
    org_id = get_current_organization_id()
    project = Project.query.filter_by(id=id, organization_id=org_id).first_or_404()
    from app.services.project_stage import sync_started_work_stage

    sync_started_work_stage(project)  # the first scheduled work has started: the job is in progress
    hub = assemble_project_hub(project, org_id)
    drawing_state = derive_drawing_state(
        project.drawing_requirement,
        bool(project_plans(org_id, project.id)),
    )
    return render_template(
        "projects/detail.html",
        project=project,
        hub=hub,
        drawing_state=drawing_state,
        estimates=hub["estimates"],
        proposals=hub["proposals"],
        change_orders=hub["change_orders"],
        breadcrumb_items=[
            {"label": "Projects", "url": url_for("projects.list_projects")},
            {"label": project.name, "url": None},
        ],
        construction_revision=current_revision_for_project(
            organization_id=org_id,
            project_id=project.id,
        ),
        **hub_operating_template_vars(project, org_id, current_user),
        **hub_punch_list_template_vars(project, org_id, current_user),
        **hub_walkthrough_template_vars(project, org_id, current_user),
        **hub_record_template_vars(project, org_id),
    )


def hub_record_template_vars(project, organization_id: str) -> dict:
    """Read-only facts the Project page shows from records kept on other pages: the job address,
    the generated contracts with their signing status, and the job's purchase orders."""
    from app.services.contract_generation import _location_address
    from app.services.supplier_hub import project_purchase_orders

    return {
        # The free-text address, else the structured job location (as the contract and the PO do).
        "job_address": (project.address or "").strip() or _location_address(project),
        "hub_contracts": _hub_contracts(project.id, organization_id),
        "purchase_orders": project_purchase_orders(organization_id=organization_id, project_id=project.id),
        "project_calculations": _project_calculations(project.id, organization_id),
        "guided_summary": _guided_summary(project.id, organization_id),
    }


def _guided_summary(project_id: int, organization_id: str):
    """The project's guided estimate, for the Project page (read only)."""
    from app.services.guided_estimating import get_guided, workflow_view

    guided = get_guided(organization_id, project_id)
    if guided is None:
        return None
    if guided.scope_status != "FINALIZED":
        return {"guided": guided, "done": 0, "included": 0}
    view = workflow_view(guided)
    return {"guided": guided, "done": view["done"], "included": view["included"]}


def _project_calculations(project_id: int, organization_id: str):
    """Calculator results linked to this project, newest first (read only)."""
    from app.models.project_calculation import ProjectCalculation

    return (ProjectCalculation.query.filter_by(project_id=project_id, organization_id=organization_id)
            .order_by(ProjectCalculation.created_at.desc(), ProjectCalculation.id.desc()).all())


def _hub_contracts(project_id: int, organization_id: str) -> list[dict]:
    """Generated contracts and their signing status, for the Project page (read only).

    The Contract page stays where a contract is generated, sent and countersigned."""
    from app.models.project_contract import GeneratedProjectContract
    from app.services.signing import overlay_for_contract

    rows = (GeneratedProjectContract.query.filter_by(project_id=project_id, organization_id=organization_id)
            .order_by(GeneratedProjectContract.generated_at.desc(), GeneratedProjectContract.id.desc()).all())
    contracts = []
    for row in rows:
        overlay = overlay_for_contract(row.id, organization_id)
        if overlay.request_status == "EXECUTED":
            label = "Signed — executed"
        elif overlay.request_status:
            label = overlay.hub_label
        else:
            label = "Generated — not signed"
        contracts.append({"number": row.contract_number, "label": label})
    return contracts


@projects_bp.route("/<int:id>/print.pdf")
def print_project(id):
    org_id = get_current_organization_id()
    project = Project.query.filter_by(id=id, organization_id=org_id).first_or_404()
    from app.services.desk_print import render_fact_sheet

    payload = render_fact_sheet(
        project.name,
        [
            (
                "Project",
                [
                    project.name,
                    project.project_number or "No project number",
                    project.client.name,
                ],
            )
        ],
    )
    return send_file(
        BytesIO(payload),
        mimetype="application/pdf",
        as_attachment=False,
        download_name=f"project-{project.id}.pdf",
    )


@projects_bp.route("/<int:id>/drawing-requirement", methods=["POST"])
def set_project_drawing_requirement_choice(id):
    org_id = get_current_organization_id()
    project = Project.query.filter_by(id=id, organization_id=org_id).first_or_404()
    try:
        set_project_drawing_requirement(
            organization_id=org_id,
            project_id=project.id,
            requirement=request.form.get("drawing_requirement", ""),
        )
    except ProjectDrawingRequirementError as exc:
        flash(str(exc), "error")
        return redirect(url_for("projects.view_project", id=project.id))
    drawing_state = derive_drawing_state(
        project.drawing_requirement,
        bool(project_plans(org_id, project.id)),
    )
    if drawing_state == DRAWING_STATE_REQUIRED_MISSING:
        flash("Drawings are required. None are on this project yet.", "success")
        return redirect(
            url_for("plan_intelligence.list_plans", project_id=project.id)
        )
    if drawing_state == DRAWING_STATE_PRESENT:
        flash(
            "The drawing choice is recorded. Current drawings stay on the project.",
            "success",
        )
    else:
        flash(
            "Drawings are not required for this project. No drawing was added.",
            "success",
        )
    return redirect(url_for("projects.view_project", id=project.id))


@projects_bp.route("/<int:id>/workflow-documents")
def workflow_documents(id):
    org_id = get_current_organization_id()
    project = Project.query.filter_by(id=id, organization_id=org_id).first_or_404()
    return render_template(
        "projects/workflow_documents.html",
        project=project,
        document_groups=workflow_document_groups(project),
        breadcrumb_items=[
            {"label": "Projects", "url": url_for("projects.list_projects")},
            {"label": project.name, "url": url_for("projects.view_project", id=project.id)},
            {"label": "Workflow documents", "url": None},
        ],
    )


def _lifecycle_gate():
    gate = require_instance_owner_or_system_administrator()
    if gate is not None:
        return gate
    return None


def _scoped_project(project_id):
    org_id = get_current_organization_id()
    return Project.query.filter_by(id=project_id, organization_id=org_id).first_or_404()


def _open_supplier_orders(project) -> list:
    """Supplier orders still waiting or confirmed with a delivery today or later: shown before closing so a
    delivery is not forgotten (job lifecycle walk, 20 Oct 2026). A notice only; closing is unchanged."""
    from datetime import date as _date

    from app.models.supplier_portal import PO_CONFIRMED, PO_PLACED
    from app.services.supplier_hub import project_purchase_orders

    rows = []
    for row in project_purchase_orders(organization_id=project.organization_id, project_id=project.id):
        when = row["schedule"]["date"]
        if row["order"].status in (PO_PLACED, PO_CONFIRMED) and (when is None or when >= local_today()):
            rows.append(row)
    return rows


@projects_bp.route("/<int:id>/close", methods=["GET", "POST"], endpoint="close_project")
def close_project_action(id):
    denied = _lifecycle_gate()
    if denied is not None:
        return denied
    project = _scoped_project(id)
    open_punch_items = list_open_punch_list_items(
        project, organization_id=project.organization_id
    )
    open_punch_count = len(open_punch_items)
    if request.method == "GET":
        if project.operating_state != OPERATING_STATE_ACTIVE:
            flash(contractor_copy.PROJECT_ALREADY_CLOSED, "error")
            return redirect(url_for("projects.view_project", id=project.id))
        return render_template(
            "projects/close_confirm.html",
            project=project,
            open_punch_count=open_punch_count,
            open_orders=_open_supplier_orders(project),
        )
    try:
        close_project(
            project,
            current_user,
            confirm_open_punch=request.form.get("confirm_open_punch"),
        )
    except ProjectLifecycleUnauthorizedError:
        abort(403)
    except ProjectLifecycleError as exc:
        flash(str(exc), "error")
        if str(exc) == contractor_copy.PROJECT_CLOSE_OPEN_PUNCH_REQUIRED:
            return render_template(
                "projects/close_confirm.html",
                project=project,
                open_punch_count=open_punch_count,
                open_orders=_open_supplier_orders(project),
            ), 400
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
    from app.services.time_entry import customer_clients_only  # the own-company record is not a customer

    clients = customer_clients_only(Client.query.filter_by(organization_id=org_id), org_id).order_by(Client.name.asc()).all()
    options = _context_options()
    options.update(_guided_form_options(org_id))

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
            guided_next = _guided_after_create(project, org_id, options)
            follow_on = _plan_start_after_create(project, org_id)
            if guided_next and (request.form.get("plan_start") or "later") != "generate":
                return guided_next  # the plan (if any) is uploaded; the estimate comes next
            if follow_on:
                return follow_on
            return redirect(url_for("projects.project_setup", id=project.id))

        except (CommercialContextValidationError, PermitFoundationError) as e:
            db.session.rollback()
            flash(str(e), "error")
            return render_template("projects/form.html", clients=clients, **options)
        except Exception as e:
            db.session.rollback()
            flash(f"Error creating project: {str(e)}", "error")
            return render_template("projects/form.html", clients=clients, **options)

    return render_template("projects/form.html", clients=clients, **options)


def _guided_form_options(org_id):
    """Guided Estimating on New Project (23 Oct 2026): project type, contractor role, and a carried calculation."""
    from app.models.guided_estimating import CONTRACTOR_ROLE_LABELS, PROJECT_TYPE_LABELS
    from app.models.project_calculation import CALCULATORS
    from app.services.calculator_projects import get_carry, restore_url
    from app.services.guided_estimating import COMMERCIAL_TYPE_HINT

    token = request.values.get("carry")
    carry = get_carry(organization_id=org_id, user_id=getattr(current_user, "id", None), token=token) if token else None
    return {
        "guided_project_types": PROJECT_TYPE_LABELS,
        "guided_roles": CONTRACTOR_ROLE_LABELS,
        "guided_commercial_hint": COMMERCIAL_TYPE_HINT,
        "start_guided": bool(request.values.get("guided") or carry),
        "carry": carry,
        "carry_label": CALCULATORS.get(carry.calculator, carry.calculator) if carry else "",
        "carry_cancel_url": restore_url(carry) if carry else "",
    }


def _guided_after_create(project, org_id, options):
    """After the project is saved: keep the carried calculation on it, and start the guided estimate if asked."""
    from app.services import calculator_projects as CP
    from app.services import guided_estimating as G

    carry, record, guided = options.get("carry"), None, None
    try:
        if carry is not None:
            record = CP.attach_carry(carry, project, user_id=getattr(current_user, "id", None),
                                     actor_display_name=current_actor_display_name(fallback="Office"))
        if request.form.get("start_guided"):
            guided = G.start_guided_estimate(organization_id=org_id, project_id=project.id,
                                             project_type=request.form.get("guided_project_type", ""),
                                             contractor_role=request.form.get("contractor_role", ""),
                                             actor=current_actor_display_name(fallback="Office"),
                                             user_id=getattr(current_user, "id", None))
    except (CP.CalculatorProjectError, G.GuidedEstimatingError) as exc:
        db.session.rollback()
        flash(f"The project was saved. {exc} You can start the estimate from the project page.", "error")
    if guided is not None:
        if record is not None:
            flash(f"Your {record.calculator_label} result is saved on the project. Choose who does each stage and "
                  "finalize the scope; the result then waits for its stage's review.", "success")
        else:
            flash("Choose who does each stage.", "success")
        return redirect(url_for("guided.scope", project_id=project.id))
    if record is not None:
        flash(f"Your {record.calculator_label} result is saved on the project.", "success")
        return redirect(url_for("guided.calculation", project_id=project.id, calculation_id=record.id))
    return None


def _plan_start_after_create(project, org_id):
    """New project, step two (23 Oct 2026): upload the plan PDF now, or go straight to the drawing tools.

    Either choice records that drawings are required. A failed upload never undoes the project."""
    choice = (request.form.get("plan_start") or "later").strip()
    if choice not in ("upload", "generate"):
        return None
    try:
        set_project_drawing_requirement(organization_id=org_id, project_id=project.id, requirement="REQUIRED")
    except ProjectDrawingRequirementError:
        pass
    if choice == "generate":
        return redirect(url_for("construction_drawings.index", project_id=project.id))
    file_storage = request.files.get("plan_file")
    if file_storage is None or not (file_storage.filename or "").strip():
        flash("Choose the plan PDF to upload.", "error")
        return redirect(url_for("plan_intelligence.upload_plan", project_id=project.id))
    from app.plan_intelligence.services import PlanIntelligenceServiceError, upload_plan_pdf

    try:
        document = upload_plan_pdf(project, file_storage, notes="Added when the project was created.")
    except PlanIntelligenceServiceError as exc:
        flash(f"The project was saved, but the plan was not uploaded: {exc}", "error")
        return redirect(url_for("plan_intelligence.upload_plan", project_id=project.id))
    flash("Plan PDF uploaded.", "success")
    return redirect(url_for("plan_intelligence.view_plan", project_id=project.id, document_id=document.id))


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


@projects_bp.route("/<int:id>/client", methods=["GET", "POST"])
def correct_project_client_page(id):
    org_id = get_current_organization_id()
    project = Project.query.filter_by(id=id, organization_id=org_id).first_or_404()
    clients = (
        Client.query.filter_by(organization_id=org_id)
        .order_by(Client.name.asc())
        .all()
    )
    client_in_company = any(row.id == project.client_id for row in clients)
    if request.method == "POST":
        try:
            correct_project_client(
                organization_id=org_id,
                project_id=project.id,
                client_id=request.form.get("client_id", type=int),
            )
        except ProjectClientError as exc:
            flash(str(exc), "error")
            return render_template(
                "projects/correct_client.html",
                project=project,
                clients=clients,
                client_in_company=client_in_company,
            ), 400
        flash("This project now uses the selected client.", "success")
        return redirect(url_for("projects.view_project", id=project.id))
    return render_template(
        "projects/correct_client.html",
        project=project,
        clients=clients,
        client_in_company=client_in_company,
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


import app.routes.project_contract  # noqa: E402,F401 — registers contract review routes
