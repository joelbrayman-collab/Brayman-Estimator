"""Sign out office and supplier accounts after 30 minutes without activity (Joel, 18 Oct 2026).

The limit is measured from the last request (or keep-alive) the person made, never from when they
signed in, so someone who keeps working is never signed out. Pages show a warning shortly before
the limit (static/js/session-timeout.js) and keep what was typed in a form if the time runs out.

Customers on signing and proposal links have no account and are not affected.
"""

from __future__ import annotations

import time

from flask import current_app, flash, jsonify, redirect, request, session, url_for
from flask_login import current_user, logout_user

SESSION_LAST_ACTIVITY_KEY = "last_activity_at"
DEFAULT_IDLE_TIMEOUT_SECONDS = 30 * 60
DEFAULT_WARNING_SECONDS = 2 * 60
# Save the time at most every 10 s, so the session cookie is not rewritten on every request
# (the limit is therefore exact to within 10 s).
TOUCH_INTERVAL_SECONDS = 10

IDLE_SIGNED_OUT_MESSAGE = "You were signed out after 30 minutes without activity. Sign in to continue."

# The status check must not count as activity, or an open tab would never time out.
STATUS_ENDPOINT = "session_status.status"
# Sign-in and sign-out pages: after an idle sign-out the page itself is shown, not redirected.
_SIGN_IN_ENDPOINTS = frozenset(
    {
        "auth.login",
        "auth.logout",
        "supplier_portal.login",
        "supplier_portal.logout",
        "useful_calculators.sign_in",  # the Useful Calculators Home Screen app's own sign-in (22 Oct 2026)
    }
)


def idle_timeout_seconds() -> int:
    return int(current_app.config.get("SESSION_IDLE_TIMEOUT_SECONDS", DEFAULT_IDLE_TIMEOUT_SECONDS))


def warning_seconds() -> int:
    return int(current_app.config.get("SESSION_IDLE_WARNING_SECONDS", DEFAULT_WARNING_SECONDS))


def _now() -> float:
    return time.time()


def mark_activity(now: float | None = None) -> None:
    session[SESSION_LAST_ACTIVITY_KEY] = float(now if now is not None else _now())


def seconds_remaining(now: float | None = None) -> float:
    now = now if now is not None else _now()
    last = session.get(SESSION_LAST_ACTIVITY_KEY)
    if last is None:
        return float(idle_timeout_seconds())
    return max(0.0, idle_timeout_seconds() - (now - float(last)))


def _is_supplier() -> bool:
    from app.services.supplier_hub import principal_class

    try:
        return principal_class(current_user) == "SUPPLIER"
    except Exception:  # pragma: no cover - never let the check itself break a request
        return False


def _sign_in_url(supplier: bool, next_path: str | None):
    endpoint = "supplier_portal.login" if supplier else "auth.login"
    # Useful Calculators (22 Oct 2026): its pages sign in again inside the Home Screen app's own scope.
    if not supplier and request.blueprint == "useful_calculators":
        endpoint = "useful_calculators.sign_in"
    if next_path:
        return url_for(endpoint, next=next_path)
    return url_for(endpoint)


def enforce_idle_timeout():
    """before_request: sign out an account that has been idle too long; otherwise record activity."""
    endpoint = request.endpoint
    if endpoint == "static" or not current_user.is_authenticated:
        return None
    now = _now()
    last = session.get(SESSION_LAST_ACTIVITY_KEY)
    if last is not None and now - float(last) >= idle_timeout_seconds():
        supplier = _is_supplier()
        logout_user()
        session.pop(SESSION_LAST_ACTIVITY_KEY, None)
        current_app.logger.info("Signed out after %s s without activity", idle_timeout_seconds())
        # Shown on the sign-in page whichever request noticed the time was up (often the page's
        # own status check, just before it goes to sign-in).
        flash(IDLE_SIGNED_OUT_MESSAGE, "info")
        if endpoint == STATUS_ENDPOINT:
            return jsonify({"signed_in": False, "remaining": 0})
        path = request.path or ""
        if path == "/api" or path.startswith("/api/") or path.startswith("/session/"):
            return (
                jsonify({"error": IDLE_SIGNED_OUT_MESSAGE, "session_expired": True, "signed_in": False}),
                401,
            )
        if endpoint in _SIGN_IN_ENDPOINTS:
            return None
        next_path = request.full_path.rstrip("?") if request.method == "GET" else None
        return redirect(_sign_in_url(supplier, next_path))
    if endpoint == STATUS_ENDPOINT:
        return None
    if last is None or now - float(last) >= TOUCH_INTERVAL_SECONDS:
        mark_activity(now)
    return None


def page_settings():
    """What session-timeout.js needs; None when nobody is signed in."""
    if not current_user.is_authenticated:
        return None
    supplier = _is_supplier()
    return {
        "timeout": idle_timeout_seconds(),
        "warning": warning_seconds(),
        "status_url": url_for("session_status.status"),
        "keepalive_url": url_for("session_status.keepalive"),
        "login_url": _sign_in_url(supplier, None),
        "user": str(getattr(current_user, "id", "") or ""),
    }
