"""Site Plans: the plans viewer and the crew's Home Screen app (Joel, 23 Oct 2026).

Its own address space, /site-plans/, is the Home Screen app's scope (manifest app/static/site-plans/
manifest.webmanifest, start_url /site-plans/?source=home-screen), separate from CalibraytAI Field (scope "/") and
Useful Calculators (scope /useful-calculators/), both unchanged. The same pages are the office's plans viewer:
the Plans button on every project page (templates/partials/plans_button.html) opens /site-plans/projects/<id>.

- sign_in: public. The office check (app/services/auth.authenticate), kept inside the app's scope, like Useful
  Calculators. Signed out, every other page here comes back to it (app/__init__.py blueprint_login_views).
- index: the projects the person may see (app/services/site_plans.visible_projects: Field's rule for Field-only
  crew, the organization's active projects for the office).
- project: that project's plans and drawings; viewer: one file, every page, sheet numbers where known.
- file / page: the PDF, whole or one page, only to a person who may see the project; Cache-Control private,
  no-store; inline; no range requests (so the phone's offline copy is always the whole file).
- service_worker: /site-plans/sw.js (app/static/site-plans/site-plans-sw.js), scope /site-plans/ only. It keeps
  the plans a person opened, or saved with "Save for offline", for use without signal; the sign-in page and
  "Sign out" remove them (app/static/js/sign-in-clears-field-cache.js, app/static/site-plans/site-plans.js).

No page here shows money, prices, costs, wages or customer contact details.
"""

from __future__ import annotations

from urllib.parse import urlparse

from flask import Blueprint, abort, flash, g, redirect, render_template, request, send_from_directory, url_for
from flask import current_app, make_response
from flask_login import current_user, login_user, logout_user

from app.services import site_plans as SP
from app.services import useful_calculators as UC

site_plans_bp = Blueprint("site_plans", __name__, url_prefix="/site-plans")

SCOPE = "/site-plans/"
PRIVATE = {"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"}


def _organization_id():
    from app.services.organizations import OrganizationAccessError, resolve_membership_organization_id

    if not current_user.is_authenticated:
        return None
    try:
        return resolve_membership_organization_id(current_user)
    except OrganizationAccessError:
        return None


def _viewer():
    """(kind, organization id). Only office members and Field-only crew of a contractor organization get in."""
    organization_id = _organization_id()
    kind = UC.viewer_kind(current_user, organization_id)
    if kind not in ("office", "field_only"):
        abort(403)
    return kind, organization_id


def safe_return(target):
    """Only a path inside this app; anything else returns to the project list."""
    default = url_for("site_plans.index")
    candidate = (target or "").strip()
    if not candidate.startswith(SCOPE) or candidate.startswith("//") or "\\" in candidate:
        return default
    parsed = urlparse(candidate)
    if parsed.scheme or parsed.netloc:
        return default
    return candidate


@site_plans_bp.context_processor
def _site_plans_pages():
    from app import login_manager

    # flask-login's office wording ("...the office application") is not shown inside Site Plans.
    return {"sp_hidden_messages": (login_manager.login_message,)}


@site_plans_bp.app_context_processor
def _plans_button():
    """The office Plans button: which project the current office page is about (templates/base.html)."""
    try:
        if not request or not current_user.is_authenticated or getattr(g, "field_only", False):
            return {}
        organization_id = getattr(g, "organization_id", None)
        project_id = SP.button_project_id(request.endpoint, request.view_args, request.args, organization_id)
    except Exception:  # pragma: no cover - a page never fails because of its button
        current_app.logger.warning("Plans button lookup failed", exc_info=True)
        return {}
    return {"plans_button_project_id": project_id} if project_id else {}


def _page(template, status=200, **context):
    response = make_response(render_template(template, **context), status)
    response.headers["Cache-Control"] = "private, no-store"
    return response


@site_plans_bp.route("/sign-in", methods=["GET", "POST"])
def sign_in():
    from app.services.auth import GENERIC_LOGIN_FAILURE, authenticate

    target = safe_return(request.values.get("next"))
    if current_user.is_authenticated:
        return redirect(target)
    if request.method == "POST":
        user = authenticate(request.form.get("email", ""), request.form.get("password", ""))
        if user is None:
            flash(GENERIC_LOGIN_FAILURE, "error")
            return _page("site_plans/sign_in.html", next_path=target)
        login_user(user, remember=False)
        return redirect(target)
    return _page("site_plans/sign_in.html", next_path=target)


@site_plans_bp.post("/sign-out")
def sign_out():
    if current_user.is_authenticated:
        logout_user()
    return redirect(url_for("site_plans.sign_in"))


@site_plans_bp.get("/sw.js")
def service_worker():
    response = send_from_directory(current_app.static_folder, "site-plans/site-plans-sw.js",
                                   mimetype="application/javascript")
    response.headers["Cache-Control"] = "no-cache"
    response.headers["Service-Worker-Allowed"] = SCOPE
    return response


@site_plans_bp.get("/")
def index():
    kind, organization_id = _viewer()
    projects = SP.visible_projects(current_user, organization_id)
    return _page("site_plans/index.html", kind=kind, projects=projects)


def _project_or_404(organization_id, project_id):
    project = SP.project_for(current_user, organization_id, project_id)
    if project is None:
        abort(404)
    return project


@site_plans_bp.get("/projects/<int:project_id>")
def project(project_id):
    kind, organization_id = _viewer()
    project = SP.project_for(current_user, organization_id, project_id)
    if project is None:
        # Not this person's job (crew), another organization's, or gone: back to the list, like Field.
        flash("That project's plans are not available to you.", "error")
        return redirect(url_for("site_plans.index"))
    files = SP.plan_files(organization_id, project)
    return _page("site_plans/project.html", kind=kind, project=project, files=files,
                 can_upload=kind == "office")


@site_plans_bp.get("/projects/<int:project_id>/<kind>/<int:file_id>")
def viewer(project_id, kind, file_id):
    viewer_kind, organization_id = _viewer()
    project = _project_or_404(organization_id, project_id)
    try:
        plan, data = SP.plan_file(organization_id, project, kind, file_id)
    except SP.PlanFileNotFound:
        abort(404)
    sheets = SP.full_sheet_list(plan, SP.page_sizes(data))
    return _page("site_plans/viewer.html", kind=viewer_kind, project=project, plan=plan,
                 sheets=sheets, pages=len(sheets))


def _pdf(data: bytes, filename: str):
    response = make_response(data)
    response.mimetype = "application/pdf"
    safe = "".join(c for c in filename if c.isalnum() or c in " ._-")[:120] or "plan.pdf"
    response.headers["Content-Disposition"] = f'inline; filename="{safe}"'
    response.headers.update(PRIVATE)
    return response


@site_plans_bp.get("/projects/<int:project_id>/<kind>/<int:file_id>.pdf")
def file(project_id, kind, file_id):
    _kind, organization_id = _viewer()
    project = _project_or_404(organization_id, project_id)
    try:
        plan, data = SP.plan_file(organization_id, project, kind, file_id)
    except SP.PlanFileNotFound:
        abort(404)
    name = plan.title if plan.title.lower().endswith(".pdf") else f"{project.name} {plan.title}.pdf"
    return _pdf(data, name)


@site_plans_bp.get("/projects/<int:project_id>/<kind>/<int:file_id>/page-<int:page>.pdf")
def page(project_id, kind, file_id, page):
    _kind, organization_id = _viewer()
    project = _project_or_404(organization_id, project_id)
    try:
        plan, data = SP.plan_file(organization_id, project, kind, file_id)
    except SP.PlanFileNotFound:
        abort(404)
    one = SP.single_page(data, page)
    if one is None:
        abort(404)
    return _pdf(one, f"{plan.title.rsplit('.', 1)[0]} page {page}.pdf")
