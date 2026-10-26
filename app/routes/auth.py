"""Office login, logout, and Account Recovery browser routes (FG-018 / FG-034 AUTH-B)."""

from urllib.parse import urlparse

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user

from app.presentation import contractor_copy
from app.services.auth import GENERIC_LOGIN_FAILURE, authenticate, sign_in

SIGN_IN_MESSAGES = {
    "locked": "Too many wrong passwords for this email. Wait 15 minutes, or use Forgot password.",
    "no_access": "Your CalibraytAI email and password are right, but this site has not given you access. "
                 "Ask the person who invited you.",
    "unavailable": "CalibraytAI sign-in is not answering right now. Try again in a minute.",
}


def _no_access_here_message():
    """Production (26 Oct 2026): an identity with no membership here, e.g. a Training Centre reviewer."""
    from app.services.identity import training_site_url

    site = training_site_url()
    return ("Your CalibraytAI email and password are right, but they give no access to this site."
            + (f" Reviewers and trainees: sign in to the Training Centre at {site} with the same email and password."
               if site else " Ask the person who invited you."))
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
    from app.training.service import enabled as training_site

    # On the training site everyone lands in their training (21 Oct 2026); elsewhere, Home.
    default = url_for("training.home") if training_site() else url_for("main.dashboard")
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
        from app.services.identity import is_identity_provider
        from app.services.supplier_hub import principal_class

        user, outcome = sign_in(
            request.form.get("email", ""),
            request.form.get("password", ""),
            client_ip=_client_ip(),
        )
        if user is not None and is_identity_provider() and principal_class(user) is None:
            user, message = None, _no_access_here_message()
        else:
            message = SIGN_IN_MESSAGES.get(outcome, GENERIC_LOGIN_FAILURE)
        if user is None:
            flash(message, "error")
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


def _recovery_portal():
    """Supplier staff who start from the supplier sign-in return to it (Joel, 17 Oct 2026)."""
    return "supplier" if (request.values.get("portal") or "") == "supplier" else ""


def _sign_in_url(portal):
    return url_for("supplier_portal.login") if portal == "supplier" else url_for("auth.login")


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    portal = _recovery_portal()
    if request.method == "POST":
        from app.services.identity import IdentityRefused, IdentityUnavailable, is_identity_client, local_only, remote_forgot

        email = request.form.get("email", "")
        if is_identity_client() and not local_only(email):
            # One CalibraytAI identity (26 Oct 2026): Production sends the link; the new password works everywhere.
            try:
                remote_forgot(email, _client_ip())
            except (IdentityUnavailable, IdentityRefused):
                flash(SIGN_IN_MESSAGES["unavailable"], "error")
                return render_template("auth/forgot.html", portal=portal, sign_in_url=_sign_in_url(portal),
                                       email_ready=True)
            return redirect(url_for("auth.forgot_password_sent", portal=portal or None))
        try:
            request_password_reset(email, client_ip=_client_ip())
        except PasswordResetServiceError:
            pass
        return redirect(url_for("auth.forgot_password_sent", portal=portal or None))
    return render_template("auth/forgot.html", portal=portal, sign_in_url=_sign_in_url(portal),
                           email_ready=_email_ready())


@auth_bp.route("/forgot-password/sent", methods=["GET"])
def forgot_password_sent():
    portal = _recovery_portal()
    return render_template("auth/forgot_sent.html", sign_in_url=_sign_in_url(portal), portal=portal,
                           email_ready=_email_ready())


def _email_ready() -> bool:
    """Whether this site can email a reset link at all (says nothing about any account). A Training Centre
    connected to CalibraytAI sign-in has Production send it (26 Oct 2026)."""
    from app.services.identity import is_identity_client
    from app.services.transactional_email import email_delivery_configured

    return is_identity_client() or email_delivery_configured()


@auth_bp.route("/reset-password/complete", methods=["GET"])
def reset_password_complete():
    # A supplier's sign-in is the Supplier Hub's (21 Oct 2026); the query only chooses which sign-in link to show.
    from app.services.identity import training_site_url

    return render_template("auth/reset_complete.html", supplier=request.args.get("side") == "supplier",
                           training_url=training_site_url())


@auth_bp.route("/reset-password", methods=["GET", "POST"])
def reset_password_form():
    """The set-password link lands here with the credential after "#" (never sent to the server, so never
    logged). GET: a page whose script moves the credential into a form and posts it. POST "open": check
    the credential and show the password form. POST with a password: set it (the credential stays in the
    form body, never in the address)."""
    if request.method == "GET":
        return render_template("auth/reset_open.html")
    credential = (request.form.get("credential") or "").strip()
    if request.form.get("step") == "open":
        try:
            validate_password_reset_credential(credential, client_ip=_client_ip())
        except PasswordResetServiceError:
            return render_template("auth/reset_invalid.html")
        return _no_store(render_template("auth/reset.html", credential=credential, form_error=None))
    return reset_password(credential)


def _no_store(body):
    return body, 200, {"Cache-Control": "no-store", "Referrer-Policy": "no-referrer"}


@auth_bp.route("/reset-password/<credential>", methods=["GET", "POST"])
def reset_password(credential):
    if request.method == "POST":
        try:
            reset_user = complete_password_reset(
                credential,
                request.form.get("password", ""),
                confirm_password=request.form.get("confirm_password", ""),
                client_ip=_client_ip(),
            )
        except PasswordResetServiceError as exc:
            form_error = _password_form_error(exc)
            if form_error is None:
                return render_template("auth/reset_invalid.html")
            return _no_store(render_template(
                "auth/reset.html",
                credential=credential,
                form_error=form_error,
            ))
        from app.services.supplier_hub import principal_class

        if principal_class(reset_user) == "SUPPLIER":
            return redirect(url_for("auth.reset_password_complete", side="supplier"))
        return redirect(url_for("auth.reset_password_complete"))
    try:
        validate_password_reset_credential(credential, client_ip=_client_ip())
    except PasswordResetServiceError:
        return render_template("auth/reset_invalid.html")
    return render_template("auth/reset.html", credential=credential, form_error=None)


@auth_bp.route("/account/password", methods=["GET", "POST"])
def change_password():
    """A signed-in person sets their own password.

    The current password is always required. Other sessions for the account end.
    (The temporary UAT sign-in bypass, and its exception here, were removed on
    18 Oct 2026.)
    """
    from app import db
    from app.services.auth import (
        AuthServiceError,
        hash_password,
        validate_new_password,
        verify_password,
    )

    if not current_user.is_authenticated:
        return redirect(url_for("auth.login", next=request.path))
    error = None
    if request.method == "POST":
        current = request.form.get("current_password") or ""
        new = request.form.get("password") or ""
        confirm = request.form.get("confirm_password") or ""
        from app.services.identity import IdentityRefused, IdentityUnavailable, federated, remote_change_password

        remote = federated(current_user.email)
        try:
            if new != confirm:
                raise AuthServiceError("The new password and confirmation do not match.")
            validate_new_password(new)
            if remote:
                # One CalibraytAI identity (26 Oct 2026): Production checks and sets it, so it works everywhere.
                try:
                    remote_change_password(current_user.email, current, new)
                except IdentityRefused as exc:
                    raise AuthServiceError(str(exc)) from exc
                except IdentityUnavailable as exc:
                    raise AuthServiceError(SIGN_IN_MESSAGES["unavailable"]) from exc
            elif not verify_password(current_user.password_hash, current):
                raise AuthServiceError("The current password is not correct.")
        except AuthServiceError as exc:
            error = str(exc)
        else:
            user = current_user._get_current_object()
            if not remote:
                user.password_hash = hash_password(new)
            user.credentials_epoch = int(user.credentials_epoch or 0) + 1
            db.session.commit()
            logout_user()
            flash("Your password is changed. Sign in with your email and the new password.", "success")
            return redirect(url_for("auth.login"))
    return render_template(
        "auth/change_password.html",
        error=error,
        email=current_user.email,
    )
