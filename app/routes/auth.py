"""Office login and logout routes (FG-018)."""

from urllib.parse import urlparse

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user

from app.services.auth import GENERIC_LOGIN_FAILURE, authenticate

auth_bp = Blueprint("auth", __name__)


def safe_next_url(target):
    """Allow only relative same-host paths. Reject open redirects."""
    default = url_for("main.dashboard")
    if not target:
        return default
    candidate = target.strip()
    if not candidate.startswith("/") or candidate.startswith("//") or "\\" in candidate:
        return default
    parsed = urlparse(candidate)
    if parsed.scheme or parsed.netloc:
        return default
    return candidate


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(safe_next_url(request.args.get("next")))

    if request.method == "POST":
        user = authenticate(
            request.form.get("email", ""),
            request.form.get("password", ""),
        )
        if user is None:
            flash(GENERIC_LOGIN_FAILURE, "error")
            return render_template("auth/login.html")
        login_user(user, remember=False)
        return redirect(safe_next_url(request.form.get("next") or request.args.get("next")))

    return render_template("auth/login.html")


@auth_bp.route("/logout", methods=["POST"])
def logout():
    if current_user.is_authenticated:
        logout_user()
    return redirect(url_for("auth.login"))
