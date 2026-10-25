"""Field quick actions of the Magnificent Seven (25 Oct 2026), on the existing Field blueprint.

My Hours (field.my_time) · Add Receipt · Need Materials · Extra Work (field.extra_work, extended) · Confirm Delivery ·
Job Update · My Schedule (field.week). Every page keeps the job the person confirmed in Field, shows only jobs the
person may see (Field-only crew: the jobs they are booked on, plus Shop / Company), and never shows a price, cost,
wage, margin or another company's record. Registered on field_bp so the Field-only wall lets crew reach them.
"""

from __future__ import annotations

from flask import abort, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user

from app import db
from app.routes.field import (
    _active_company_project,
    _confirmed_operating_project,
    _organization,
    _project_is_active,
    _project_or_redirect,
    _set_confirmed_project,
    _visible_ids,
    _visible_projects,
    field_bp,
)
from app.services.field_operations import FieldOperationError
from app.services.local_time import local_today

ACTIONS = {
    "materials": ("Need Materials", "field.materials"),
    "extra_work": ("Extra Work", "field.extra_work"),
    "delivery": ("Confirm Delivery", "field.deliveries"),
    "job_update": ("Job Update", "field.job_update"),
}


def _job_projects(organization):
    """The person's active customer jobs (no Shop / Company project: those actions need a job site)."""
    from app.services.time_entry import is_company_time_project

    return [p for p in _visible_projects(organization) if _project_is_active(p) and not is_company_time_project(p)]


def _job_or_redirect(project_id):
    organization = _organization()
    project = _project_or_redirect(organization, project_id)
    if project is None or not _project_is_active(project):
        flash("That job is not available. Choose one of your jobs.", "error")
        return organization, None
    _set_confirmed_project(organization.id, project.id)
    return organization, project


@field_bp.route("/choose/<action>")
def choose_job(action):
    """One list of the person's jobs; each goes straight to the action on that job."""
    if action not in ACTIONS:
        abort(404)
    organization = _organization()
    title, endpoint = ACTIONS[action]
    projects = _job_projects(organization)
    current = _confirmed_operating_project(organization)
    if len(projects) == 1:
        return redirect(url_for(endpoint, project_id=projects[0].id))
    return render_template("field/choose_job.html", title=title, endpoint=endpoint, projects=projects,
                           current_id=current.id if current else None)


# ------------------------------------------------------------------------------------------------------ receipts
def _receipt_projects(organization):
    projects = [p for p in _visible_projects(organization) if _project_is_active(p)]
    company = _active_company_project(organization.id)
    from app.services.time_entry import is_company_time_project

    jobs = [p for p in projects if not is_company_time_project(p)]
    return jobs, company


@field_bp.route("/receipt")
def receipt():
    from app.services import receipts as R

    organization = _organization()
    jobs, company = _receipt_projects(organization)
    current = _confirmed_operating_project(organization)
    wanted = request.args.get("project_id", type=int)
    selected = None
    for p in jobs + ([company] if company else []):
        if p.id == wanted:
            selected = p.id
    if selected is None and current is not None and any(p.id == current.id for p in jobs):
        selected = current.id
    return render_template("field/receipt.html", jobs=jobs, company_project=company, selected=selected,
                           mine=R.worker_receipts(organization.id, current_user.id), worker_label=R.worker_label,
                           actor_name=current_user.display_name)


@field_bp.route("/receipts/register", methods=["POST"])
def receipt_register():
    """Called by the phone (field.js) after the receipt photo reached the office. Idempotent."""
    from app.services import receipts as R

    organization = _organization()
    payload = request.get_json(silent=True) or {}
    jobs, company = _receipt_projects(organization)
    allowed = {p.id for p in jobs} | ({company.id} if company else set())
    try:
        row, created = R.register(organization.id, current_user, client_capture_uuid=payload.get("client_capture_uuid"),
                                  supplier=payload.get("supplier") or "", amount=payload.get("amount"),
                                  note=payload.get("note") or "", visible_project_ids=allowed)
    except FieldOperationError as exc:
        db.session.rollback()
        return jsonify({"error": str(exc)}), 400
    return jsonify({"id": row.id, "number": row.number, "status": R.worker_label(row),
                    "url": url_for("field.receipt_view", receipt_id=row.id)}), 201 if created else 200


@field_bp.route("/receipts/<int:receipt_id>")
def receipt_view(receipt_id):
    from app.services import receipts as R

    organization = _organization()
    row = R.receipt_for(organization.id, receipt_id)
    if row is None or row.submitted_by_user_id != current_user.id:
        abort(404)
    return render_template("field/receipt_view.html", receipt=row, label=R.worker_label(row))


# ----------------------------------------------------------------------------------------------- need materials
@field_bp.route("/projects/<int:project_id>/materials", methods=["GET", "POST"])
def materials(project_id):
    from app.services import material_requests as M

    organization, project = _job_or_redirect(project_id)
    if project is None:
        return redirect(url_for("field.choose_job", action="materials"))
    if request.method == "POST":
        try:
            row, created = M.submit(project, current_user, request.form, request.files.getlist("photos"))
        except FieldOperationError as exc:
            db.session.rollback()
            flash(str(exc), "error")
        else:
            flash(f"Material request {row.number} sent to the office." if created else
                  f"Material request {row.number} was already sent.", "success")
            return redirect(url_for("field.materials", project_id=project.id))
    mine = [r for r in M.worker_requests(organization.id, current_user.id) if r.project_id == project.id]
    return render_template("field/materials.html", project=project, catalogue=M.catalogue_choices(), units=M.UNITS,
                           mine=mine, status_label=M.status_label, today=local_today().isoformat())


@field_bp.route("/requests")
def my_requests():
    """The person's own material requests and extra work, with where each one is now."""
    from app.services import extra_work_reports as EW
    from app.services import material_requests as M

    organization = _organization()
    return render_template("field/my_requests.html",
                           materials=M.worker_requests(organization.id, current_user.id, limit=30),
                           material_label=M.status_label,
                           extra=EW.worker_reports(organization.id, current_user.id, limit=30),
                           extra_label=EW.outcome_label)


# ----------------------------------------------------------------------------------------------------- extra work
@field_bp.route("/extra-work/mine")
def extra_work_mine():
    from app.services import extra_work_reports as EW

    organization = _organization()
    return render_template("field/extra_work_mine.html",
                           rows=EW.worker_reports(organization.id, current_user.id, limit=30),
                           outcome=EW.outcome_label)


@field_bp.route("/extra-work/<int:report_id>/answer", methods=["POST"])
def extra_work_answer(report_id):
    from app.services import extra_work_reports as EW

    organization = _organization()
    row = EW.get(organization.id, report_id)
    if row is None or row.reported_by_user_id != current_user.id:
        abort(404)
    try:
        EW.answer(row, current_user, request.form.get("answer", ""))
        flash("Answer sent to the office.", "success")
    except FieldOperationError as exc:
        flash(str(exc), "error")
    return redirect(url_for("field.extra_work_mine"))


# ------------------------------------------------------------------------------------------------ confirm delivery
@field_bp.route("/projects/<int:project_id>/deliveries")
def deliveries(project_id):
    from app.services import delivery_confirmations as D

    organization, project = _job_or_redirect(project_id)
    if project is None:
        return redirect(url_for("field.choose_job", action="delivery"))
    orders = D.open_orders(organization.id, project.id)
    rows = [{"order": o, "supplier": o.share.supplier.legal_name, "state": D.order_state(o),
             "when": o.scheduled_date or o.delivery_date, "lines": len(o.lines_json or [])} for o in orders]
    return render_template("field/deliveries.html", project=project, rows=rows,
                           recent=D.recent(organization.id, project_id=project.id, limit=10))


@field_bp.route("/projects/<int:project_id>/deliveries/<int:order_id>", methods=["GET", "POST"])
def delivery_confirm(project_id, order_id):
    from app.services import delivery_confirmations as D

    organization, project = _job_or_redirect(project_id)
    if project is None:
        return redirect(url_for("field.choose_job", action="delivery"))
    order = D.order_for_project(organization.id, project.id, order_id)
    if order is None:
        abort(404)
    if request.method == "POST":
        try:
            row, created = D.confirm(order, current_user, request.form, request.files.getlist("photos"))
        except FieldOperationError as exc:
            db.session.rollback()
            flash(str(exc), "error")
        else:
            if row.exception_status == "OPEN":
                flash(f"Delivery {row.outcome_label.lower()} recorded for {order.number}. The office has it.", "success")
            else:
                flash(f"Delivery received recorded for {order.number}.", "success")
            return redirect(url_for("field.deliveries", project_id=project.id))
    return render_template("field/delivery_confirm.html", project=project, order=order,
                           supplier=order.share.supplier.legal_name, lines=D.field_lines(order),
                           state=D.order_state(order), history=D.confirmations_for_order(order))


# ------------------------------------------------------------------------------------------------------ job update
@field_bp.route("/projects/<int:project_id>/job-update", methods=["GET", "POST"])
def job_update(project_id):
    from app.services import daily_summaries as S

    organization, project = _job_or_redirect(project_id)
    if project is None:
        return redirect(url_for("field.choose_job", action="job_update"))
    day = local_today()
    if request.method == "POST":
        try:
            row = S.submit(project, current_user, request.form)
        except FieldOperationError as exc:
            db.session.rollback()
            flash(str(exc), "error")
        else:
            flash("Job update saved to the project." + (" The problem is on the office's list." if
                                                         row.problem_status == "OPEN" else ""), "success")
            return redirect(url_for("field.job_update", project_id=project.id))
    existing = S.existing(organization.id, project.id, day, current_user.id)
    return render_template("field/job_update.html", project=project, facts=S.facts(organization.id, project, day),
                           existing=existing, day=day)


# ------------------------------------------------------------------------------------------------------- reminders
@field_bp.route("/reminders/<int:reminder_id>/read", methods=["POST"])
def reminder_read(reminder_id):
    from app.services import reminders as RM

    organization = _organization()
    try:
        RM.mark_read(organization.id, current_user.id, reminder_id)
    except FieldOperationError:
        abort(404)
    return redirect(url_for("field.today"))


@field_bp.route("/reminders/preference", methods=["POST"])
def reminder_preference():
    from app.services import reminders as RM

    organization = _organization()
    try:
        RM.save_preference(organization.id, current_user, in_app=True, sms=request.form.get("sms") == "1")
        flash("Reminder choice saved.", "success")
    except FieldOperationError as exc:
        flash(str(exc), "error")
    return redirect(url_for("field.text_messages"))


def quick_actions(organization, project):
    """The seven Field quick actions, keeping the confirmed job (Field Today)."""
    from app.services.time_entry import is_company_time_project

    job = project if project is not None and not is_company_time_project(project) else None

    def pick(action, endpoint):
        return url_for(endpoint, project_id=job.id) if job is not None else url_for("field.choose_job", action=action)

    return [
        {"key": "hours", "label": "My Hours", "href": url_for("field.my_time")},
        {"key": "receipt", "label": "Add Receipt",
         "href": url_for("field.receipt", project_id=job.id) if job is not None else url_for("field.receipt")},
        {"key": "materials", "label": "Need Materials", "href": pick("materials", "field.materials")},
        {"key": "extra_work", "label": "Extra Work", "href": pick("extra_work", "field.extra_work")},
        {"key": "delivery", "label": "Confirm Delivery", "href": pick("delivery", "field.deliveries")},
        {"key": "job_update", "label": "Job Update", "href": pick("job_update", "field.job_update")},
        {"key": "schedule", "label": "My Schedule", "href": url_for("field.week")},
    ]


@field_bp.app_template_filter("qty")
def _qty_filter(value):
    from app.services.field_operations import plain_quantity

    return plain_quantity(value)


@field_bp.app_template_global("unit_label")
def _unit_label(value):
    from app.services.material_requests import unit_label

    return unit_label(value)
