"""Payroll handoff pages (Joel, 22 Oct 2026): QuickBooks Time transfers, banked hours, the hours policy, and
Shop / Company Work. Office only.

Security route sweep (tests/test_security_route_sweep.py): every route here is an ordinary office page. None
is public; signed-out visitors get the login wall, field-only crew are sent to Field (protect_office_routes),
and this blueprint additionally requires office financial access (the Accounting rule) on every request.
Changing QuickBooks Time person / job-code links and the hours policy further needs the owner or a System
Administrator (checked in the services). Every query is scoped to the signed-in organization.
"""

from __future__ import annotations

from datetime import date, timedelta

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user

from app import db
from app.services import banked_hours as banked
from app.services import quickbooks_time as qbt
from app.services.access_domains import require_office_financial_access
from app.services.instance_authority import is_instance_owner, is_system_administrator
from app.services.organizations import get_current_organization_id

payroll_time_bp = Blueprint("payroll_time", __name__)


@payroll_time_bp.before_request
def _office_only():
    return require_office_financial_access()


def _org():
    return get_current_organization_id()


def _can_administer(org) -> bool:
    return is_instance_owner(current_user, org) or is_system_administrator(current_user, org)


def _date_arg(name, default):
    raw = (request.values.get(name) or "").strip()
    if not raw:
        return default
    try:
        return date.fromisoformat(raw)
    except ValueError:
        return default


# ------------------------------------------------------------------ QuickBooks Time transfers


@payroll_time_bp.route("/time/quickbooks-time")
def quickbooks_time():
    """Office: approved time → QuickBooks Time. Status of every transfer, Send / Retry, last check."""
    org = _org()
    status = (request.args.get("status") or "").strip() or None
    if status not in qbt.STATUS_LABELS:
        status = None
    return render_template("payroll_time/quickbooks_time.html", connection=qbt.connection_status(),
                           rows=qbt.transfer_rows(org, status=status), counts=qbt.counts(org),
                           labels=qbt.STATUS_LABELS, status=status, events=qbt.history(org, 40),
                           can_administer=_can_administer(org), today=date.today())


@payroll_time_bp.route("/time/quickbooks-time/send", methods=["POST"])
def quickbooks_time_send():
    """Office: send waiting, newly linked and failed transfers now (the same send approval does)."""
    result = qbt.send_waiting(_org(), actor=current_user)
    _flash_send(result)
    return redirect(url_for("payroll_time.quickbooks_time"))


@payroll_time_bp.route("/time/quickbooks-time/transfers/<int:transfer_id>/retry", methods=["POST"])
def quickbooks_time_retry(transfer_id):
    """Office: retry one transfer. Looks QuickBooks Time up first, so a retry never duplicates."""
    org = _org()
    if qbt.QuickBooksTimeTransfer.query.filter_by(id=transfer_id, organization_id=org).first() is None:
        abort(404)
    _flash_send(qbt.send_waiting(org, actor=current_user, transfer_ids=[transfer_id]))
    return redirect(url_for("payroll_time.quickbooks_time"))


@payroll_time_bp.route("/time/quickbooks-time/transfers/<int:transfer_id>/send-anyway", methods=["POST"])
def quickbooks_time_send_anyway(transfer_id):
    """Office: release one entry that is in a hand-entry file (reason required, kept in the history)."""
    try:
        _flash_send(qbt.send_anyway(_org(), transfer_id, actor=current_user, reason=request.form.get("reason")))
    except qbt.QuickBooksTimeError as exc:
        flash(str(exc), "error")
    return redirect(url_for("payroll_time.quickbooks_time"))


def _flash_send(result):
    if not result or not result.get("connected"):
        flash("QuickBooks Time is not switched on. Nothing was sent; approved time is waiting here.", "error")
        return
    parts = [f"{result['sent']} sent", f"{result['updated']} updated"]
    if result["failed"]:
        parts.append(f"{result['failed']} failed")
    if result["needs_setup"]:
        parts.append(f"{result['needs_setup']} need a link")
    if result["in_file"]:
        parts.append(f"{result['in_file']} already in a hand-entry file")
    flash("QuickBooks Time: " + ", ".join(parts) + ".", "error" if result["failed"] else "success")


@payroll_time_bp.route("/time/quickbooks-time/links", methods=["GET", "POST"])
def quickbooks_time_links():
    """Office sees the links; only the owner or a System Administrator changes them (audited)."""
    from app.models.work_structure import ProjectWorkActivity, ProjectWorkElement
    from app.services.shared_api import list_organization_projects
    from app.services.time_entry import get_company_time_project, org_time_workers

    org = _org()
    if request.method == "POST":
        try:
            kind = request.form.get("kind")
            listed = qbt.directory()  # the QuickBooks Time names for the chosen numbers, when connected
            people = {u["id"]: u["name"] for u in listed["users"]}
            codes = {j["id"]: j["name"] for j in listed["jobcodes"]}
            chosen_person = (request.form.get("qbt_user_id") or "").strip()
            chosen_code = (request.form.get("qbt_jobcode_id") or "").strip()
            if kind == "person":
                qbt.link_employee(org, int(request.form.get("user_id") or 0), chosen_person,
                                  actor=current_user, qbt_name=people.get(chosen_person))
            elif kind == "project":
                qbt.link_jobcode(org, project_id=int(request.form.get("project_id") or 0),
                                 jobcode_id=chosen_code, actor=current_user, jobcode_name=codes.get(chosen_code))
            elif kind == "activity":
                qbt.link_jobcode(org, activity_id=int(request.form.get("activity_id") or 0),
                                 jobcode_id=chosen_code, actor=current_user, jobcode_name=codes.get(chosen_code))
            else:
                raise qbt.QuickBooksTimeError("Choose what to link.")
            flash("Link saved.", "success")
        except (qbt.QuickBooksTimeError, ValueError) as exc:
            db.session.rollback()
            flash(str(exc) if isinstance(exc, qbt.QuickBooksTimeError) else "Check the link.", "error")
        return redirect(url_for("payroll_time.quickbooks_time_links"))
    company = get_company_time_project(org)
    categories = []
    if company is not None:
        categories = (ProjectWorkActivity.query.join(ProjectWorkElement)
                      .filter(ProjectWorkElement.project_id == company.id, ProjectWorkActivity.organization_id == org)
                      .order_by(ProjectWorkActivity.sort_order, ProjectWorkActivity.id).all())
    return render_template("payroll_time/links.html", workers=org_time_workers(org), projects=list_organization_projects(org),
                           categories=categories, people=qbt.employee_links(org), jobs=qbt.jobcode_links(org),
                           directory=qbt.directory(), can_administer=_can_administer(org),
                           connection=qbt.connection_status())


@payroll_time_bp.route("/time/quickbooks-time/check", methods=["GET", "POST"])
def quickbooks_time_check():
    """Office: compare QuickBooks Time with what CalibraytAI sent, for a date range. Reads only."""
    org = _org()
    start = _date_arg("from", date.today() - timedelta(days=date.today().weekday() + 7))
    end = _date_arg("to", date.today())
    result = None
    if request.method == "POST":
        try:
            result = qbt.reconcile(org, start=start, end=end, actor=current_user)
        except (qbt.QuickBooksTimeError, qbt.TransportError) as exc:
            db.session.rollback()
            flash(str(exc), "error")
    return render_template("payroll_time/check.html", result=result, start=start, end=end,
                           connection=qbt.connection_status())


# ------------------------------------------------------------------ banked hours


@payroll_time_bp.route("/time/banked-hours")
def banked_hours_index():
    """Office: everyone's banked balance under the company's own hours policy."""
    org = _org()
    policy = banked.latest_policy(org)
    return render_template("payroll_time/banked_index.html", rows=banked.organization_balances(org), policy=policy,
                           policy_text=banked.policy_summary(policy), can_administer=_can_administer(org))


@payroll_time_bp.route("/time/banked-hours/<int:user_id>")
def banked_hours_worker(user_id):
    """Office: one person's banked-hours ledger, time off and adjustments."""
    from app.models.user import User, UserMembership

    org = _org()
    worker = db.session.get(User, user_id)
    if worker is None or UserMembership.query.filter_by(user_id=user_id, organization_id=org).first() is None:
        abort(404)
    return render_template("payroll_time/banked_worker.html", worker=worker,
                           summary=banked.worker_summary(org, user_id), today=date.today(),
                           is_self=worker.id == current_user.id)


@payroll_time_bp.route("/time/banked-hours/<int:user_id>/time-off", methods=["POST"])
def banked_hours_time_off(user_id):
    """Office: record banked time taken off (reduces the balance; reason kept)."""
    try:
        banked.record_time_off(_org(), user_id, hours=request.form.get("hours"), on_date=request.form.get("on_date"),
                               reason=request.form.get("reason"), actor=current_user)
        flash("Time off recorded.", "success")
    except banked.BankedHoursError as exc:
        db.session.rollback()
        flash(str(exc), "error")
    return redirect(url_for("payroll_time.banked_hours_worker", user_id=user_id))


@payroll_time_bp.route("/time/banked-hours/<int:user_id>/adjust", methods=["POST"])
def banked_hours_adjust(user_id):
    """Office: add or remove banked hours with a reason (kept in the ledger)."""
    try:
        banked.adjust(_org(), user_id, hours=request.form.get("hours"), reason=request.form.get("reason"),
                      actor=current_user)
        flash("Banked hours adjusted.", "success")
    except banked.BankedHoursError as exc:
        db.session.rollback()
        flash(str(exc), "error")
    return redirect(url_for("payroll_time.banked_hours_worker", user_id=user_id))


@payroll_time_bp.route("/settings/hours-policy", methods=["GET", "POST"])
def hours_policy():
    """Owner or System Administrator: the company's hours policy (normal week, extra hours, bank rate, which
    work counts, week start). Each save is a new version with who, when, old → new and an effective date."""
    org = _org()
    if not _can_administer(org):
        abort(403)
    current = banked.latest_policy(org)
    form = request.form if request.method == "POST" else {}
    if request.method == "POST":
        try:
            row = banked.save_policy(org, current_user, request.form)
            flash(f"Hours policy saved (version {row.version}, in effect from {row.effective_from.strftime('%b %d, %Y')}).",
                  "success")
            return redirect(url_for("payroll_time.hours_policy"))
        except banked.BankedHoursError as exc:
            db.session.rollback()
            flash(str(exc), "error")
    return render_template("payroll_time/hours_policy.html", current=current, versions=banked.policy_versions(org),
                           policy_text=banked.policy_summary(current), form=form, days=banked.DAY_NAMES,
                           fields=dict(banked.POLICY_FIELDS), today=date.today())


# ------------------------------------------------------------------ Shop / Company Work


@payroll_time_bp.route("/time/company")
def company_work():
    """Office: Shop / Company Work — its categories and hours. Not a customer job and never shown as one."""
    from app.services.project_performance import assemble_project_labour_cost
    from app.services.time_entry import get_company_time_project, list_time_entries, time_entry_presentation

    org = _org()
    company = get_company_time_project(org)
    if company is None:
        return render_template("payroll_time/company.html", company=None)
    start = _date_arg("from", date.today() - timedelta(days=date.today().weekday()))
    end = _date_arg("to", date.today())
    entries = list_time_entries(organization_id=org, project_id=company.id, work_date_from=start, work_date_to=end)
    by_category = {}
    for e in entries:
        if e.status == "APPROVED":
            by_category[e.activity_display_name] = by_category.get(e.activity_display_name, 0) + e.hours
    return render_template("payroll_time/company.html", company=company,
                           categories=[a for el in company.work_elements for a in el.activities],
                           rows=[time_entry_presentation(e) for e in entries], by_category=sorted(by_category.items()),
                           cost=assemble_project_labour_cost(org, company.id), start=start, end=end)


@payroll_time_bp.route("/time/company/categories", methods=["POST"])
def company_work_category():
    """Office: add a Shop / Company Work category (for example "Snow clearing at the yard")."""
    from app.services.time_entry import TimeEntryError, add_company_time_category

    try:
        add_company_time_category(_org(), request.form.get("name"), actor=current_user)
        flash("Category added.", "success")
    except TimeEntryError as exc:
        db.session.rollback()
        flash(str(exc), "error")
    return redirect(url_for("payroll_time.company_work"))
