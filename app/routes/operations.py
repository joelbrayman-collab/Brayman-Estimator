"""Office working screens for the Magnificent Seven (25 Oct 2026). Office members only; Field-only crew never.

/operations/attention                      WHAT NEEDS MY ATTENTION? (the full list behind Home)
/operations/material-requests[/<id>]       review, correct, approve, decline, send to the supplier
/operations/extra-work[/<id>]              review, ask the crew, prepare the change order, record the outcome
/operations/deliveries[/<id>]              delivery problems from the site and their resolution
/operations/job-updates[/<id>]             the crew's daily job updates; mark a problem handled
/operations/reminders                      end-of-day reminder settings, my reminders, the reminders sent
"""

from __future__ import annotations

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user

from app import db
from app.models import Project
from app.services.access_domains import require_office_scheduling_authority
from app.services.field_operations import FieldOperationError
from app.services.local_time import local_today
from app.services.organizations import get_current_organization_id

operations_bp = Blueprint("operations", __name__, url_prefix="/operations")


@operations_bp.before_request
def _office_only():
    return require_office_scheduling_authority()


def _org():
    return get_current_organization_id()


def _projects(org):
    return {p.id: p for p in Project.query.filter_by(organization_id=org).all()}


@operations_bp.route("/attention")
def attention():
    from app.services.needs_attention import assemble

    return render_template("operations/attention.html", view=assemble(_org(), current_user))


# ------------------------------------------------------------------------------------------------ material requests
@operations_bp.route("/material-requests")
def material_requests():
    from app.services import material_requests as M

    org = _org()
    rows = M.office_list(org, project_id=request.args.get("project_id", type=int),
                         open_only=request.args.get("show") != "all")
    return render_template("operations/material_requests.html", rows=rows, label=M.status_label,
                           accounts=M.supplier_accounts(org), show_all=request.args.get("show") == "all")


@operations_bp.route("/material-requests/<int:request_id>", methods=["GET", "POST"])
def material_request(request_id):
    from app.services import material_requests as M

    org = _org()
    row = M.get(org, request_id)
    if row is None:
        abort(404)
    if request.method == "POST":
        action = request.form.get("action")
        try:
            if action == "correct":
                M.correct(row, current_user, request.form)
                flash("Quantity saved.", "success")
            elif action == "approve":
                if request.form.get("approved_quantity"):
                    M.correct(row, current_user, request.form)
                M.approve(row, current_user)
                flash(f"{row.number} approved. Choose the supplier and send it.", "success")
            elif action == "decline":
                M.decline(row, current_user, request.form.get("decline_reason", ""))
                flash(f"{row.number} declined. The worker sees the reason.", "success")
            elif action == "send":
                result = M.send_to_supplier([row], current_user, account_id=request.form.get("account_id", type=int) or 0)
                flash(f"Supplier request {result['share'].number} sent to {result['supplier']}. Their price comes back "
                      "on the job's supplier requests; you order from there.", "success")
            else:
                abort(400)
        except FieldOperationError as exc:
            db.session.rollback()
            flash(str(exc), "error")
        return redirect(url_for("operations.material_request", request_id=row.id))
    from app.services.field_operations import image_originals
    from app.services.material_requests import order_for

    return render_template("operations/material_request.html", row=row, label=M.status_label(row),
                           photos=image_originals(row.field_event_id),
                           accounts=M.supplier_accounts(org), history=M.history(row), order=order_for(row),
                           units=M.UNITS, catalogue=M.catalogue_choices())


@operations_bp.route("/material-requests/send", methods=["POST"])
def material_requests_send():
    from app.services import material_requests as M

    org = _org()
    ids = [int(i) for i in request.form.getlist("request_ids") if str(i).isdigit()]
    rows = [r for r in (M.get(org, i) for i in ids) if r is not None]
    try:
        result = M.send_to_supplier(rows, current_user, account_id=request.form.get("account_id", type=int) or 0)
        flash(f"Supplier request {result['share'].number} sent to {result['supplier']} with "
              f"{len(rows)} request{'s' if len(rows) != 1 else ''}.", "success")
    except FieldOperationError as exc:
        db.session.rollback()
        flash(str(exc), "error")
    return redirect(url_for("operations.material_requests"))


# ------------------------------------------------------------------------------------------------------- extra work
@operations_bp.route("/extra-work")
def extra_work():
    from app.services import extra_work_reports as EW

    org = _org()
    show_all = request.args.get("show") == "all"
    rows = EW.office_list(org, project_id=request.args.get("project_id", type=int), open_only=not show_all)
    return render_template("operations/extra_work.html", rows=rows, outcome=EW.outcome_label, show_all=show_all)


@operations_bp.route("/extra-work/<int:report_id>", methods=["GET", "POST"])
def extra_work_report(report_id):
    from app.services import extra_work_reports as EW

    org = _org()
    row = EW.get(org, report_id)
    if row is None:
        abort(404)
    if request.method == "POST":
        action = request.form.get("action")
        try:
            if action == "ask":
                EW.ask(row, current_user, request.form.get("question", ""))
                flash("Question sent to the crew (Field → My extra work).", "success")
            elif action == "not_extra":
                EW.not_extra(row, current_user, request.form.get("note", ""))
                flash("Recorded as part of the original work. Nothing is charged.", "success")
            elif action == "decline":
                EW.decline(row, current_user, request.form.get("note", ""))
                flash("Declined. Nothing is charged to the customer.", "success")
            else:
                abort(400)
        except FieldOperationError as exc:
            db.session.rollback()
            flash(str(exc), "error")
        return redirect(url_for("operations.extra_work_report", report_id=row.id))
    EW.sync_status(row)
    from app.services.field_operations import image_originals

    return render_template("operations/extra_work_report.html", row=row, outcome=EW.outcome_label(row),
                           change_order=EW.change_order(row), history=EW.history(row),
                           photos=image_originals(row.field_event_id))


# ------------------------------------------------------------------------------------------------------- deliveries
@operations_bp.route("/deliveries")
def deliveries():
    from app.services import delivery_confirmations as D

    org = _org()
    return render_template("operations/deliveries.html", open_rows=D.exceptions(org, open_only=True),
                           recent=D.recent(org, limit=40))


@operations_bp.route("/deliveries/<int:confirmation_id>", methods=["GET", "POST"])
def delivery(confirmation_id):
    from app.services import delivery_confirmations as D

    org = _org()
    row = D.get(org, confirmation_id)
    if row is None:
        abort(404)
    if request.method == "POST":
        try:
            D.resolve(row, current_user, resolution=request.form.get("resolution", ""), note=request.form.get("note", ""))
            flash("Delivery problem resolved.", "success")
        except FieldOperationError as exc:
            db.session.rollback()
            flash(str(exc), "error")
        return redirect(url_for("operations.delivery", confirmation_id=row.id))
    from app.services.field_operations import history, image_originals
    from app.models.field_operations import RECORD_DELIVERY

    return render_template("operations/delivery.html", row=row, order=row.order, state=D.order_state(row.order),
                           lines=D.field_lines(row.order), resolutions=D.RESOLUTIONS,
                           confirmations=D.confirmations_for_order(row.order),
                           history=history(org, RECORD_DELIVERY, row.id), photos=image_originals(row.field_event_id))


# ------------------------------------------------------------------------------------------------------ job updates
@operations_bp.route("/job-updates")
def job_updates():
    from app.models.field_operations import DailyJobSummary

    org = _org()
    query = DailyJobSummary.query.filter_by(organization_id=org)
    project_id = request.args.get("project_id", type=int)
    if project_id:
        query = query.filter_by(project_id=project_id)
    rows = query.order_by(DailyJobSummary.work_date.desc(), DailyJobSummary.submitted_at.desc()).limit(100).all()
    return render_template("operations/job_updates.html", rows=rows)


@operations_bp.route("/job-updates/<int:summary_id>", methods=["GET", "POST"])
def job_update(summary_id):
    from app.services import daily_summaries as S

    org = _org()
    row = S.get(org, summary_id)
    if row is None:
        abort(404)
    if request.method == "POST":
        try:
            S.resolve(row, current_user, request.form.get("note", ""))
            flash("Marked handled.", "success")
        except FieldOperationError as exc:
            flash(str(exc), "error")
        return redirect(url_for("operations.job_update", summary_id=row.id))
    from app.models.field_operations import RECORD_JOB_UPDATE
    from app.services.field_operations import history

    return render_template("operations/job_update.html", row=row, facts=row.facts_json or {},
                           history=history(org, RECORD_JOB_UPDATE, row.id))


# -------------------------------------------------------------------------------------------------------- reminders
@operations_bp.route("/reminders", methods=["GET", "POST"])
def reminders():
    from app.models.field_operations import AUDIENCE_OWNER
    from app.services import reminders as RM
    from app.services.instance_authority import is_instance_owner, is_system_administrator
    from app.services.text_messages import has_text_consent, settings_summary

    org = _org()
    can_edit = is_instance_owner(current_user, org) or is_system_administrator(current_user, org)
    if request.method == "POST":
        action = request.form.get("action")
        try:
            if action == "settings":
                RM.save_settings(org, current_user, request.form)
                flash("Reminder settings saved.", "success")
            elif action == "preference":
                RM.save_preference(org, current_user, in_app=True, sms=request.form.get("sms") == "1")
                flash("Your reminder choice is saved.", "success")
            elif action == "send_now":
                summary = RM.send_due(organization_id=org)
                if summary["not_due"]:
                    flash("Not reminder time: reminders go out between the reminder time and the latest time on "
                          "working days.", "error")
                else:
                    flash(f"Reminders made: {summary['crew']} crew, {summary['owner']} owner; {summary['already']} "
                          f"already had today's reminder; texts accepted by the provider: {summary['texts']}.",
                          "success")
            else:
                abort(400)
        except FieldOperationError as exc:
            db.session.rollback()
            flash(str(exc), "error")
        return redirect(url_for("operations.reminders"))
    today = local_today()
    from app.models.user import User

    recent = RM.recent(org)
    ids = {r.user_id for r in recent}
    names = {u.id: u.display_name for u in User.query.filter(User.id.in_(ids)).all()} if ids else {}
    return render_template("operations/reminders.html", settings=RM.settings_for(org), can_edit=can_edit, names=names,
                           window=RM.window(org), pref=RM.preference(org, current_user.id),
                           consent=has_text_consent(current_user), sms=settings_summary(),
                           sms_available=RM.sms_available(), recent=recent,
                           mine=RM.live_view(org, current_user, AUDIENCE_OWNER, today), day_names=RM.DAY_NAMES)


@operations_bp.route("/reminders/<int:reminder_id>/read", methods=["POST"])
def reminder_read(reminder_id):
    from app.services import reminders as RM

    try:
        RM.mark_read(_org(), current_user.id, reminder_id)
    except FieldOperationError:
        abort(404)
    return redirect(url_for("main.dashboard"))
