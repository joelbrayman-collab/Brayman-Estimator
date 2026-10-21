"""Getting started: Ben's First Day guided checklist (Joel, 21 Oct 2026). Office users of the organization."""

from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user

from app.services.onboarding import OnboardingError, checklist, mark_step
from app.services.organizations import get_current_organization_id

getting_started_bp = Blueprint("getting_started", __name__, url_prefix="/getting-started")


@getting_started_bp.route("")
def index():
    return render_template("getting_started/index.html", c=checklist(get_current_organization_id(), current_user))


@getting_started_bp.route("/steps/<key>", methods=["POST"])
def mark(key):
    try:
        mark_step(get_current_organization_id(), current_user, key, request.form.get("done") == "yes")
    except OnboardingError:
        flash("That step is not on the checklist.", "error")
    return redirect(url_for("getting_started.index") + f"#step-{key}")
