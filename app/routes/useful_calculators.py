"""Useful Calculators: the phone dashboard and Home Screen app (Joel, 22 Oct 2026).

Its own address space, /useful-calculators/, is the Home Screen app's scope (manifest
app/static/useful-calculators/manifest.webmanifest), separate from CalibraytAI Field (scope "/", start "/",
app/static/manifest.webmanifest and /field-sw.js, all unchanged). No service worker of its own: nothing here is
claimed to work offline.

- index: public. Signed out it shows the public calculators and a sign-in; signed in it shows every calculator
  the person may open (app/services/useful_calculators.py) and names the others with the reason.
- sign_in: public. The same check as the office sign-in (app/services/auth.authenticate), kept inside the
  app's scope so the Home Screen app signs in and comes straight back here.
- The calculator pages are the existing views from app/routes/calculators.py, served again here with the phone
  layout (no engine is copied). The office wall (app/__init__.py) treats them like any office page; only the
  quantity-only ones are on the Field-only allow list (app/services/access_domains.py).
- projects: office only. Choose a job, then open its estimate or project calculators in the office.
"""

from __future__ import annotations

from urllib.parse import urlparse

from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user

from app.routes import calculators as calc_views
from app.services import useful_calculators as UC

useful_calculators_bp = Blueprint("useful_calculators", __name__, url_prefix="/useful-calculators")

SCOPE = "/useful-calculators/"
LAYOUT = "useful_calculators/calculator_layout.html"


def _organization_id():
    from app.services.organizations import OrganizationAccessError, resolve_membership_organization_id

    if not current_user.is_authenticated:
        return None
    try:
        return resolve_membership_organization_id(current_user)
    except OrganizationAccessError:
        return None


def _kind():
    return UC.viewer_kind(current_user, _organization_id())


def safe_return(target):
    """Only a path inside this app; anything else returns to the dashboard."""
    default = url_for("useful_calculators.index")
    candidate = (target or "").strip()
    if not candidate.startswith(SCOPE) or candidate.startswith("//") or "\\" in candidate:
        return default
    parsed = urlparse(candidate)
    if parsed.scheme or parsed.netloc:
        return default
    return candidate


@useful_calculators_bp.app_context_processor
def _calculator_layout():
    """The calculator templates extend the phone layout when served from here, the office shell otherwise."""
    if request and request.blueprint == "useful_calculators":
        from app import login_manager

        # flask-login's office wording ("...the office application") is not shown on these pages.
        return {"calculator_layout": LAYOUT, "uc_hidden_messages": (login_manager.login_message,)}
    return {}


@useful_calculators_bp.get("/")
def index():
    kind = _kind()
    return render_template(
        "useful_calculators/index.html",
        kind=kind,
        groups=UC.dashboard(kind),
        project_reason=UC.PROJECT_REASON,
    )


@useful_calculators_bp.route("/sign-in", methods=["GET", "POST"])
def sign_in():
    from app.services.auth import GENERIC_LOGIN_FAILURE, authenticate

    target = safe_return(request.values.get("next"))
    if current_user.is_authenticated:
        return redirect(target)
    if request.method == "POST":
        user = authenticate(request.form.get("email", ""), request.form.get("password", ""))
        if user is None:
            flash(GENERIC_LOGIN_FAILURE, "error")
            return render_template("useful_calculators/sign_in.html", next_path=target), 200
        login_user(user, remember=False)
        return redirect(target)
    return render_template("useful_calculators/sign_in.html", next_path=target)


@useful_calculators_bp.post("/sign-out")
def sign_out():
    if current_user.is_authenticated:
        logout_user()
    return redirect(url_for("useful_calculators.index"))


@useful_calculators_bp.get("/projects")
def projects():
    """Office only: the field-only wall sends crew to Field before this runs; checked again here."""
    if getattr(g, "field_only", False) or _kind() != "office":
        abort(403)
    return render_template(
        "useful_calculators/projects.html",
        rows=UC.project_tool_links(g.organization_id),
        project_reason=UC.PROJECT_REASON,
    )


# The result panel (Use Result Only / Add to Existing Project / Create New Project) for office people on the phone app
# too (Guided Estimating, 23 Oct 2026); the crew sees the result alone.
useful_calculators_bp.context_processor(calc_views.result_options_context)
useful_calculators_bp.before_request(calc_views.restore_carried_result)

# The existing calculator views, unchanged, under this app's scope.
_SAME_VIEWS = (
    ("/concrete", "concrete", calc_views.concrete, ["GET"]),
    ("/stairs", "stairs", calc_views.stairs, ["GET"]),
    ("/wall-form", "wall_form", calc_views.wall_form, ["GET", "POST"]),
    ("/wall-framing", "wall_framing", calc_views.wall_framing, ["GET", "POST"]),
    ("/footing", "footing", calc_views.footing, ["GET", "POST"]),
    ("/roofing", "roofing", calc_views.roofing, ["GET", "POST"]),
    ("/siding", "siding", calc_views.siding, ["GET", "POST"]),
    ("/drywall", "drywall", calc_views.drywall, ["GET", "POST"]),
    ("/flooring", "flooring", calc_views.flooring, ["GET", "POST"]),
)
for _rule, _endpoint, _view, _methods in _SAME_VIEWS:
    useful_calculators_bp.add_url_rule(_rule, endpoint=_endpoint, view_func=_view, methods=_methods)

PHONE_CALCULATOR_ENDPOINTS = frozenset(f"useful_calculators.{endpoint}" for _r, endpoint, _v, _m in _SAME_VIEWS)
