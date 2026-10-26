"""Production's side of the one CalibraytAI identity (Joel, 26 Oct 2026). See app/services/identity.py.

PUBLIC (security route sweep) but never anonymous: every request must carry a known site's credentials
(Authorization: Bearer <client id>:<secret>, from IDENTITY_CLIENTS); otherwise 404 while not configured and 401
when wrong. No sign-in session, no CSRF token (server to server). Passwords are checked and set here only; nothing
here returns a password, a hash or a token, except the one-time set-password link the calling site shows its
owner (the same link an emailed invitation carries).
"""

from __future__ import annotations

import secrets
from datetime import datetime

from flask import Blueprint, abort, jsonify, request

from app import csrf, db

identity_api_bp = Blueprint("identity_api", __name__, url_prefix="/identity/api")


def _client():
    from app.services.identity import client_from_request, is_identity_provider

    if not is_identity_provider():
        abort(404)
    client = client_from_request(request)
    if client is None:
        abort(401)
    return client


def _body() -> dict:
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


def _user(email):
    from app.models.user import User
    from app.services.auth import AuthServiceError, normalize_email

    try:
        normalized = normalize_email(email)
    except AuthServiceError:
        return None, ""
    return User.query.filter_by(email=normalized).first(), normalized


def _iso(value):
    return value.isoformat(timespec="seconds") + "Z" if value else None


@identity_api_bp.route("/verify", methods=["POST"])
@csrf.exempt
def verify():
    """Is this the person's CalibraytAI password? Locks after 10 wrong tries in 15 minutes."""
    from app.services.auth import verify_password
    from app.services.identity import record_sign_in_failure, sign_in_locked

    _client()
    data = _body()
    user, normalized = _user(data.get("email"))
    if not normalized:
        return jsonify({"ok": False})
    if sign_in_locked(normalized):
        return jsonify({"ok": False, "locked": True})
    if user is None or not user.is_active or not verify_password(user.password_hash, data.get("password") or ""):
        record_sign_in_failure(normalized, str(data.get("client_ip") or ""))
        return jsonify({"ok": False})
    return jsonify({"ok": True, "name": user.display_name, "epoch": int(user.credentials_epoch or 0)})


@identity_api_bp.route("/change-password", methods=["POST"])
@csrf.exempt
def change_password():
    """The person's own change: the current password is required; every session for the account ends."""
    from app.services.auth import AuthServiceError, hash_password, validate_new_password, verify_password
    from app.services.identity import record_sign_in_failure, sign_in_locked

    _client()
    data = _body()
    user, normalized = _user(data.get("email"))
    if user is None or not user.is_active or sign_in_locked(normalized) or \
            not verify_password(user.password_hash, data.get("current_password") or ""):
        if normalized:
            record_sign_in_failure(normalized, "identity-change")
        return jsonify({"error": "The current password is not correct."}), 400
    try:
        validate_new_password(data.get("new_password") or "")
    except AuthServiceError as exc:
        return jsonify({"error": str(exc)}), 400
    user.password_hash = hash_password(data["new_password"])
    user.credentials_epoch = int(user.credentials_epoch or 0) + 1
    db.session.commit()
    return jsonify({"ok": True})


@identity_api_bp.route("/forgot", methods=["POST"])
@csrf.exempt
def forgot():
    """Forgot password started on another site: the same generic, rate-limited request as here."""
    from app.services.password_reset import PasswordResetServiceError, request_password_reset

    _client()
    data = _body()
    try:
        request_password_reset(str(data.get("email") or ""), client_ip=str(data.get("client_ip") or "") or None)
    except PasswordResetServiceError:
        pass
    return jsonify({"ok": True})


def _link_answer(outcome_path, expires_at, message):
    from app.services.email_delivery import state_of

    state = state_of(message) if message is not None else None
    return {"link_path": outcome_path, "expires_at": _iso(expires_at),
            "emailed": bool(state and state.code not in ("NOT_SENT",)),
            "email_state": state.label if state else "Not emailed"}


@identity_api_bp.route("/provision", methods=["POST"])
@csrf.exempt
def provision():
    """Another site added this person. Create their one identity if they have none (no Production access is
    given), invite them and return the link. An existing identity is never changed: {"existing": true}."""
    from app.models.transactional_message import TransactionalMessage
    from app.models.user import User
    from app.services.auth import hash_password
    from app.services.password_reset import PasswordResetServiceError, send_set_password_link

    client = _client()
    data = _body()
    user, normalized = _user(data.get("email"))
    if not normalized:
        return jsonify({"error": "That is not a valid email address."}), 400
    if user is not None:
        return jsonify({"existing": True, "active": bool(user.is_active), "name": user.display_name})
    name = (str(data.get("name") or "").strip() or normalized)[:150]
    user = User(email=normalized, display_name=name, password_hash=hash_password(secrets.token_urlsafe(32)),
                is_active=True)
    db.session.add(user)
    db.session.commit()
    invitation = {"company_name": (str(data.get("company") or "") or f"CalibraytAI ({client})")[:150],
                  "invited_by": str(data.get("invited_by") or "")[:150]}
    try:
        outcome = send_set_password_link(user, client_ip="identity-" + client, invitation=invitation)
    except PasswordResetServiceError:
        return jsonify({"created": True, "link_path": None, "emailed": False, "email_state": "Not emailed"})
    message = db.session.get(TransactionalMessage, outcome.message_id) if outcome.message_id else None
    return jsonify({"created": True, **_link_answer(outcome.path, outcome.expires_at, message)})


@identity_api_bp.route("/issue-link", methods=["POST"])
@csrf.exempt
def issue_link():
    """A new one-time set-password link for an existing identity, emailed or (send_email false) not."""
    from app.models.transactional_message import TransactionalMessage
    from app.services.password_reset import (
        BLOCK_RATE_LIMITED,
        PasswordResetServiceError,
        issue_link_without_email,
        send_set_password_link,
    )

    client = _client()
    data = _body()
    user, _normalized = _user(data.get("email"))
    if user is None or not user.is_active:
        return jsonify({"error": "No active CalibraytAI sign-in has that email address."}), 400
    if data.get("send_email", True) is False:
        path, expires_at = issue_link_without_email(user)
        return jsonify(_link_answer(path, expires_at, None))
    try:
        outcome = send_set_password_link(user, client_ip="identity-" + client)
    except PasswordResetServiceError as exc:
        return jsonify({"error": "Several links were already sent to this address in the last hour. Try later."
                        if exc.code == BLOCK_RATE_LIMITED else "This sign-in is deactivated."}), 400
    message = db.session.get(TransactionalMessage, outcome.message_id) if outcome.message_id else None
    return jsonify(_link_answer(outcome.path, outcome.expires_at, message))


@identity_api_bp.route("/email-history", methods=["POST"])
@csrf.exempt
def email_history():
    """The last sign-in emails to this person and what the mail service reported (optionally checked now)."""
    from app.routes.people_access import EMAIL_KINDS, _email_rows
    from app.services.email_delivery import check_waiting, state_of

    _client()
    data = _body()
    rows = _email_rows(str(data.get("email") or ""), 5)
    problem = None
    if data.get("check"):
        _added, problem = check_waiting(rows)
    return jsonify({"problem": problem, "emails": [
        {"at": _iso(r.created_at), "kind": EMAIL_KINDS.get(r.template_id, r.template_id.replace("_", " ").title()),
         "state": state_of(r).code, "label": state_of(r).label, "checkable": state_of(r).checkable} for r in rows]})


@identity_api_bp.route("/import", methods=["POST"])
@csrf.exempt
def import_identity():
    """One-time reconciliation: a person who so far existed only on the calling site keeps the password they
    already chose there. Only when Production has no identity for the address; an existing one always wins."""
    from app.models.user import User

    _client()
    data = _body()
    user, normalized = _user(data.get("email"))
    password_hash = str(data.get("password_hash") or "")
    if not normalized or not password_hash.startswith(("pbkdf2:", "scrypt:")):
        return jsonify({"error": "Not an importable identity."}), 400
    if user is not None:
        return jsonify({"existing": True})
    db.session.add(User(email=normalized, display_name=(str(data.get("name") or "") or normalized)[:150],
                        password_hash=password_hash, is_active=True, created_at=datetime.utcnow()))
    db.session.commit()
    return jsonify({"created": True})


@identity_api_bp.route("/lookup", methods=["POST"])
@csrf.exempt
def lookup():
    """Reconciliation report: for each address, whether Production has an identity and whether it gives any
    Production access (a contractor or supplier membership). Never returns a password or hash."""
    from app.services.supplier_hub import principal_class

    _client()
    out = {}
    for email in (_body().get("emails") or [])[:500]:
        user, normalized = _user(email)
        if not normalized:
            continue
        if user is None:
            out[normalized] = {"exists": False}
            continue
        out[normalized] = {"exists": True, "active": bool(user.is_active),
                           "production_access": principal_class(user) is not None}
    return jsonify({"people": out})
