"""FG-035 TIME office review, approval, and desktop entry.

Same LabourTimeEntry authority as Field Web. No separate desktop engine.
"""

from datetime import date, timedelta

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user

from app.models.time_entry import (
    TIME_STATUS_APPROVED,
    TIME_STATUS_RETURNED,
    TIME_STATUS_SUBMITTED,
)
from app.services.organizations import get_current_organization
from app.services.shared_api import list_organization_projects
from app.services.time_entry import (
    TimeEntryError,
    TimeEntryForbiddenError,
    TimeEntryNotFoundError,
    approve_time,
    contractor_time_status_label,
    correct_approved_time,
    get_time_entry,
    list_time_entries,
    list_time_work_choices,
    org_time_workers,
    return_time,
    submit_time,
    time_entry_presentation,
)

time_entry_bp = Blueprint("time_entry", __name__, url_prefix="/time")

REVIEW_STATUSES = (
    TIME_STATUS_SUBMITTED,
    TIME_STATUS_RETURNED,
    TIME_STATUS_APPROVED,
)


def _org():
    return get_current_organization()


def _optional_int(value):
    raw = (value or "").strip()
    if not raw:
        return None
    return int(raw)


def _optional_date(value):
    raw = (value or "").strip()
    if not raw:
        return None
    return date.fromisoformat(raw)


@time_entry_bp.route("")
def review():
    organization = _org()
    status = (request.args.get("status") or "").strip() or None
    if status and status not in REVIEW_STATUSES:
        status = None
    try:
        project_id = _optional_int(request.args.get("project_id"))
        worker_id = _optional_int(request.args.get("worker_user_id"))
        date_from = _optional_date(request.args.get("from"))
        date_to = _optional_date(request.args.get("to"))
    except (TypeError, ValueError):
        flash("Check the time filters.", "error")
        return redirect(url_for("time_entry.review"))
    if date_from is None and date_to is None and not request.args:
        date_from = date.today() - timedelta(days=6)
        date_to = date.today()
    entries = list_time_entries(
        organization_id=organization.id,
        project_id=project_id,
        worker_user_id=worker_id,
        status=status,
        work_date_from=date_from,
        work_date_to=date_to,
    )
    rows = [time_entry_presentation(entry) for entry in entries]
    return render_template(
        "time/review.html",
        rows=rows,
        projects=list_organization_projects(organization.id),
        workers=org_time_workers(organization.id),
        statuses=REVIEW_STATUSES,
        status_label=contractor_time_status_label,
        filters={
            "status": status or "",
            "project_id": project_id,
            "worker_user_id": worker_id,
            "from": date_from.isoformat() if date_from else "",
            "to": date_to.isoformat() if date_to else "",
        },
    )


@time_entry_bp.route("/new", methods=["GET", "POST"])
def new_entry():
    organization = _org()
    projects = list_organization_projects(organization.id)
    project_id = None
    try:
        project_id = _optional_int(request.values.get("project_id"))
    except (TypeError, ValueError):
        flash("Choose a project.", "error")
        return redirect(url_for("time_entry.new_entry"))
    project = None
    choices = []
    if project_id is not None:
        project = next((row for row in projects if row.id == project_id), None)
        if project is None:
            flash("Project not found.", "error")
            return redirect(url_for("time_entry.new_entry"))
        choices = list_time_work_choices(project.id, organization_id=organization.id)
    if request.method == "POST":
        try:
            entry = submit_time(
                project_id=int(request.form.get("project_id") or 0),
                project_work_activity_id=_optional_int(
                    request.form.get("project_work_activity_id")
                )
                or 0,
                hours=request.form.get("hours"),
                work_date=request.form.get("work_date"),
                worker_note=request.form.get("worker_note"),
                extra_work_description=request.form.get("extra_work_description"),
                extra_work_element_id=_optional_int(
                    request.form.get("extra_work_element_id")
                ),
                extra_work_element_name=request.form.get("extra_work_element_name"),
                organization_id=organization.id,
            )
            flash("Time sent for approval.", "success")
            return redirect(url_for("time_entry.detail", time_entry_id=entry.id))
        except (TimeEntryError, TypeError, ValueError) as exc:
            flash(str(exc) if isinstance(exc, TimeEntryError) else "Check the time entry.", "error")
    return render_template(
        "time/form.html",
        projects=projects,
        project=project,
        choices=choices,
        today=date.today().isoformat(),
    )


@time_entry_bp.route("/<int:time_entry_id>")
def detail(time_entry_id):
    organization = _org()
    try:
        entry = get_time_entry(time_entry_id, organization_id=organization.id)
    except TimeEntryNotFoundError as exc:
        flash(str(exc), "error")
        return redirect(url_for("time_entry.review"))
    return render_template(
        "time/detail.html",
        row=time_entry_presentation(entry),
        can_review=current_user.id != entry.worker_user_id,
        status_label=contractor_time_status_label,
    )


@time_entry_bp.route("/<int:time_entry_id>/approve", methods=["POST"])
def approve(time_entry_id):
    try:
        approve_time(time_entry_id=time_entry_id)
        flash("Time approved.", "success")
    except (TimeEntryError, TimeEntryForbiddenError, TimeEntryNotFoundError) as exc:
        flash(str(exc), "error")
    return redirect(url_for("time_entry.detail", time_entry_id=time_entry_id))


@time_entry_bp.route("/<int:time_entry_id>/return", methods=["POST"])
def return_entry(time_entry_id):
    try:
        return_time(time_entry_id=time_entry_id, reason=request.form.get("reason") or "")
        flash("Time returned.", "success")
    except (TimeEntryError, TimeEntryForbiddenError, TimeEntryNotFoundError) as exc:
        flash(str(exc), "error")
    return redirect(url_for("time_entry.detail", time_entry_id=time_entry_id))


@time_entry_bp.route("/approve-selected", methods=["POST"])
def approve_selected():
    ids = request.form.getlist("time_entry_id")
    approved = 0
    errors = []
    for raw in ids:
        try:
            approve_time(time_entry_id=int(raw))
            approved += 1
        except (TimeEntryError, TimeEntryForbiddenError, TimeEntryNotFoundError, ValueError) as exc:
            errors.append(str(exc))
    if approved:
        flash(f"Approved {approved} time {'entry' if approved == 1 else 'entries'}.", "success")
    if errors:
        flash(errors[0], "error")
    return redirect(url_for("time_entry.review", **{k: v for k, v in request.args.items() if v}))


@time_entry_bp.route("/<int:time_entry_id>/correct", methods=["POST"])
def correct(time_entry_id):
    try:
        correction = correct_approved_time(
            time_entry_id=time_entry_id,
            hours=request.form.get("hours"),
            reason=request.form.get("reason") or "",
            work_date=request.form.get("work_date") or None,
        )
        flash("Approved time corrected. The original entry is kept.", "success")
        return redirect(url_for("time_entry.detail", time_entry_id=correction.id))
    except (TimeEntryError, TimeEntryForbiddenError, TimeEntryNotFoundError) as exc:
        flash(str(exc), "error")
        return redirect(url_for("time_entry.detail", time_entry_id=time_entry_id))
