"""Office login, logout, and Account Recovery browser routes (FG-018 / FG-034 AUTH-B)."""

from urllib.parse import urlparse

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user

from app.presentation import contractor_copy
from app.services.auth import GENERIC_LOGIN_FAILURE, authenticate
from app.services.opening_v1 import opening_v1_config
from app.services.password_reset import (
    BLOCK_PASSWORD_MISMATCH,
    PasswordResetServiceError,
    complete_password_reset,
    request_password_reset,
    validate_password_reset_credential,
)

auth_bp = Blueprint("auth", __name__)

GENERIC_RESET_SENT = contractor_copy.FORGOT_PASSWORD_SENT_BODY


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


def _client_ip():
    return (request.remote_addr or "").strip() or "unknown"


def _password_form_error(exc: PasswordResetServiceError):
    if exc.code == BLOCK_PASSWORD_MISMATCH:
        return "The new password and confirmation do not match."
    if exc.code in ("Password is required.", "Password must be at least 8 characters."):
        return exc.code
    return None


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
            return render_template(
                "auth/login.html",
                opening_v1=opening_v1_config(url_for),
            )
        login_user(user, remember=False)
        return redirect(safe_next_url(request.form.get("next") or request.args.get("next")))

    return render_template(
        "auth/login.html",
        opening_v1=opening_v1_config(url_for),
    )


@auth_bp.route("/logout", methods=["POST"])
def logout():
    if current_user.is_authenticated:
        logout_user()
    return redirect(url_for("auth.login"))


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        try:
            request_password_reset(request.form.get("email", ""), client_ip=_client_ip())
        except PasswordResetServiceError:
            pass
        return redirect(url_for("auth.forgot_password_sent"))
    return render_template("auth/forgot.html")


@auth_bp.route("/forgot-password/sent", methods=["GET"])
def forgot_password_sent():
    return render_template("auth/forgot_sent.html")


@auth_bp.route("/reset-password/complete", methods=["GET"])
def reset_password_complete():
    return render_template("auth/reset_complete.html")


@auth_bp.route("/reset-password/<credential>", methods=["GET", "POST"])
def reset_password(credential):
    if request.method == "POST":
        try:
            complete_password_reset(
                credential,
                request.form.get("password", ""),
                confirm_password=request.form.get("confirm_password", ""),
                client_ip=_client_ip(),
            )
        except PasswordResetServiceError as exc:
            form_error = _password_form_error(exc)
            if form_error is None:
                return render_template("auth/reset_invalid.html")
            return render_template(
                "auth/reset.html",
                credential=credential,
                form_error=form_error,
            )
        return redirect(url_for("auth.reset_password_complete"))
    try:
        validate_password_reset_credential(credential, client_ip=_client_ip())
    except PasswordResetServiceError:
        return render_template("auth/reset_invalid.html")
    return render_template("auth/reset.html", credential=credential, form_error=None)
