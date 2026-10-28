"""FG-034 shared transactional-email service.

Owns delivery only. Password-reset and Signing consume this service.
AUTH-D activates the Postmark HTTP adapter when token and sender exist.
Missing configuration remains FAILED_CONFIG. Status is never DELIVERED.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Mapping, Optional

from flask import current_app

from app import db
from app.models.transactional_message import (
    PROVIDER_FAKE,
    PROVIDER_LOCAL,
    PROVIDER_POSTMARK,
    PROVIDER_SMTP,
    STATUS_ACCEPTED,
    STATUS_FAILED,
    STATUS_FAILED_CONFIG,
    STATUS_LOCAL_CAPTURED,
    STATUS_SKIPPED_ALLOWLIST,
    TEMPLATE_DELIVERY_SCHEDULE,
    TEMPLATE_PASSWORD_RESET,
    TEMPLATE_ACCOUNT_INVITATION,
    TEMPLATE_INVITATION_SENT_CONFIRMATION,
    TEMPLATE_PROPOSAL_INVITATION,
    TEMPLATE_SIGNING_COMPLETE,
    TEMPLATE_SIGNING_INVITATION,
    TEMPLATE_SIGNING_RESEND,
    TEMPLATE_SIGNING_SUPPLIER_INVITATION,
    TEMPLATE_SUPPLIER_QUOTE,
    TRANSACTIONAL_TEMPLATE_IDS,
    TransactionalMessage,
)

SECRET_VARIABLE_KEYS = {
    "secret",
    "token",
    "password",
    "raw_secret",
    "reset_url",
    "invitation_url",
    "signing_url",
    "reset_secret",
    "invitation_secret",
}

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class TransactionalEmailError(Exception):
    """Operator-facing transactional email failure."""


@dataclass(frozen=True)
class TransportPayload:
    template_id: str
    to_email: str
    from_email: str
    from_name: str
    reply_to: str
    subject: str
    text_body: str
    variables: Mapping[str, Any]
    html_body: Optional[str] = None  # CaliSIGN invitations (28 Oct 2026); the text body is always sent too


@dataclass
class TransportResult:
    status: str
    provider: str
    provider_message_id: Optional[str] = None
    error_code: Optional[str] = None
    capture_path: Optional[str] = None


def _normalize_email(value: Optional[str]) -> str:
    email = (value or "").strip().lower()
    if not email or not _EMAIL_RE.match(email):
        raise TransactionalEmailError("A valid recipient email is required.")
    return email


def _config_str(name: str, default: str = "") -> str:
    value = current_app.config.get(name)
    if value is None or value == "":
        value = os.environ.get(name, default)
    return (value or default).strip()


def public_base_url() -> str:
    configured = _config_str("PUBLIC_BASE_URL")
    if configured:
        return configured.rstrip("/")
    provider = _config_str("TRANSACTIONAL_EMAIL_PROVIDER", PROVIDER_LOCAL).lower()
    if current_app.config.get("TESTING") or provider == PROVIDER_LOCAL:
        return "http://localhost"
    return ""


def redact_variables(variables: Optional[Mapping[str, Any]]) -> dict:
    redacted = {}
    for key, value in dict(variables or {}).items():
        if str(key).strip().lower() in SECRET_VARIABLE_KEYS:
            redacted[str(key)] = "[REDACTED]"
        else:
            redacted[str(key)] = value
    return redacted


def _allowlist() -> set[str]:
    raw = _config_str("TRANSACTIONAL_UAT_ALLOWLIST")
    if not raw:
        return set()
    return {part.strip().lower() for part in raw.split(",") if part.strip()}


def _render(template_id: str, variables: Mapping[str, Any]) -> tuple[str, str]:
    expires = str(variables.get("expires_minutes") or "60")
    if template_id == TEMPLATE_PASSWORD_RESET:
        url = str(variables.get("reset_url") or "")
        subject = "Reset your CalibraytAI password"
        body = (
            "CalibraytAI received a password-reset request.\n\n"
            f"Use this link to choose a new password. It expires in {expires} minutes.\n"
            f"{url}\n\n"
            "If you did not request this, ignore this message. "
            "Your password will not change."
        )
        return subject, body
    if template_id == TEMPLATE_ACCOUNT_INVITATION:
        url = str(variables.get("reset_url") or "")
        company = str(variables.get("company_name") or "Your company")
        inviter = str(variables.get("invited_by") or "")
        hours = str(variables.get("expires_hours") or "72")
        subject = f"{company} invited you to CalibraytAI"
        body = (
            f"{company} has set up a CalibraytAI sign-in for you"
            + (f" ({inviter} invited you)" if inviter else "") + ".\n\n"
            f"Use this link to choose your password and sign in. It works for {hours} hours.\n"
            f"{url}\n\n"
            "On an iPhone: open the link in Safari, choose your password, then tap Share and Add to Home Screen.\n\n"
            "If you were not expecting this, ignore this message."
        )
        return subject, body
    if template_id == "DELIVERY_TEST":
        code = str(variables.get("code") or "")
        site = str(variables.get("site") or "CalibraytAI")
        subject = f"CalibraytAI email test {code}"
        body = (
            f"This is a test from {site} to check that its sign-in emails reach this inbox.\n\n"
            f"Test code: {code}\n\n"
            "Nothing to do; you can delete it. It contains no link."
        )
        return subject, body
    if template_id == TEMPLATE_INVITATION_SENT_CONFIRMATION:
        # Built only from a name, an address, a kind and two times: there is no link variable to render.
        kind = "invitation" if variables.get("kind") == "invitation" else "set-password link"
        name = str(variables.get("person_name") or "")
        email = str(variables.get("person_email") or "")
        subject = f"Your CalibraytAI {kind} to {name} was sent"
        body = (
            f"Your CalibraytAI {kind} to {name} ({email}) was sent at {variables.get('sent_at') or ''}. "
            f"It works once and expires {variables.get('expires') or ''}.\n\n"
            "This note does not contain the link. If the person did not get the email, send a new link from "
            "Company \u2192 People & Access."
        )
        return subject, body
    if template_id == TEMPLATE_DELIVERY_SCHEDULE:
        subject = str(variables.get("subject") or "Delivery schedule update")
        body = str(variables.get("body") or "")
        url = str(variables.get("link") or "")
        return subject, body + (f"\n\nOpen it: {url}\n" if url else "\n")
    if template_id == TEMPLATE_SUPPLIER_QUOTE:
        supplier = str(variables.get("supplier_name") or "Your building supplier")
        number = str(variables.get("quote_number") or "")
        total = str(variables.get("total") or "")
        valid = str(variables.get("valid_until") or "")
        subject = f"{supplier}: material quotation {number}"
        body = (
            f"{supplier} has prepared material quotation {number} for you"
            + (f", total ${total} including tax" if total else "") + ".\n\n"
            "Open the link to review it and the preliminary drawing. If you agree, type your name and select Accept.\n"
            + (f"The quotation is valid until {valid}.\n" if valid else "")
            + f"{variables.get('link') or ''}\n\n"
            "This is a materials-only quotation. The drawing is a preliminary sales drawing, not for construction.\n"
        )
        return subject, body
    if template_id == TEMPLATE_PROPOSAL_INVITATION:
        url = str(variables.get("invitation_url") or "")
        org = str(variables.get("organization_name") or "Brayman Construction")
        document = str(variables.get("document_label") or "your proposal")
        expiry = str(variables.get("expires_display") or "").strip()
        expiry_line = f"The link is valid until {expiry}.\n" if expiry else ""
        subject = f"{org}: your proposal is ready to review"
        body = (
            f"{org} has prepared a proposal for you: {document}.\n\n"
            "Open the link to review it. If you agree, tick the box and select Accept Proposal.\n"
            f"{expiry_line}"
            f"{url}\n"
        )
        return subject, body
    if template_id == TEMPLATE_SIGNING_INVITATION:
        url = str(variables.get("invitation_url") or "")
        org = str(variables.get("organization_name") or "CalibraytAI")
        document = str(variables.get("document_label") or "a document")
        kind = str(variables.get("document_kind") or "document")
        project = str(variables.get("project_name") or "").strip()
        expiry = str(variables.get("expires_display") or "").strip()
        expiry_line = f"This invitation expires {expiry}.\n" if expiry else ""
        subject = f"{org}: {kind} ready to Review & Sign"
        body = (
            f"{org} has a {kind} ready for your signature: {document}"
            + (f" (project: {project})" if project else "") + ".\n\n"
            "Review & Sign — open the secure link below to review the document and sign it electronically "
            "(CaliSIGN by CalibraytAI). No CalibraytAI account is needed.\n"
            f"{expiry_line}"
            f"Review and Sign Document: {url}\n"
        )
        return subject, body
    if template_id == TEMPLATE_SIGNING_RESEND:
        url = str(variables.get("invitation_url") or "")
        org = str(variables.get("organization_name") or "CalibraytAI")
        document = str(variables.get("document_label") or "a document")
        kind = str(variables.get("document_kind") or "document")
        expiry = str(variables.get("expires_display") or "").strip()
        expiry_line = f"This invitation expires {expiry}.\n" if expiry else ""
        subject = f"{org}: current {kind} signing link"
        body = (
            f"{org} sent the current signing link for {document}. Any earlier link no longer works.\n\n"
            "Review & Sign using this current signing link. No CalibraytAI account is needed.\n"
            f"{expiry_line}"
            f"Review and Sign Document: {url}\n"
        )
        return subject, body
    if template_id == TEMPLATE_SIGNING_SUPPLIER_INVITATION:
        url = str(variables.get("link") or "")
        org = str(variables.get("organization_name") or "The contractor")
        document = str(variables.get("document_label") or "a purchase order")
        kind = str(variables.get("document_kind") or "purchase order")
        reason = str(variables.get("reason") or "").strip()
        subject = f"{org}: {kind} {document} ready for your signature"
        body = (
            f"{org} sent {kind} {document} for your signature.\n"
            + (f"{reason}\n" if reason else "") + "\n"
            "Sign in to the Supplier Hub to review the document and sign it (CaliSIGN by CalibraytAI).\n"
            f"Review and Sign Document: {url}\n"
        )
        return subject, body
    if template_id == TEMPLATE_SIGNING_COMPLETE:
        org = str(variables.get("organization_name") or "CalibraytAI")
        document = str(variables.get("document_label") or "the document")
        kind = str(variables.get("document_kind") or "document")
        subject = f"{org}: {kind} signing is complete"
        body = (
            f"{org}: signing is complete for {document}.\n"
            "Contact the office if you need a copy of the completed document. "
            "This message does not include a new signing link."
        )
        return subject, body
    raise TransactionalEmailError("Unsupported transactional template.")


# CaliSIGN (28 Oct 2026): the signing emails also go as HTML in the approved CaliSIGN treatment
# (templates/emails/calisign_message.html). The plain-text body above is unchanged in meaning and always sent.
_CALISIGN_HTML_TEMPLATES = None


def _calisign_templates():
    global _CALISIGN_HTML_TEMPLATES
    if _CALISIGN_HTML_TEMPLATES is None:
        from app.models.transactional_message import (
            TEMPLATE_SIGNING_COMPLETE as _C,
            TEMPLATE_SIGNING_INVITATION as _I,
            TEMPLATE_SIGNING_RESEND as _R,
            TEMPLATE_SIGNING_SUPPLIER_INVITATION as _S,
        )

        _CALISIGN_HTML_TEMPLATES = {_I, _R, _C, _S}
    return _CALISIGN_HTML_TEMPLATES


def _render_html(template_id: str, variables: Mapping[str, Any], subject: str) -> Optional[str]:
    if template_id not in _calisign_templates():
        return None
    try:
        from flask import render_template

        return render_template("emails/calisign_message.html", template_id=template_id, v=variables, subject=subject)
    except Exception:  # noqa: BLE001 - the text email still goes if the HTML cannot be made
        return None


class LocalCaptureTransport:
    def send(self, payload: TransportPayload) -> TransportResult:
        root = current_app.config.get("MAIL_CAPTURE_ROOT")
        if not root:
            root = os.path.join(current_app.instance_path, "mail_capture")
        os.makedirs(root, exist_ok=True)
        stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S%f")
        path = os.path.join(root, f"{stamp}-{payload.template_id}.txt")
        redacted = redact_variables(payload.variables)
        content = (
            f"From: {payload.from_name} <{payload.from_email}>\n"
            f"To: {payload.to_email}\n"
            f"Reply-To: {payload.reply_to}\n"
            f"Subject: {payload.subject}\n"
            f"Template: {payload.template_id}\n"
            f"Variables-redacted: {json.dumps(redacted, sort_keys=True)}\n"
            "\n"
            f"{payload.text_body}\n"
        )
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(content)
        if payload.html_body:
            with open(path[:-4] + ".html", "w", encoding="utf-8") as handle:
                handle.write(payload.html_body)
        return TransportResult(
            status=STATUS_LOCAL_CAPTURED,
            provider=PROVIDER_LOCAL,
            provider_message_id=None,
            capture_path=path,
        )


POSTMARK_EMAIL_ENDPOINT = "https://api.postmarkapp.com/email"


def postmark_request_payload(payload: TransportPayload) -> dict[str, str]:
    """Build the Postmark /email JSON body. Never includes the server token."""
    from_value = payload.from_email
    if payload.from_name:
        from_value = f"{payload.from_name} <{payload.from_email}>"
    body = {
        "From": from_value,
        "To": payload.to_email,
        "Subject": payload.subject,
        "TextBody": payload.text_body,
    }
    if payload.html_body:
        body["HtmlBody"] = payload.html_body
    if payload.reply_to:
        body["ReplyTo"] = payload.reply_to
    return body


def postmark_http_send(payload: TransportPayload) -> TransportResult:
    """AUTH-D production Postmark HTTP. Tests inject POSTMARK_URLOPEN or POSTMARK_HTTP_SEND."""
    token = _config_str("POSTMARK_SERVER_TOKEN")
    if not token or not payload.from_email:
        return TransportResult(
            status=STATUS_FAILED_CONFIG,
            provider=PROVIDER_POSTMARK,
            error_code="POSTMARK_CONFIG",
        )
    opener = current_app.config.get("POSTMARK_URLOPEN") or urllib.request.urlopen
    request = urllib.request.Request(
        POSTMARK_EMAIL_ENDPOINT,
        data=json.dumps(postmark_request_payload(payload)).encode("utf-8"),
        method="POST",
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Postmark-Server-Token": token,
        },
    )
    try:
        with opener(request, timeout=15) as response:
            raw = response.read() or b"{}"
        parsed = json.loads(raw.decode("utf-8"))
        message_id = parsed.get("MessageID")
        return TransportResult(
            status=STATUS_ACCEPTED,
            provider=PROVIDER_POSTMARK,
            provider_message_id=str(message_id) if message_id else None,
        )
    except urllib.error.HTTPError as exc:
        error_code = f"POSTMARK_HTTP_{exc.code}"
        try:
            parsed = json.loads((exc.read() or b"").decode("utf-8") or "{}")
            provider_code = parsed.get("ErrorCode")
            if provider_code is not None:
                error_code = f"POSTMARK_{provider_code}"
        except Exception:
            pass
        return TransportResult(
            status=STATUS_FAILED,
            provider=PROVIDER_POSTMARK,
            error_code=str(error_code)[:40],
        )
    except Exception:
        return TransportResult(
            status=STATUS_FAILED,
            provider=PROVIDER_POSTMARK,
            error_code="POSTMARK_TRANSPORT",
        )


class PostmarkTransport:
    """AUTH-D Postmark adapter. Missing config is FAILED_CONFIG. Never DELIVERED."""

    def send(self, payload: TransportPayload) -> TransportResult:
        token = _config_str("POSTMARK_SERVER_TOKEN")
        from_email = payload.from_email
        http_send = current_app.config.get("POSTMARK_HTTP_SEND")
        if not token or not from_email:
            return TransportResult(
                status=STATUS_FAILED_CONFIG,
                provider=PROVIDER_POSTMARK,
                error_code="POSTMARK_CONFIG",
            )
        if http_send is None:
            http_send = postmark_http_send
        result = http_send(payload)
        if isinstance(result, TransportResult):
            return result
        return TransportResult(
            status=STATUS_ACCEPTED,
            provider=PROVIDER_POSTMARK,
            provider_message_id=str(result),
        )


class SmtpTransport:
    """Hands the message to an SMTP server (22 Oct 2026): on the HostPapa server, its own mail system on
    localhost:25. SMTP_HOST, SMTP_PORT, SMTP_STARTTLS, SMTP_USERNAME and SMTP_PASSWORD configure it; the
    password is read from the environment only and never logged. Tests inject SMTP_FACTORY."""

    def send(self, payload: TransportPayload) -> TransportResult:
        import smtplib
        from email.message import EmailMessage
        from email.utils import formataddr, make_msgid

        host = _config_str("SMTP_HOST", "localhost")
        try:
            port = int(_config_str("SMTP_PORT", "25") or 25)
        except ValueError:
            port = 25
        if not host or not payload.from_email or payload.from_email.endswith("@localhost"):
            return TransportResult(status=STATUS_FAILED_CONFIG, provider=PROVIDER_SMTP, error_code="SMTP_CONFIG")
        message = EmailMessage()
        message["From"] = formataddr((payload.from_name or "", payload.from_email))
        message["To"] = payload.to_email
        if payload.reply_to:
            message["Reply-To"] = payload.reply_to
        message["Subject"] = payload.subject
        message_id = make_msgid(domain=payload.from_email.rsplit("@", 1)[-1])
        message["Message-ID"] = message_id
        message.set_content(payload.text_body)
        if payload.html_body:
            message.add_alternative(payload.html_body, subtype="html")
        factory = current_app.config.get("SMTP_FACTORY") or smtplib.SMTP
        try:
            with factory(host, port, timeout=20) as client:
                if _config_str("SMTP_STARTTLS").lower() in ("1", "true", "yes"):
                    client.starttls()
                user = _config_str("SMTP_USERNAME")
                if user:
                    client.login(user, _config_str("SMTP_PASSWORD"))
                refused = client.send_message(message)
        except (OSError, smtplib.SMTPException):
            return TransportResult(status=STATUS_FAILED, provider=PROVIDER_SMTP, error_code="SMTP_TRANSPORT")
        if refused:
            return TransportResult(status=STATUS_FAILED, provider=PROVIDER_SMTP, error_code="SMTP_REFUSED")
        return TransportResult(status=STATUS_ACCEPTED, provider=PROVIDER_SMTP, provider_message_id=message_id[:120])


def email_delivery_configured() -> bool:
    """True when this site hands email to a real mail service (Postmark with a server token).

    Without it, forgot-password and invitation emails are only written to a file on the server, so the
    sign-in pages say so instead of telling people to wait for an email that will never come
    (training sign-in fix, 21 Oct 2026). Says nothing about any account."""
    if current_app.config.get("TRANSACTIONAL_EMAIL_TRANSPORT") is not None:
        return True
    provider = _config_str("TRANSACTIONAL_EMAIL_PROVIDER", PROVIDER_LOCAL).lower()
    if provider == PROVIDER_SMTP:
        return True
    if provider == PROVIDER_POSTMARK:
        # Postmark chosen: a missing token is an operator error, recorded on each message (FAILED_CONFIG);
        # the public pages stay generic for it.
        return True
    # Captured mail is the delivery on a development or test office (the file is read there), never on a
    # hosted office or the training site: the same rule as password_reset._delivered.
    from app import _is_hosted
    from app.training.service import enabled as training_site

    return not _is_hosted(current_app) and not training_site(current_app)


def link_base_url() -> str:
    """The address for a link shown on screen: PUBLIC_BASE_URL when set, else the address the person is
    using now. (public_base_url() falls back to http://localhost for captured mail, which is wrong for a
    link someone will open on another device.)"""
    from flask import has_request_context, request

    configured = _config_str("PUBLIC_BASE_URL")
    if configured:
        return configured.rstrip("/")
    return request.url_root.rstrip("/") if has_request_context() else ""


def _resolve_transport() -> Any:
    injected = current_app.config.get("TRANSACTIONAL_EMAIL_TRANSPORT")
    if injected is not None:
        return injected
    provider = _config_str("TRANSACTIONAL_EMAIL_PROVIDER", PROVIDER_LOCAL).lower()
    if provider == PROVIDER_POSTMARK:
        return PostmarkTransport()
    if provider == PROVIDER_SMTP:
        return SmtpTransport()
    return LocalCaptureTransport()


def send_transactional_message(
    template_id: str,
    to_email: str,
    variables: Optional[Mapping[str, Any]] = None,
    related_type: Optional[str] = None,
    related_id: Optional[Any] = None,
) -> TransactionalMessage:
    if template_id not in TRANSACTIONAL_TEMPLATE_IDS:
        raise TransactionalEmailError("Unsupported transactional template.")
    recipient = _normalize_email(to_email)
    from_email = _config_str("TRANSACTIONAL_FROM_EMAIL", "noreply@localhost")
    from_name = _config_str("TRANSACTIONAL_FROM_NAME", "CalibraytAI")
    reply_to = _config_str("TRANSACTIONAL_REPLY_TO", from_email)
    vars_map = dict(variables or {})
    subject, text_body = _render(template_id, vars_map)
    payload = TransportPayload(
        template_id=template_id,
        to_email=recipient,
        from_email=from_email,
        from_name=from_name,
        reply_to=reply_to,
        subject=subject,
        text_body=text_body,
        variables=vars_map,
        html_body=_render_html(template_id, vars_map, subject),
    )
    allowlist = _allowlist()
    provider_name = _config_str("TRANSACTIONAL_EMAIL_PROVIDER", PROVIDER_LOCAL).lower()
    if current_app.config.get("TRANSACTIONAL_EMAIL_TRANSPORT") is not None:
        provider_name = PROVIDER_FAKE
    if allowlist and recipient not in allowlist:
        row = TransactionalMessage(
            template_id=template_id,
            to_email=recipient,
            from_email=from_email or "noreply@localhost",
            provider=provider_name or PROVIDER_LOCAL,
            status=STATUS_SKIPPED_ALLOWLIST,
            error_code="ALLOWLIST",
            related_type=(related_type or "")[:40] or None,
            related_id=None if related_id is None else str(related_id)[:80],
        )
        db.session.add(row)
        db.session.commit()
        return row
    transport = _resolve_transport()
    try:
        result = transport.send(payload)
    except Exception:
        result = TransportResult(
            status=STATUS_FAILED,
            provider=provider_name or PROVIDER_LOCAL,
            error_code="TRANSPORT_ERROR",
        )
    row = TransactionalMessage(
        template_id=template_id,
        to_email=recipient,
        from_email=from_email or "noreply@localhost",
        provider=result.provider or provider_name or PROVIDER_LOCAL,
        provider_message_id=result.provider_message_id,
        status=result.status,
        error_code=result.error_code,
        related_type=(related_type or "")[:40] or None,
        related_id=None if related_id is None else str(related_id)[:80],
    )
    db.session.add(row)
    db.session.commit()
    return row
