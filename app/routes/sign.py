"""FG-033 SIGN-B public customer signing ceremony.

Narrow /sign/* exemption. No office chrome. No customer account.
Stops at SIGNED. Does not countersign or assemble an executed PDF.
"""

from __future__ import annotations

from flask import (
    Blueprint,
    Response,
    render_template,
    request,
)

from app import db
from app.models.organization import Organization
from app.models.project import Project
from app.models.signing import (
    AUTHORITY_SYNTHETIC_UAT,
    DOCUMENT_FAMILY_CHANGE_ORDER,
    STATUS_SIGNED,
)
from app.project_controls.repository import get_change_order
from app.services.signing import (
    BLOCK_CONFIRMED_NAME_REQUIRED,
    BLOCK_CONSENT_NOT_ACCEPTED,
    BLOCK_CONTRACT_PDF_NOT_AVAILABLE,
    BLOCK_REQUEST_TERMINAL,
    BLOCK_TOKEN_CONSUMED,
    BLOCK_TOKEN_EXPIRED,
    BLOCK_TOKEN_INVALID,
    BLOCK_TOKEN_RATE_LIMITED,
    SigningServiceError,
    accept_and_sign,
    frozen_pdf_bytes_for_customer,
    record_customer_viewed,
    resolve_customer_access,
)

sign_bp = Blueprint("sign", __name__, url_prefix="/sign")


def _client_ip():
    return request.remote_addr or "unknown"


def _user_agent():
    return request.headers.get("User-Agent", "")


def _ceremony_context(access):
    signing_request = access.request
    organization = db.session.get(Organization, signing_request.organization_id)
    project = db.session.get(Project, signing_request.project_id)
    document_title = signing_request.request_number
    if signing_request.document_family == DOCUMENT_FAMILY_CHANGE_ORDER:
        change_order = get_change_order(
            signing_request.source_record_id,
            organization_id=signing_request.organization_id,
        )
        if change_order is not None:
            document_title = change_order.title or document_title
    return {
        "signing_request": signing_request,
        "participant": access.participant,
        "organization": organization,
        "project": project,
        "document_title": document_title,
        "consent": signing_request.consent_version,
        "artifact_sha": signing_request.frozen_artifact.sha256,
        "is_change_order_pdf": (
            signing_request.document_family == DOCUMENT_FAMILY_CHANGE_ORDER
        ),
        "is_synthetic": signing_request.authority_class == AUTHORITY_SYNTHETIC_UAT,
        "completed": signing_request.status == STATUS_SIGNED,
        "credential": None,
    }


def _fail_closed(code: str, *, status_code=None):
    status = status_code
    if status is None:
        if code == BLOCK_TOKEN_RATE_LIMITED:
            status = 429
        elif code == BLOCK_TOKEN_EXPIRED:
            status = 410
        elif code == BLOCK_TOKEN_CONSUMED:
            status = 409
        elif code == BLOCK_CONTRACT_PDF_NOT_AVAILABLE:
            status = 409
        else:
            status = 404
    return (
        render_template(
            "signing/unavailable.html",
            code=code,
            rate_limited=code == BLOCK_TOKEN_RATE_LIMITED,
        ),
        status,
    )


@sign_bp.route("/<credential>", methods=["GET"])
def ceremony(credential):
    try:
        access = resolve_customer_access(
            credential,
            client_ip=_client_ip(),
            user_agent=_user_agent(),
            allow_completed=True,
        )
    except SigningServiceError as exc:
        return _fail_closed(exc.code)
    if access.request.status != STATUS_SIGNED:
        record_customer_viewed(access)
    context = _ceremony_context(access)
    context["credential"] = credential
    return render_template("signing/ceremony.html", **context)


@sign_bp.route("/<credential>/document", methods=["GET"])
def document(credential):
    try:
        access = resolve_customer_access(
            credential,
            client_ip=_client_ip(),
            user_agent=_user_agent(),
            allow_completed=True,
        )
        pdf = frozen_pdf_bytes_for_customer(access)
    except SigningServiceError as exc:
        return _fail_closed(exc.code)
    filename = f"{access.request.request_number}.pdf"
    return Response(
        pdf,
        mimetype="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Content-Type-Options": "nosniff",
        },
    )


@sign_bp.route("/<credential>/sign", methods=["POST"])
def sign_accept(credential):
    consent_accepted = (request.form.get("consent_accepted") or "") == "yes"
    confirmed_name = request.form.get("confirmed_signer_name") or ""
    try:
        signing_request = accept_and_sign(
            credential,
            confirmed_signer_name=confirmed_name,
            consent_accepted=consent_accepted,
            client_ip=_client_ip(),
            user_agent=_user_agent(),
        )
    except SigningServiceError as exc:
        if exc.code in (BLOCK_CONSENT_NOT_ACCEPTED, BLOCK_CONFIRMED_NAME_REQUIRED):
            try:
                access = resolve_customer_access(
                    credential,
                    client_ip=_client_ip(),
                    user_agent=_user_agent(),
                    allow_completed=False,
                )
            except SigningServiceError as inner:
                return _fail_closed(inner.code)
            context = _ceremony_context(access)
            context["credential"] = credential
            context["error_code"] = exc.code
            return render_template("signing/ceremony.html", **context), 400
        return _fail_closed(exc.code)
    access = resolve_customer_access(
        credential,
        client_ip=_client_ip(),
        user_agent=_user_agent(),
        allow_completed=True,
    )
    context = _ceremony_context(access)
    context["credential"] = credential
    context["just_signed"] = True
    _ = signing_request
    return render_template("signing/ceremony.html", **context)
