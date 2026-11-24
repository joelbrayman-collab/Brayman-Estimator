"""The approved project baseline page (FG-042 S1). Owner or System Administrator only: it shows loaded labour rates."""

from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user

from app.models.project import Project
from app.routes.projects import projects_bp
from app.services.organizations import get_current_organization_id


def _admin_only():
    from app.services.financial_access import can_view_employee_cost

    org = get_current_organization_id()
    if not getattr(current_user, "is_authenticated", False) or not can_view_employee_cost(current_user, org):
        abort(403)
    return org


def _project(project_id, org):
    return Project.query.filter_by(id=project_id, organization_id=org).first_or_404()


def _baseline(project, baseline_id):
    from app.services import project_baseline as PB

    row = PB.get_baseline(project.organization_id, baseline_id)
    if row is None or row.project_id != project.id:
        abort(404)
    return row


def _back(project, baseline=None):
    return redirect(url_for("projects.project_baseline", id=project.id,
                            baseline=baseline.id if baseline is not None else None))


def _act(project, baseline, done: str, fn):
    from app.services.project_baseline import BaselineError

    try:
        fn()
    except BaselineError as exc:
        flash(str(exc), "error")
    else:
        flash(done, "success")
    return _back(project, baseline)


@projects_bp.route("/<int:id>/baseline")
def project_baseline(id):
    from app.models.estimate import Estimate, EstimateVersion
    from app.services import project_baseline as PB

    org = _admin_only()
    project = _project(id, org)
    rows = PB.baselines_for_project(org, project.id)
    chosen = next((r for r in rows if str(r.id) == request.args.get("baseline")), rows[0] if rows else None)
    versions = (EstimateVersion.query.join(Estimate, Estimate.id == EstimateVersion.estimate_id)
                .filter(Estimate.project_id == project.id, Estimate.organization_id == org)
                .order_by(EstimateVersion.id.desc()).all())
    return render_template("projects/baseline.html", project=project, baselines=rows, baseline=chosen,
                           versions=versions, data=PB.view(chosen, include_rates=True) if chosen else None)


@projects_bp.route("/<int:id>/baseline/create", methods=["POST"])
def create_project_baseline(id):
    from app.models.estimate import EstimateVersion
    from app.services import project_baseline as PB

    org = _admin_only()
    project = _project(id, org)
    version = EstimateVersion.query.get(request.form.get("estimate_version_id", type=int) or 0)
    if version is None:
        flash("Choose the estimate version this baseline is for.", "error")
        return _back(project)
    created = []
    return _act(project, None, "Provisional baseline created.", lambda: created.append(
        PB.create_provisional_baseline(project, version, actor=current_user,
                                       option_label=request.form.get("option_label", ""),
                                       labour_selling_rate=request.form.get("labour_selling_rate", ""))))


@projects_bp.route("/<int:id>/baseline/<int:baseline_id>/import", methods=["POST"])
def import_project_baseline_labour(id, baseline_id):
    from app.services import project_baseline as PB

    org = _admin_only()
    project = _project(id, org)
    baseline = _baseline(project, baseline_id)
    upload = request.files.get("labour_csv")
    if upload is None or not upload.filename:
        flash("Choose the Labour Calculation Detail by Person file (CSV).", "error")
        return _back(project, baseline)
    data = upload.read(2_000_000)
    return _act(project, baseline, "Labour allocations imported.",
                lambda: PB.import_labour_csv(baseline, data, actor=current_user))


@projects_bp.route("/<int:id>/baseline/<int:baseline_id>/lines", methods=["POST"])
def add_project_baseline_line(id, baseline_id):
    from app.services import project_baseline as PB

    org = _admin_only()
    project = _project(id, org)
    baseline = _baseline(project, baseline_id)
    f = request.form
    return _act(project, baseline, "Line added.", lambda: PB.add_line(
        baseline, actor=current_user, category=f.get("category", ""), description=f.get("description", ""),
        net_cost=f.get("net_cost", ""), markup_rate=(f.get("markup_rate") or None),
        quoted_price=(f.get("quoted_price") or None), price_override_reason=f.get("price_override_reason"),
        is_provisional=bool(f.get("is_provisional")), provisional_reason=f.get("provisional_reason"),
        supplier_name=f.get("supplier_name") or None))


@projects_bp.route("/<int:id>/baseline/<int:baseline_id>/lines/<int:line_id>/remove", methods=["POST"])
def remove_project_baseline_line(id, baseline_id, line_id):
    from app.services import project_baseline as PB

    org = _admin_only()
    project = _project(id, org)
    baseline = _baseline(project, baseline_id)
    return _act(project, baseline, "Line removed.", lambda: PB.remove_line(baseline, line_id, actor=current_user))


@projects_bp.route("/<int:id>/baseline/<int:baseline_id>/open-items", methods=["POST"])
def add_project_baseline_open_item(id, baseline_id):
    from app.services import project_baseline as PB

    org = _admin_only()
    project = _project(id, org)
    baseline = _baseline(project, baseline_id)
    return _act(project, baseline, "Open item recorded.",
                lambda: PB.add_open_item(baseline, request.form.get("description", ""), actor=current_user))


@projects_bp.route("/<int:id>/baseline/<int:baseline_id>/open-items/<int:item_id>/resolve", methods=["POST"])
def resolve_project_baseline_open_item(id, baseline_id, item_id):
    from app.services import project_baseline as PB

    org = _admin_only()
    project = _project(id, org)
    baseline = _baseline(project, baseline_id)
    return _act(project, baseline, "Open item resolved.",
                lambda: PB.resolve_open_item(baseline, item_id, request.form.get("note", ""), actor=current_user))


@projects_bp.route("/<int:id>/baseline/<int:baseline_id>/freeze", methods=["POST"])
def freeze_project_baseline(id, baseline_id):
    from decimal import Decimal, InvalidOperation

    from app.services import project_baseline as PB

    org = _admin_only()
    project = _project(id, org)
    baseline = _baseline(project, baseline_id)
    source = None
    typed = {k: request.form.get(f"source_{k}", "").strip() for k in ("hours", "revenue", "cost", "profit")}
    if any(typed.values()):
        source = dict(PB.approved_source_totals(baseline))
        try:
            source.update({k: Decimal(v) for k, v in typed.items() if v})
        except InvalidOperation:
            flash("A source figure is not a valid number.", "error")
            return _back(project, baseline)
    return _act(project, baseline, "Baseline frozen.", lambda: PB.freeze(baseline, actor=current_user, source=source))
