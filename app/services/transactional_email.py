"""FG-034 MAIL-A shared transactional-email service.

Owns delivery only. Password-reset and Signing consume this service later.
MAIL-A does not perform live Postmark HTTP; the adapter is the activation boundary.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Mapping, Optional

from flask import current_app

from app import db
from app.models.transactional_message import (
    PROVIDER_FAKE,
    PROVIDER_LOCAL,
    PROVIDER_POSTMARK,
    STATUS_ACCEPTED,
    STATUS_FAILED,
    STATUS_FAILED_CONFIG,
    STATUS_LOCAL_CAPTURED,
    STATUS_SKIPPED_ALLOWLIST,
    TEMPLATE_PASSWORD_RESET,
    TEMPLATE_SIGNING_COMPLETE,
    TEMPLATE_SIGNING_INVITATION,
    TEMPLATE_SIGNING_RESEND,
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
    if template_id == TEMPLATE_SIGNING_INVITATION:
        url = str(variables.get("invitation_url") or "")
        subject = "Document ready for your signature"
        body = (
            "CalibraytAI has a document ready for your signature.\n\n"
            f"Open this secure link to review and sign:\n{url}\n"
        )
        return subject, body
    if template_id == TEMPLATE_SIGNING_RESEND:
        url = str(variables.get("invitation_url") or "")
        subject = "Signing link resent"
        body = (
            "CalibraytAI resent your signing link.\n\n"
            f"Open this secure link to review and sign:\n{url}\n"
        )
        return subject, body
    if template_id == TEMPLATE_SIGNING_COMPLETE:
        subject = "Document signing is complete"
        body = (
            "CalibraytAI: the document you were invited to sign is complete.\n"
            "Contact the office if you need a copy. This message does not "
            "include a new signing link."
        )
        return subject, body
    raise TransactionalEmailError("Unsupported transactional template.")


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
        return TransportResult(
            status=STATUS_LOCAL_CAPTURED,
            provider=PROVIDER_LOCAL,
            provider_message_id=None,
            capture_path=path,
        )


class PostmarkTransport:
    """MAIL-A adapter boundary. Live HTTP is AUTH-D; missing config is FAILED_CONFIG."""

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
            return TransportResult(
                status=STATUS_FAILED_CONFIG,
                provider=PROVIDER_POSTMARK,
                error_code="POSTMARK_HTTP_NOT_ACTIVATED",
            )
        result = http_send(payload)
        if isinstance(result, TransportResult):
            return result
        return TransportResult(
            status=STATUS_ACCEPTED,
            provider=PROVIDER_POSTMARK,
            provider_message_id=str(result),
        )


def _resolve_transport() -> Any:
    injected = current_app.config.get("TRANSACTIONAL_EMAIL_TRANSPORT")
    if injected is not None:
        return injected
    provider = _config_str("TRANSACTIONAL_EMAIL_PROVIDER", PROVIDER_LOCAL).lower()
    if provider == PROVIDER_POSTMARK:
        return PostmarkTransport()
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
