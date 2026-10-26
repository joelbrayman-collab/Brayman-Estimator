"""Did the email actually arrive? (sign-in reliability, Joel, 26 Oct 2026)

"Accepted" means only that the mail service took the message. What happened next comes from the mail service:
Postmark's delivery, bounce and spam-complaint webhooks (POST /webhooks/postmark, HTTP Basic credentials from
POSTMARK_WEBHOOK_USERNAME / POSTMARK_WEBHOOK_PASSWORD) and "Check delivery", which reads Postmark's own record of
the message (GET /messages/outbound/{id}/details with the server token). Each report is one row in
transactional_delivery_events; nothing here stores a link, token or message body.

The words people see:
    Delivered            the receiving mail server took it (Postmark confirmed)
    Bounced: <reason>    it was refused; the reason is Postmark's
    Delayed              the receiving server asked Postmark to try again later
    Waiting              accepted by Postmark, no report yet
    Not confirmable      handed to an SMTP server that reports nothing back
    Not sent: <reason>   never left CalibraytAI (allowlist, not set up, refused)
"""

from __future__ import annotations

import hmac
import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, Optional

from flask import current_app

from app import db
from app.models.email_delivery import (
    EVENT_BOUNCED,
    EVENT_DELAYED,
    EVENT_DELIVERED,
    EVENT_SPAM_COMPLAINT,
    SOURCE_CHECK,
    SOURCE_WEBHOOK,
    TransactionalDeliveryEvent,
)
from app.models.transactional_message import (
    PROVIDER_POSTMARK,
    PROVIDER_SMTP,
    STATUS_ACCEPTED,
    STATUS_LOCAL_CAPTURED,
    TransactionalMessage,
)

POSTMARK_DETAILS_ENDPOINT = "https://api.postmarkapp.com/messages/outbound/{id}/details"

STATE_DELIVERED = "DELIVERED"
STATE_BOUNCED = "BOUNCED"
STATE_DELAYED = "DELAYED"
STATE_WAITING = "WAITING"
STATE_UNCONFIRMABLE = "UNCONFIRMABLE"
STATE_CAPTURED = "CAPTURED"
STATE_NOT_SENT = "NOT_SENT"

NOT_SENT_REASONS = {
    "SKIPPED_ALLOWLIST": "this office only emails the test addresses on its allowlist",
    "FAILED_CONFIG": "email delivery is not set up",
    "FAILED": "the mail service refused it or could not be reached",
    "LOCAL_CAPTURED": "email delivery is not set up on this server",
}

# Postmark bounce types that mean "try again later", not "refused" (postmarkapp.com/developer/api/bounce-api).
_TEMPORARY_BOUNCES = {"Transient", "SoftBounce", "DnsError"}
_IGNORED_BOUNCES = {"AutoResponder", "Subscribe", "ChallengeVerification", "OpenRelayTest"}


class DeliveryError(ValueError):
    pass


@dataclass(frozen=True)
class DeliveryState:
    code: str
    label: str          # one short phrase for a list, e.g. "Delivered" or "Bounced: mailbox not found"
    detail: str = ""    # the mail service's own words, when there are any
    at: Optional[datetime] = None
    checkable: bool = False  # Postmark can be asked about it now


def _config(name: str) -> str:
    import os

    value = current_app.config.get(name)
    if value is None:
        value = os.environ.get(name, "")
    return str(value or "").strip()


def _parse_time(value) -> Optional[datetime]:
    if not value:
        return None
    text = str(value).strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        # Postmark sometimes sends seven fractional digits; keep the first six.
        head, dot, rest = text.partition(".")
        if not dot:
            return None
        digits = "".join(ch for ch in rest if ch.isdigit())
        zone = rest[len(digits):]
        try:
            parsed = datetime.fromisoformat(f"{head}.{digits[:6]}{zone}")
        except ValueError:
            return None
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
    return parsed


def _clip(text, limit=300) -> Optional[str]:
    text = " ".join(str(text or "").split())
    return text[:limit] or None


def _record(message: TransactionalMessage, *, event: str, detail, occurred_at, source: str, key: str) -> bool:
    """Add one event unless that same report is already here. No commit."""
    key = key[:200]
    if TransactionalDeliveryEvent.query.filter_by(event_key=key).first() is not None:
        return False
    db.session.add(TransactionalDeliveryEvent(
        message_id=message.id, provider=message.provider, event=event, detail=_clip(detail),
        occurred_at=occurred_at, source=source, event_key=key))
    db.session.flush()
    return True


def _postmark_message(message_id) -> Optional[TransactionalMessage]:
    if not message_id:
        return None
    return (TransactionalMessage.query.filter_by(provider=PROVIDER_POSTMARK, provider_message_id=str(message_id))
            .order_by(TransactionalMessage.id.desc()).first())


# ------------------------------------------------------------------ Postmark webhooks


def webhook_configured() -> bool:
    return bool(_config("POSTMARK_WEBHOOK_USERNAME") and _config("POSTMARK_WEBHOOK_PASSWORD"))


def webhook_authorized(authorization) -> bool:
    """HTTP Basic credentials Postmark sends with each webhook (set in the webhook URL). Constant-time."""
    if not webhook_configured() or authorization is None:
        return False
    user_ok = hmac.compare_digest((authorization.username or "").encode(), _config("POSTMARK_WEBHOOK_USERNAME").encode())
    pass_ok = hmac.compare_digest((authorization.password or "").encode(), _config("POSTMARK_WEBHOOK_PASSWORD").encode())
    return user_ok and pass_ok


def record_postmark_webhook(payload: dict) -> str:
    """One Postmark Delivery, Bounce or SpamComplaint webhook. Returns what was done (for the response only)."""
    if not isinstance(payload, dict):
        raise DeliveryError("not a Postmark webhook")
    kind = payload.get("RecordType")
    message = _postmark_message(payload.get("MessageID"))
    if message is None:
        return "unknown message"
    if kind == "Delivery":
        added = _record(message, event=EVENT_DELIVERED,
                        detail=payload.get("Details") or "Delivered", occurred_at=_parse_time(payload.get("DeliveredAt")),
                        source=SOURCE_WEBHOOK, key=f"pm:delivered:{payload.get('MessageID')}")
    elif kind == "Bounce":
        bounce_type = str(payload.get("Type") or "")
        if bounce_type in _IGNORED_BOUNCES:
            return "ignored"
        event = EVENT_DELAYED if bounce_type in _TEMPORARY_BOUNCES else EVENT_BOUNCED
        reason = payload.get("Description") or payload.get("Name") or bounce_type
        if payload.get("Details"):
            reason = f"{reason} ({payload.get('Details')})"
        added = _record(message, event=event, detail=reason, occurred_at=_parse_time(payload.get("BouncedAt")),
                        source=SOURCE_WEBHOOK, key=f"pm:bounce:{payload.get('ID') or payload.get('MessageID')}")
    elif kind == "SpamComplaint":
        added = _record(message, event=EVENT_SPAM_COMPLAINT, detail="The recipient marked it as spam",
                        occurred_at=_parse_time(payload.get("BouncedAt")), source=SOURCE_WEBHOOK,
                        key=f"pm:spam:{payload.get('ID') or payload.get('MessageID')}")
    else:
        return "ignored"
    db.session.commit()
    return "recorded" if added else "already recorded"


# ------------------------------------------------------------------ Check delivery (Postmark message details)


def _details(provider_message_id: str) -> dict:
    token = _config("POSTMARK_SERVER_TOKEN")
    if not token:
        raise DeliveryError("Postmark is not set up on this server.")
    opener = current_app.config.get("POSTMARK_URLOPEN") or urllib.request.urlopen
    request = urllib.request.Request(
        POSTMARK_DETAILS_ENDPOINT.format(id=urllib.parse.quote(str(provider_message_id), safe="")),
        method="GET", headers={"Accept": "application/json", "X-Postmark-Server-Token": token})
    try:
        with opener(request, timeout=15) as response:
            return json.loads((response.read() or b"{}").decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise DeliveryError(f"Postmark answered {exc.code}.") from exc
    except (OSError, ValueError) as exc:
        raise DeliveryError("Postmark could not be reached.") from exc


def check_with_postmark(message: TransactionalMessage) -> int:
    """Ask Postmark what happened to one accepted message; record anything new. Returns how many events were
    added. Raises DeliveryError when Postmark cannot be asked."""
    if message.provider != PROVIDER_POSTMARK or message.status != STATUS_ACCEPTED or not message.provider_message_id:
        return 0
    data = _details(message.provider_message_id)
    added = 0
    for item in data.get("MessageEvents") or []:
        kind = item.get("Type")
        details = item.get("Details") or {}
        at = _parse_time(item.get("ReceivedAt"))
        stamp = item.get("ReceivedAt") or ""
        if kind == "Delivered":
            text = details.get("DeliveryMessage") or "Delivered"
            if details.get("DestinationServer"):
                text = f"{text} ({details.get('DestinationServer')})"
            added += _record(message, event=EVENT_DELIVERED, detail=text, occurred_at=at, source=SOURCE_CHECK,
                             key=f"pm:delivered:{message.provider_message_id}")
        elif kind == "Bounced":
            key = f"pm:bounce:{details.get('BounceID') or message.provider_message_id + ':' + stamp}"
            added += _record(message, event=EVENT_BOUNCED, detail=details.get("Summary") or "Bounced",
                             occurred_at=at, source=SOURCE_CHECK, key=key)
        elif kind == "Transient":
            added += _record(message, event=EVENT_DELAYED,
                             detail=details.get("DeliveryMessage") or details.get("Summary") or "Delayed",
                             occurred_at=at, source=SOURCE_CHECK, key=f"pm:delayed:{message.provider_message_id}:{stamp}")
        elif kind == "SpamComplaint":
            added += _record(message, event=EVENT_SPAM_COMPLAINT, detail="The recipient marked it as spam",
                             occurred_at=at, source=SOURCE_CHECK, key=f"pm:spam:{message.provider_message_id}")
    db.session.commit()
    return added


def check_waiting(messages: Iterable[TransactionalMessage]) -> tuple[int, Optional[str]]:
    """Check every message still waiting. Returns (events added, the first problem asking Postmark, if any)."""
    added, problem = 0, None
    for message in messages:
        if state_of(message).code not in (STATE_WAITING, STATE_DELAYED):
            continue
        try:
            added += check_with_postmark(message)
        except DeliveryError as exc:
            problem = problem or str(exc)
    return added, problem


# ------------------------------------------------------------------ what people see


def _not_sent_reason(status: str) -> str:
    return NOT_SENT_REASONS.get(status, "it could not be sent")


def state_of(message: TransactionalMessage) -> DeliveryState:
    from app.services.password_reset import _delivered

    if message.status == STATUS_LOCAL_CAPTURED and _delivered(message.status):
        return DeliveryState(STATE_CAPTURED, "Kept on this computer (development)")
    if message.status != STATUS_ACCEPTED:
        reason = _not_sent_reason(message.status)
        return DeliveryState(STATE_NOT_SENT, f"Not sent: {reason}", detail=reason)
    events = (TransactionalDeliveryEvent.query.filter_by(message_id=message.id)
              .order_by(TransactionalDeliveryEvent.id.asc()).all())
    final = [e for e in events if e.event in (EVENT_BOUNCED, EVENT_SPAM_COMPLAINT)]
    if final:
        e = final[-1]
        if e.event == EVENT_SPAM_COMPLAINT:
            return DeliveryState(STATE_BOUNCED, "Marked as spam by the recipient", detail=e.detail or "", at=e.occurred_at)
        return DeliveryState(STATE_BOUNCED, f"Bounced: {e.detail or 'refused'}", detail=e.detail or "", at=e.occurred_at)
    delivered = [e for e in events if e.event == EVENT_DELIVERED]
    if delivered:
        e = delivered[-1]
        return DeliveryState(STATE_DELIVERED, "Delivered", detail=e.detail or "", at=e.occurred_at)
    if message.provider == PROVIDER_SMTP:
        return DeliveryState(STATE_UNCONFIRMABLE, "Handed to the server's mail system (delivery cannot be confirmed)")
    checkable = message.provider == PROVIDER_POSTMARK and bool(message.provider_message_id)
    delayed = [e for e in events if e.event == EVENT_DELAYED]
    if delayed:
        e = delayed[-1]
        return DeliveryState(STATE_DELAYED, "Delayed: the mail service is still trying", detail=e.detail or "",
                             at=e.occurred_at, checkable=checkable)
    return DeliveryState(STATE_WAITING, "Waiting for the mail service to confirm delivery", checkable=checkable)
