"""FG-033 SIGN-C/D authenticated office signing actions.

SIGN-C: executed-artifact retrieval.
SIGN-D: Change Order Send for Signature and in-progress office actions.
Not a signing dashboard. Actions stay on the Change Order record.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from flask import Blueprint, Response, abort, flash, g, redirect, request, session, url_for
from flask_login import current_user

from app.models.signing import ACTOR_HUMAN
from app.project_controls.repository import get_change_order
from app.presentation.contractor_copy import (
    EMAIL_NOT_SENT,
    SIGNING_INVITATION_ISSUED,
    SIGNING_LINK_COPY_HINT,
)
from app.services.signing import (
    BLOCK_ACTIVE_SIGNING_REQUEST,
    BLOCK_ALREADY_EXECUTED,
    BLOCK_CHANGE_ORDER_NOT_APPROVED,
    BLOCK_COUNTERSIGN_NOT_REQUIRED,
    BLOCK_COUNTERSIGN_REQUIRED,
    BLOCK_MEMBERSHIP_REQUIRED,
    BLOCK_REQUEST_NOT_APPROVED,
    BLOCK_REQUEST_NOT_CREATED,
    BLOCK_REQUEST_NOT_FOUND,
    BLOCK_REQUEST_NOT_SENT,
    BLOCK_REQUEST_NOT_SIGNED,
    BLOCK_REQUEST_TERMINAL,
    BLOCK_SIGNER_EMAIL_REQUIRED,
    BLOCK_SIGNER_NAME_REQUIRED,
    BLOCK_VOID_REASON_REQUIRED,
    DEFAULT_INVITATION_DAYS,
    SigningServiceError,
    approve_signing_request,
    countersign_and_execute,
    execute_signed_request,
    get_signing_request,
    issue_customer_invitation,
    office_send_change_order_for_signature,
    resend_customer_invitation,
    retrieve_executed_artifact_bytes,
    void_signing_request,
)
from app.services.signing_mail import office_email_delivery_label

signing_office_bp = Blueprint("signing_office", __name__)

_OFFICE_ERROR_COPY = {
    BLOCK_CHANGE_ORDER_NOT_APPROVED: (
        "This Change Order must be Approved before it can be sent for signature."
    ),
    BLOCK_ACTIVE_SIGNING_REQUEST: (
        "A signing request is already in progress for this Change Order."
    ),
    BLOCK_SIGNER_NAME_REQUIRED: "Enter the signer name.",
    BLOCK_SIGNER_EMAIL_REQUIRED: "Enter a valid signer email.",
    BLOCK_REQUEST_NOT_FOUND: "Signing request not found.",
    BLOCK_REQUEST_NOT_CREATED: "This request is not waiting for approval.",
    BLOCK_REQUEST_NOT_APPROVED: "This request is not ready for an invitation.",
    BLOCK_REQUEST_NOT_SENT: "This request does not have an active invitation.",
    BLOCK_REQUEST_NOT_SIGNED: "The customer has not signed this request yet.",
    BLOCK_REQUEST_TERMINAL: "This signing request is closed.",
    BLOCK_ALREADY_EXECUTED: "This signing request is already executed.",
    BLOCK_COUNTERSIGN_REQUIRED: "Organization countersignature is required first.",
    BLOCK_COUNTERSIGN_NOT_REQUIRED: "This request does not require countersignature.",
    BLOCK_VOID_REASON_REQUIRED: "Enter a reason to void this request.",
    BLOCK_MEMBERSHIP_REQUIRED: "You cannot act on another organization's request.",
}


def _organization_id():
    organization_id = getattr(g, "organization_id", None)
    if not organization_id:
        abort(404)
    return organization_id


def _actor():
    return ACTOR_HUMAN, current_user.id, (current_user.email or "").strip()


def _flash_error(code: str) -> None:
    flash(_OFFICE_ERROR_COPY.get(code, "That signing action could not be completed."), "error")


def _flash_invitation(issue, *, resent=False) -> None:
    row = getattr(issue, "mail_message", None)
    label = office_email_delivery_label(row.status) if row is not None else EMAIL_NOT_SENT
    if resent:
        flash(
            f"A new invitation link was generated. The previous link no longer works. {label}. {SIGNING_LINK_COPY_HINT}",
            "success",
        )
        return
    flash(f"{SIGNING_INVITATION_ISSUED}. {label}. {SIGNING_LINK_COPY_HINT}", "success")


def _co_url(change_order_id: int) -> str:
    return url_for("project_controls.view_change_order", id=change_order_id)


def _redirect_for_request(request_id: int, organization_id: str):
    try:
        signing_request = get_signing_request(request_id, organization_id)
    except SigningServiceError:
        abort(404)
    if signing_request.document_family != "CHANGE_ORDER":
        abort(404)
    return redirect(_co_url(signing_request.source_record_id))


def _store_invitation(issue) -> str:
    url = request.host_url.rstrip("/") + issue.path
    session["signing_invitation_request_id"] = issue.request.id
    session["signing_invitation_url"] = url
    return url


def _parse_expiry_days(raw) -> datetime:
    try:
        days = int((raw or "").strip() or DEFAULT_INVITATION_DAYS)
    except (TypeError, ValueError):
        days = DEFAULT_INVITATION_DAYS
    if days < 1 or days > 30:
        days = DEFAULT_INVITATION_DAYS
    return datetime.utcnow() + timedelta(days=days)


@signing_office_bp.route(
    "/project-controls/change-orders/<int:change_order_id>/send-for-signature",
    methods=["POST"],
)
def send_for_signature(change_order_id):
    organization_id = _organization_id()
    change_order = get_change_order(change_order_id, organization_id=organization_id)
    if change_order is None:
        abort(404)
    actor_kind, actor_user_id, actor_identifier = _actor()
    countersign_required = (request.form.get("countersign_required") or "").strip() == "yes"
    try:
        issue = office_send_change_order_for_signature(
            change_order_id,
            organization_id=organization_id,
            actor_user_id=actor_user_id,
            actor_identifier=actor_identifier,
            invited_name=request.form.get("signer_name", ""),
            invited_email=request.form.get("signer_email", ""),
            countersign_required=countersign_required,
            expires_at=_parse_expiry_days(request.form.get("expiry_days")),
        )
    except SigningServiceError as exc:
        _flash_error(exc.code)
        return redirect(_co_url(change_order_id))
    _store_invitation(issue)
    _flash_invitation(issue)
    return redirect(_co_url(change_order_id))


@signing_office_bp.route("/signing-requests/<int:request_id>/approve", methods=["POST"])
def approve(request_id):
    organization_id = _organization_id()
    actor_kind, actor_user_id, actor_identifier = _actor()
    try:
        approve_signing_request(
            request_id,
            organization_id=organization_id,
            actor_kind=actor_kind,
            actor_user_id=actor_user_id,
            actor_identifier=actor_identifier,
        )
    except SigningServiceError as exc:
        _flash_error(exc.code)
        return _redirect_for_request(request_id, organization_id)
    flash("Approved for signature.", "success")
    return _redirect_for_request(request_id, organization_id)


@signing_office_bp.route("/signing-requests/<int:request_id>/invite", methods=["POST"])
def invite(request_id):
    organization_id = _organization_id()
    actor_kind, actor_user_id, actor_identifier = _actor()
    try:
        issue = issue_customer_invitation(
            request_id,
            organization_id=organization_id,
            actor_kind=actor_kind,
            actor_user_id=actor_user_id,
            actor_identifier=actor_identifier,
        )
    except SigningServiceError as exc:
        _flash_error(exc.code)
        return _redirect_for_request(request_id, organization_id)
    _store_invitation(issue)
    _flash_invitation(issue)
    return _redirect_for_request(request_id, organization_id)


@signing_office_bp.route("/signing-requests/<int:request_id>/resend", methods=["POST"])
def resend(request_id):
    organization_id = _organization_id()
    actor_kind, actor_user_id, actor_identifier = _actor()
    try:
        issue = resend_customer_invitation(
            request_id,
            organization_id=organization_id,
            actor_kind=actor_kind,
            actor_user_id=actor_user_id,
            actor_identifier=actor_identifier,
        )
    except SigningServiceError as exc:
        _flash_error(exc.code)
        return _redirect_for_request(request_id, organization_id)
    _store_invitation(issue)
    _flash_invitation(issue, resent=True)
    return _redirect_for_request(request_id, organization_id)


@signing_office_bp.route("/signing-requests/<int:request_id>/void", methods=["POST"])
def void(request_id):
    organization_id = _organization_id()
    actor_kind, actor_user_id, actor_identifier = _actor()
    try:
        void_signing_request(
            request_id,
            organization_id=organization_id,
            actor_kind=actor_kind,
            actor_user_id=actor_user_id,
            actor_identifier=actor_identifier,
            reason=request.form.get("void_reason", ""),
        )
    except SigningServiceError as exc:
        _flash_error(exc.code)
        return _redirect_for_request(request_id, organization_id)
    session.pop("signing_invitation_url", None)
    session.pop("signing_invitation_request_id", None)
    flash("Signing request voided. The invitation can no longer be used.", "success")
    return _redirect_for_request(request_id, organization_id)


@signing_office_bp.route("/signing-requests/<int:request_id>/countersign", methods=["POST"])
def countersign(request_id):
    organization_id = _organization_id()
    actor_kind, actor_user_id, actor_identifier = _actor()
    try:
        countersign_and_execute(
            request_id,
            organization_id=organization_id,
            actor_kind=actor_kind,
            actor_user_id=actor_user_id,
            actor_identifier=actor_identifier,
        )
    except SigningServiceError as exc:
        _flash_error(exc.code)
        return _redirect_for_request(request_id, organization_id)
    flash("Countersigned. Executed PDF is retained.", "success")
    return _redirect_for_request(request_id, organization_id)


@signing_office_bp.route("/signing-requests/<int:request_id>/execute", methods=["POST"])
def execute(request_id):
    organization_id = _organization_id()
    actor_kind, actor_user_id, actor_identifier = _actor()
    try:
        execute_signed_request(
            request_id,
            organization_id=organization_id,
            actor_kind=actor_kind,
            actor_user_id=actor_user_id,
            actor_identifier=actor_identifier,
        )
    except SigningServiceError as exc:
        _flash_error(exc.code)
        return _redirect_for_request(request_id, organization_id)
    flash("Executed PDF is retained.", "success")
    return _redirect_for_request(request_id, organization_id)


@signing_office_bp.route("/signing-requests/<int:request_id>/executed", methods=["GET"])
def download_executed(request_id):
    organization_id = _organization_id()
    try:
        overlay_probe = get_signing_request(request_id, organization_id)
        pdf = retrieve_executed_artifact_bytes(request_id, organization_id)
    except SigningServiceError:
        abort(404)
    filename = f"{overlay_probe.request_number}-executed.pdf"
    return Response(
        pdf,
        mimetype="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Content-Type-Options": "nosniff",
        },
    )
