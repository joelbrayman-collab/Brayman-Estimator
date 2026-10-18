"""Session time left, and keep-alive, for the inactivity warning (static/js/session-timeout.js).

Both answer for office and supplier accounts. The status check never counts as activity; the
keep-alive does (the person clicked "Stay signed in" or is typing).
"""

from __future__ import annotations

import math

from flask import Blueprint, jsonify
from flask_login import current_user

from app.services.session_timeout import idle_timeout_seconds, mark_activity, seconds_remaining

session_status_bp = Blueprint("session_status", __name__, url_prefix="/session")


@session_status_bp.route("/status", methods=["GET"])
def status():
    if not current_user.is_authenticated:
        return jsonify({"signed_in": False, "remaining": 0})
    # Rounded up, so 0 means the time is really over (the next request signs out).
    response = jsonify({"signed_in": True, "remaining": int(math.ceil(seconds_remaining()))})
    response.headers["Cache-Control"] = "no-store"
    return response


@session_status_bp.route("/keepalive", methods=["POST"])
def keepalive():
    if not current_user.is_authenticated:
        return jsonify({"signed_in": False, "remaining": 0}), 401
    mark_activity()
    response = jsonify({"signed_in": True, "remaining": idle_timeout_seconds()})
    response.headers["Cache-Control"] = "no-store"
    return response
