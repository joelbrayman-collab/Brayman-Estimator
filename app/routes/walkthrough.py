"""FG-035 CORE CLOSE C2 — public client Final Walkthrough.

Narrow /walkthrough/* exemption. No office chrome. No Field chrome.
No client account. Token grants this page only.
"""

from __future__ import annotations

from flask import Blueprint, render_template, request

from app.models.final_walkthrough import WALKTHROUGH_STATUS_RESPONDED
from app.presentation import contractor_copy
from app.services.project_final_walkthrough import (
    BLOCK_TOKEN_CONSUMED,
    BLOCK_TOKEN_EXPIRED,
    BLOCK_TOKEN_INVALID,
    BLOCK_TOKEN_RATE_LIMITED,
    WalkthroughError,
    WalkthroughTokenError,
    resolve_walkthrough_access,
    submit_walkthrough_response,
    walkthrough_public_identity,
)

walkthrough_bp = Blueprint("walkthrough", __name__, url_prefix="/walkthrough")


def _client_ip():
    return request.remote_addr or "unknown"


def _fail_closed(code: str, *, status_code=None):
    status = status_code
    if status is None:
        if code == BLOCK_TOKEN_RATE_LIMITED:
            status = 429
        elif code == BLOCK_TOKEN_EXPIRED:
            status = 410
        elif code == BLOCK_TOKEN_CONSUMED:
            status = 409
        else:
            status = 404
    return (
        render_template(
            "walkthrough/unavailable.html",
            code=code,
            rate_limited=code == BLOCK_TOKEN_RATE_LIMITED,
        ),
        status,
    )


def _form_context(access, *, credential, error=None):
    identity = walkthrough_public_identity(access)
    return {
        "credential": credential,
        "company_name": identity["company_name"],
        "project_name": identity["project_name"],
        "client_name": identity["client_name"],
        "error": error,
        "nothing_to_add_label": contractor_copy.WALKTHROUGH_NOTHING_TO_ADD,
        "heading": contractor_copy.WALKTHROUGH_CLIENT_HEADING,
        "lede": contractor_copy.WALKTHROUGH_CLIENT_LEDE,
        "what_needs_attention": contractor_copy.WALKTHROUGH_WHAT_NEEDS_ATTENTION,
        "add_another": contractor_copy.WALKTHROUGH_ADD_ANOTHER,
        "submit_label": contractor_copy.WALKTHROUGH_SUBMIT,
        "received_label": contractor_copy.WALKTHROUGH_RECEIVED,
        "responded": access.invitation.status == WALKTHROUGH_STATUS_RESPONDED,
        "response_mode": access.invitation.response_mode,
    }


@walkthrough_bp.route("/<credential>", methods=["GET"])
def form(credential):
    try:
        access = resolve_walkthrough_access(
            credential,
            client_ip=_client_ip(),
            allow_responded=True,
        )
    except WalkthroughTokenError as exc:
        return _fail_closed(exc.code)
    return render_template(
        "walkthrough/form.html",
        **_form_context(access, credential=credential),
    )


@walkthrough_bp.route("/<credential>", methods=["POST"])
def submit(credential):
    try:
        access = resolve_walkthrough_access(
            credential,
            client_ip=_client_ip(),
            allow_responded=False,
        )
    except WalkthroughTokenError as exc:
        return _fail_closed(exc.code)
    nothing_to_add = (request.form.get("nothing_to_add") or "").strip() == "1"
    items = request.form.getlist("item")
    try:
        submit_walkthrough_response(
            access,
            nothing_to_add=nothing_to_add,
            item_descriptions=items,
        )
    except WalkthroughTokenError as exc:
        return _fail_closed(exc.code)
    except WalkthroughError as exc:
        refreshed = resolve_walkthrough_access(
            credential,
            client_ip=_client_ip(),
            allow_responded=True,
        )
        return (
            render_template(
                "walkthrough/form.html",
                **_form_context(
                    refreshed, credential=credential, error=str(exc)
                ),
            ),
            400,
        )
    received = resolve_walkthrough_access(
        credential,
        client_ip=_client_ip(),
        allow_responded=True,
    )
    return render_template(
        "walkthrough/form.html",
        **_form_context(received, credential=credential),
    )
