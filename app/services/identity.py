"""One CalibraytAI identity across Production and the Training Centre (Joel, 26 Oct 2026).

Before: Production (Render) and the Training Centre (HostPapa) were two copies of CalibraytAI, each with its own
users table and its own password hashes, and nothing connected them. A password set on one meant nothing on the
other.

Now: Production is the one place a real person's password lives (the identity provider). The Training Centre is a
client of it. On the Training Centre, for a real person (any address not ending in ".invalid"):

- signing in checks the email and password with Production (server to server, over HTTPS);
- Change password and Forgot password are done by Production, so the new password works on both at once;
- adding a person creates their one identity on Production if they do not have one yet (never touching an
  existing one), and the one-time set-password link the owner gets (Copy / Text it) is Production's.

What each person may do stays with each site: a Training Centre account (company, Field only, training
administrator) is still the Training Centre's own record, and a Production membership is Production's. An identity
with no Production membership (a reviewer such as Kevin) can set and use its password but cannot open Production.

Practice personas on the Training Centre ("… (training)" people, the synthetic supplier staff) have addresses ending
in ".invalid"; they are not people, keep their local passwords and never reach Production.

Settings (never in code; see docs/operations/sign-in-and-email.md):
- Production: IDENTITY_CLIENTS = "training=<long random secret>", IDENTITY_TRAINING_SITE_URL =
  https://training.calibraytai.com (only for the "also works on the Training Centre" link).
- Training Centre: IDENTITY_PROVIDER_URL = https://calibryatai.onrender.com, IDENTITY_CLIENT_ID = training,
  IDENTITY_CLIENT_SECRET = the same secret. Unset = the Training Centre signs in locally, as before (the documented
  break-glass if Production is unreachable).
"""

from __future__ import annotations

import hmac
import json
import os
import urllib.error
import urllib.request
from typing import Optional

from flask import current_app

LOCAL_ONLY_SUFFIX = ".invalid"
SIGN_IN_FAILURE_OUTCOME = "SIGNIN_FAIL"
SIGN_IN_LOCK_LIMIT = 10
SIGN_IN_LOCK_WINDOW_SECONDS = 15 * 60


class IdentityUnavailable(RuntimeError):
    """Production could not be asked (network, not set up, or it refused this site's credentials)."""


class IdentityRefused(ValueError):
    """Production answered, and said no (with a message that is safe to show)."""


def _setting(name: str) -> str:
    value = current_app.config.get(name)
    if value is None:
        value = os.environ.get(name, "")
    return str(value or "").strip()


# ------------------------------------------------------------------ which side this server is


def provider_clients() -> dict:
    """Production: {client id: secret} from IDENTITY_CLIENTS ("training=secret,other=secret")."""
    out = {}
    for part in _setting("IDENTITY_CLIENTS").split(","):
        name, _, secret = part.strip().partition("=")
        if name.strip() and len(secret.strip()) >= 32:
            out[name.strip()] = secret.strip()
    return out


def is_identity_provider() -> bool:
    return bool(provider_clients())


def is_identity_client() -> bool:
    return bool(_setting("IDENTITY_PROVIDER_URL") and _setting("IDENTITY_CLIENT_SECRET"))


def local_only(email: str) -> bool:
    return (email or "").strip().lower().endswith(LOCAL_ONLY_SUFFIX)


def federated(email: str) -> bool:
    """This server signs this address in through Production."""
    return is_identity_client() and not local_only(email)


def provider_url() -> str:
    return _setting("IDENTITY_PROVIDER_URL").rstrip("/")


def training_site_url() -> str:
    return _setting("IDENTITY_TRAINING_SITE_URL").rstrip("/")


def client_from_request(request) -> Optional[str]:
    """Production: which known site is calling (Authorization: Bearer <client id>:<secret>). Constant-time."""
    clients = provider_clients()
    header = request.headers.get("Authorization", "")
    if not clients or not header.startswith("Bearer "):
        return None
    client_id, _, secret = header[len("Bearer "):].partition(":")
    expected = clients.get(client_id.strip())
    if expected is None:
        hmac.compare_digest(secret.encode(), b"x" * 40)
        return None
    return client_id.strip() if hmac.compare_digest(secret.encode(), expected.encode()) else None


# ------------------------------------------------------------------ the Training Centre asks Production


def _call(action: str, payload: dict) -> dict:
    transport = current_app.config.get("IDENTITY_TRANSPORT")  # tests: callable(action, payload) -> (status, body)
    if transport is not None:
        status, body = transport(action, dict(payload))
    else:
        url = f"{provider_url()}/identity/api/{action}"
        client_id = _setting("IDENTITY_CLIENT_ID") or "training"
        request = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), method="POST", headers={
            "Content-Type": "application/json", "Accept": "application/json",
            "Authorization": f"Bearer {client_id}:{_setting('IDENTITY_CLIENT_SECRET')}"})
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                status, body = response.status, json.loads((response.read() or b"{}").decode("utf-8"))
        except urllib.error.HTTPError as exc:
            try:
                status, body = exc.code, json.loads((exc.read() or b"{}").decode("utf-8"))
            except ValueError:
                status, body = exc.code, {}
        except (OSError, ValueError) as exc:
            raise IdentityUnavailable("CalibraytAI sign-in could not be reached.") from exc
    if status in (401, 403, 404):
        raise IdentityUnavailable("This site is not connected to CalibraytAI sign-in.")
    if status >= 500:
        raise IdentityUnavailable("CalibraytAI sign-in is not answering right now.")
    if status == 400 and body.get("error"):
        raise IdentityRefused(str(body["error"]))
    return body or {}


def remote_verify(email: str, password: str, client_ip: str = "") -> dict:
    return _call("verify", {"email": email, "password": password, "client_ip": client_ip})


def remote_change_password(email: str, current: str, new: str) -> dict:
    return _call("change-password", {"email": email, "current_password": current, "new_password": new})


def remote_forgot(email: str, client_ip: str = "") -> dict:
    return _call("forgot", {"email": email, "client_ip": client_ip})


def remote_provision(email: str, name: str, *, invited_by: str = "", company: str = "") -> dict:
    return _call("provision", {"email": email, "name": name, "invited_by": invited_by, "company": company})


def remote_issue_link(email: str, *, send_email: bool = True, invited_by: str = "", company: str = "") -> dict:
    return _call("issue-link", {"email": email, "send_email": send_email, "invited_by": invited_by,
                                "company": company})


def remote_email_history(email: str, *, check: bool = False) -> dict:
    return _call("email-history", {"email": email, "check": check})


def remote_lookup(emails) -> dict:
    return _call("lookup", {"emails": list(emails)}).get("people") or {}


def remote_import(email: str, name: str, password_hash: str) -> dict:
    return _call("import", {"email": email, "name": name, "password_hash": password_hash})


# ------------------------------------------------------------------ Production answers


def _email_key(email: str) -> str:
    from app.services.password_reset import hash_email_key

    return hash_email_key((email or "").strip().lower())


def sign_in_locked(email: str) -> bool:
    from datetime import datetime, timedelta

    from app.models.password_reset import PasswordResetAccessAttempt

    since = datetime.utcnow() - timedelta(seconds=SIGN_IN_LOCK_WINDOW_SECONDS)
    count = (PasswordResetAccessAttempt.query.filter(
        PasswordResetAccessAttempt.email_key_hash == _email_key(email),
        PasswordResetAccessAttempt.outcome == SIGN_IN_FAILURE_OUTCOME,
        PasswordResetAccessAttempt.created_at >= since).count())
    return count >= SIGN_IN_LOCK_LIMIT


def record_sign_in_failure(email: str, client_ip: str = "") -> None:
    from datetime import datetime

    from app import db
    from app.models.password_reset import PasswordResetAccessAttempt

    db.session.add(PasswordResetAccessAttempt(client_ip=(client_ip or "identity")[:64], email_key_hash=_email_key(email),
                                              outcome=SIGN_IN_FAILURE_OUTCOME, created_at=datetime.utcnow()))
    db.session.commit()
