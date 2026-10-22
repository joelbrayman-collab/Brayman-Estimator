"""Text messages (SMS): delivery schedule notices (Joel, 17 Oct 2026) and crew schedule-change notices
(Joel, 22 Oct 2026, mandatory V1). One sending path for every text CalibraytAI sends.

Twilio, configured only through environment settings (never in the code or the database):

* ``TRANSACTIONAL_SMS_PROVIDER=twilio`` switches real sending on. Anything else (the default) sends
  nothing: each text is recorded as NOT_CONFIGURED so the office can see it was not sent.
* ``TWILIO_ACCOUNT_SID`` and ``TWILIO_AUTH_TOKEN``, and the sender: ``TWILIO_MESSAGING_SERVICE_SID``
  (preferred) or ``TWILIO_FROM_NUMBER`` (E.164, e.g. +16135550100).
* ``TRANSACTIONAL_SMS_UAT_ALLOWLIST`` (optional): comma-separated mobile numbers. When set, only those
  numbers get texts; the rest are recorded as SKIPPED_ALLOWLIST (test before switching on for everyone).
* ``PUBLIC_BASE_URL``: the address Twilio calls back with delivery status (/sms/twilio/status).

A text goes only to a person who has a mobile number and recorded consent (``NotificationContact``);
every consent change is kept in ``sms_consent_events``. Tests use a fake transport (``TEXT_TRANSPORT``)
or a fake Twilio opener (``TWILIO_URLOPEN``); no test reaches Twilio. The training site never sends.
Operation and the Twilio references: docs/operations/sms-notifications.md.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from typing import Iterable, Optional

from flask import current_app

from app import db
from app.models.sms_notification import (
    CONSENT_NUMBER_CHANGED,
    CONSENT_OPTED_IN,
    CONSENT_OPTED_OUT,
    METHOD_PROVIDER,
    METHOD_REPLY_START,
    METHOD_REPLY_STOP,
    METHOD_SELF_ACCOUNT,
    SmsConsentEvent,
    SmsDeliveryEvent,
    SmsTextMessageDetail,
)
from app.models.supplier_portal import (
    TEXT_FAILED,
    TEXT_LOCAL_CAPTURED,
    TEXT_NOT_CONFIGURED,
    TEXT_SENT,
    NotificationContact,
    TextMessage,
)

MAX_BODY = 480  # about three SMS segments

# Statuses a text can reach after it is sent (from Twilio's delivery reports).
TEXT_DELIVERED = "DELIVERED"
TEXT_UNDELIVERED = "UNDELIVERED"
TEXT_SKIPPED_ALLOWLIST = "SKIPPED_ALLOWLIST"
# Statuses the office may retry. The settings ones (not configured, allowlist) are retried once the
# settings are fixed; a retry re-checks consent first.
RETRYABLE_STATUSES = (TEXT_FAILED, TEXT_UNDELIVERED, TEXT_NOT_CONFIGURED, TEXT_SKIPPED_ALLOWLIST)
FAILED_STATUSES = (TEXT_FAILED, TEXT_UNDELIVERED)

# Twilio's MessageStatus -> ours. queued/accepted/sending/scheduled: Twilio has it; sent: handed to the carrier.
_TWILIO_STATUS = {
    "accepted": TEXT_SENT,
    "scheduled": TEXT_SENT,
    "queued": TEXT_SENT,
    "sending": TEXT_SENT,
    "sent": TEXT_SENT,
    "delivered": TEXT_DELIVERED,
    "read": TEXT_DELIVERED,
    "undelivered": TEXT_UNDELIVERED,
    "failed": TEXT_FAILED,
    "canceled": TEXT_FAILED,
}
# Callbacks can arrive out of order (Twilio docs): never move back from a final status.
_RANK = {TEXT_SENT: 1, TEXT_DELIVERED: 3, TEXT_UNDELIVERED: 3, TEXT_FAILED: 3}

TWILIO_OPTED_OUT_ERROR = "21610"  # "Attempt to send to unsubscribed recipient"
# Opt-out and opt-in words Twilio recognizes by default on long codes and toll-free numbers (English and
# French, for Canada). Twilio itself answers them and blocks further texts; we record the change too.
STOP_WORDS = {"STOP", "STOPALL", "UNSUBSCRIBE", "CANCEL", "END", "QUIT", "OPTOUT", "REVOKE", "ARRET", "ARRÊT"}
START_WORDS = {"START", "UNSTOP", "YES"}

CONSENT_WORDING = ("I agree to receive work schedule text messages from my employer through CalibraytAI at this "
                   "number. Message and data rates may apply. Reply STOP to stop.")


class TextSettingsError(Exception):
    """A mobile number or consent that cannot be saved."""


class TextRetryError(Exception):
    """A text that cannot be sent again (shown to the office)."""


def normalize_phone(raw: str) -> str:
    """North American numbers to E.164 (+1XXXXXXXXXX); other numbers must already start with +."""
    text = (raw or "").strip()
    if not text:
        return ""
    digits = re.sub(r"\D", "", text)
    if text.startswith("+") and 8 <= len(digits) <= 15:
        return "+" + digits
    if len(digits) == 10:
        return "+1" + digits
    if len(digits) == 11 and digits.startswith("1"):
        return "+" + digits
    raise TextSettingsError("Enter a mobile number like 613-555-0100.")


def masked_phone(phone: Optional[str]) -> str:
    """For office lists: the last four digits only."""
    digits = re.sub(r"\D", "", phone or "")
    return f"•••-{digits[-4:]}" if len(digits) >= 4 else ""


def contact_for(user) -> Optional[NotificationContact]:
    if user is None or not getattr(user, "id", None):
        return None
    return NotificationContact.query.filter_by(user_id=user.id).first()


def has_text_consent(user) -> bool:
    contact = contact_for(user)
    return bool(contact is not None and contact.sms_opt_in and contact.mobile_phone)


def _actor_name(actor) -> str:
    return (getattr(actor, "display_name", None) or getattr(actor, "email", None) or "System")[:150]


def _record_consent(user_id, organization_id, action, method, phone, actor, note=None) -> None:
    db.session.add(SmsConsentEvent(
        user_id=user_id, organization_id=organization_id, action=action, method=method, mobile_phone=phone or None,
        recorded_by_user_id=getattr(actor, "id", None) if actor is not None else None,
        recorded_by_display_name=_actor_name(actor) if actor is not None else "Text message reply",
        note=(note or "")[:240] or None, created_at=datetime.utcnow()))


def save_contact(user, *, mobile_phone: str, opt_in: bool, method: str = METHOD_SELF_ACCOUNT, recorded_by=None,
                 organization_id: Optional[str] = None, note: Optional[str] = None) -> NotificationContact:
    """Save a person's mobile number and consent, and record what changed in the consent history.

    ``recorded_by`` is who made the change (the person themselves by default; the owner or a System
    Administrator when entered on the worker's behalf, with ``note`` saying how consent was given)."""
    phone = normalize_phone(mobile_phone)
    if opt_in and not phone:
        raise TextSettingsError("Enter your mobile number to receive texts.")
    actor = recorded_by if recorded_by is not None else user
    contact = contact_for(user) or NotificationContact(user_id=user.id, sms_opt_in=False)
    was_in, old_phone = bool(contact.sms_opt_in), contact.mobile_phone
    now = datetime.utcnow()
    now_in = bool(opt_in and phone)
    if now_in and not was_in:
        contact.opted_in_at = now
        _record_consent(user.id, organization_id, CONSENT_OPTED_IN, method, phone, actor, note)
    elif now_in and was_in and phone != old_phone:
        _record_consent(user.id, organization_id, CONSENT_NUMBER_CHANGED, method, phone, actor, note)
    if was_in and not now_in:
        contact.opted_out_at = now
        _record_consent(user.id, organization_id, CONSENT_OPTED_OUT, method, phone or old_phone, actor, note)
    contact.mobile_phone = phone or None
    contact.sms_opt_in = now_in
    contact.updated_at = now
    db.session.add(contact)
    db.session.commit()
    return contact


def consent_history(user_id: int, *, limit: int = 20):
    return (SmsConsentEvent.query.filter_by(user_id=user_id)
            .order_by(SmsConsentEvent.created_at.desc(), SmsConsentEvent.id.desc()).limit(limit).all())


# ------------------------------------------------------------------ settings

def _setting(name: str) -> str:
    value = current_app.config.get(name)
    if value in (None, ""):
        value = os.environ.get(name, "")
    return str(value or "").strip()


def sms_provider() -> str:
    return _setting("TRANSACTIONAL_SMS_PROVIDER").lower() or "off"


def texting_configured() -> bool:
    """Twilio account settings and a sender are present (switching on is TRANSACTIONAL_SMS_PROVIDER)."""
    sender = _setting("TWILIO_MESSAGING_SERVICE_SID") or _setting("TWILIO_FROM_NUMBER")
    return bool(_setting("TWILIO_ACCOUNT_SID") and _setting("TWILIO_AUTH_TOKEN") and sender)


def texting_live() -> bool:
    return sms_provider() == "twilio" and texting_configured() and not _training_site()


def sms_allowlist() -> set:
    raw = _setting("TRANSACTIONAL_SMS_UAT_ALLOWLIST")
    out = set()
    for part in raw.split(","):
        try:
            phone = normalize_phone(part)
        except TextSettingsError:
            continue
        if phone:
            out.add(phone)
    return out


def _training_site() -> bool:
    try:
        from app.training.service import enabled

        return enabled(current_app)
    except Exception:  # pragma: no cover - the training module always imports
        return False


def status_callback_url() -> str:
    base = _setting("PUBLIC_BASE_URL").rstrip("/")
    return f"{base}/sms/twilio/status" if base.startswith("https://") else ""


def settings_summary() -> dict:
    """What the office page shows about sending (names only, never values)."""
    return {
        "provider": sms_provider(),
        "configured": texting_configured(),
        "live": texting_live(),
        "allowlist_count": len(sms_allowlist()),
        "sender": ("messaging service" if _setting("TWILIO_MESSAGING_SERVICE_SID")
                   else ("phone number" if _setting("TWILIO_FROM_NUMBER") else "")),
        "callback": bool(status_callback_url()),
        "training_site": _training_site(),
    }


# ------------------------------------------------------------------ sending

def send_text_to_user(user, body: str, *, related_type: str = "", related_id=None,
                      organization_id: Optional[str] = None, purpose: Optional[str] = None) -> Optional[TextMessage]:
    contact = contact_for(user)
    if contact is None or not contact.sms_opt_in or not contact.mobile_phone:
        return None
    return send_text(contact.mobile_phone, body, user_id=user.id, related_type=related_type, related_id=related_id,
                     organization_id=organization_id, purpose=purpose)


def send_text(phone: str, body: str, *, user_id=None, related_type: str = "", related_id=None,
              organization_id: Optional[str] = None, purpose: Optional[str] = None,
              retry_of: Optional[TextMessage] = None, retried_by=None) -> TextMessage:
    text = (body or "").strip()
    if len(text) > MAX_BODY:
        text = text[: MAX_BODY - 1] + "…"
    now = datetime.utcnow()
    row = TextMessage(user_id=user_id, to_phone=phone, body=text, provider="twilio",
                      related_type=(related_type or "")[:40] or None,
                      related_id=None if related_id is None else str(related_id)[:80], created_at=now)
    detail = SmsTextMessageDetail(organization_id=organization_id, purpose=(purpose or related_type or "")[:40] or None,
                                  created_at=now)
    if retry_of is not None:
        detail.retry_of_text_message_id = retry_of.id
        detail.retried_by_user_id = getattr(retried_by, "id", None)
        detail.retried_by_display_name = _actor_name(retried_by) if retried_by is not None else None
    provider_status = None
    allow = sms_allowlist()
    transport = current_app.config.get("TEXT_TRANSPORT")
    if allow and phone not in allow:
        row.provider, row.status, row.error_code = "none", TEXT_SKIPPED_ALLOWLIST, "NOT_ON_SMS_ALLOWLIST"
    elif transport is not None:  # tests: a fake transport
        row.provider = "fake"
        try:
            row.provider_message_id = str(transport(phone, text))
            row.status, provider_status = TEXT_SENT, "queued"
        except Exception as exc:
            row.status, row.error_code = TEXT_FAILED, type(exc).__name__[:80]
    elif _training_site():
        row.provider, row.status, row.error_code = "none", TEXT_NOT_CONFIGURED, "TRAINING_SITE_NEVER_TEXTS"
    elif current_app.config.get("TESTING") and not texting_configured():
        row.provider, row.status = "local", TEXT_LOCAL_CAPTURED
    elif not texting_configured():
        row.status, row.error_code = TEXT_NOT_CONFIGURED, "TWILIO_SETTINGS_MISSING"
    elif sms_provider() != "twilio":
        row.status, row.error_code = TEXT_NOT_CONFIGURED, "SMS_PROVIDER_OFF"
    else:
        row.status, row.provider_message_id, row.error_code, provider_status = _twilio(phone, text)
    detail.provider_status = provider_status
    detail.status_updated_at = now
    db.session.add(row)
    db.session.flush()
    detail.text_message_id = row.id
    db.session.add(detail)
    if row.status == TEXT_FAILED and (row.error_code or "").endswith("_" + TWILIO_OPTED_OUT_ERROR):
        _opt_out_number(phone, METHOD_PROVIDER, note="Twilio error 21610: the number has opted out (STOP)")
    db.session.commit()
    return row


def _twilio(to_phone: str, body: str):
    """One Twilio Messages API call. Returns (status, provider_message_id, error_code, provider_status)."""
    sid, token = _setting("TWILIO_ACCOUNT_SID"), _setting("TWILIO_AUTH_TOKEN")
    url = f"https://api.twilio.com/2010-04-01/Accounts/{urllib.parse.quote(sid)}/Messages.json"
    fields = {"To": to_phone, "Body": body}
    service = _setting("TWILIO_MESSAGING_SERVICE_SID")
    if service:
        fields["MessagingServiceSid"] = service
    else:
        fields["From"] = _setting("TWILIO_FROM_NUMBER")
    callback = status_callback_url()
    if callback:
        fields["StatusCallback"] = callback
    request = urllib.request.Request(url, data=urllib.parse.urlencode(fields).encode(), method="POST")
    request.add_header("Authorization", "Basic " + base64.b64encode(f"{sid}:{token}".encode()).decode())
    opener = current_app.config.get("TWILIO_URLOPEN") or urllib.request.urlopen
    try:
        with opener(request, timeout=10) as response:
            payload = json.loads(response.read().decode() or "{}")
        provider_status = str(payload.get("status") or "queued")[:30]
        status = _TWILIO_STATUS.get(provider_status, TEXT_SENT)
        error = str(payload.get("error_code"))[:80] if payload.get("error_code") else None
        return status, str(payload.get("sid") or "")[:80] or None, error, provider_status
    except urllib.error.HTTPError as exc:
        try:
            code = json.loads(exc.read().decode() or "{}").get("code")
        except Exception:
            code = None
        return TEXT_FAILED, None, f"HTTP_{exc.code}" + (f"_{code}" if code else ""), None
    except Exception as exc:
        return TEXT_FAILED, None, type(exc).__name__[:80], None


def detail_for(text: TextMessage) -> Optional[SmsTextMessageDetail]:
    return SmsTextMessageDetail.query.filter_by(text_message_id=text.id).first()


def latest_attempt(text: TextMessage) -> TextMessage:
    """Follow the retry chain to the newest attempt."""
    current = text
    for _ in range(50):
        nxt = SmsTextMessageDetail.query.filter_by(retry_of_text_message_id=current.id).first()
        if nxt is None:
            return current
        current = db.session.get(TextMessage, nxt.text_message_id)
    return current


def retry_text(text: TextMessage, *, actor, organization_id: Optional[str] = None) -> TextMessage:
    """Send a failed or not-sent text again, once. Consent is checked again first."""
    if latest_attempt(text).id != text.id:
        raise TextRetryError("This text was already sent again. See the newest attempt.")
    if text.status not in RETRYABLE_STATUSES:
        raise TextRetryError("Only a failed or not-sent text can be sent again.")
    if text.user_id is not None:
        from app.models.user import User

        user = db.session.get(User, text.user_id)
        contact = contact_for(user)
        if contact is None or not contact.sms_opt_in or not contact.mobile_phone:
            raise TextRetryError("This person no longer agrees to texts (or has no mobile number). Nothing was sent.")
        phone = contact.mobile_phone  # their current number
    else:
        phone = text.to_phone
    from sqlalchemy.exc import IntegrityError

    try:
        return send_text(phone, text.body, user_id=text.user_id, related_type=text.related_type or "",
                         related_id=text.related_id, organization_id=organization_id,
                         purpose=(detail_for(text).purpose if detail_for(text) else None), retry_of=text,
                         retried_by=actor)
    except IntegrityError:  # two presses at once: the unique retry link refuses the second
        db.session.rollback()
        raise TextRetryError("This text was already sent again. See the newest attempt.")


# ------------------------------------------------------------------ Twilio callbacks

def twilio_signature(url: str, params: Iterable, auth_token: str) -> str:
    """Twilio's documented request signature: the full URL, then each POST field name and value sorted
    by name (case-sensitive), no separators; HMAC-SHA1 with the auth token; Base64.
    https://www.twilio.com/docs/usage/security#validating-requests"""
    data = url
    for key, value in sorted(params, key=lambda kv: kv[0]):
        data += f"{key}{value}"
    digest = hmac.new(auth_token.encode("utf-8"), data.encode("utf-8"), hashlib.sha1).digest()
    return base64.b64encode(digest).decode("ascii")


def _with_and_without_port(url: str) -> list:
    """Twilio keeps an explicit port for SMS webhooks; a proxy may add or drop one. Try both forms."""
    parts = urllib.parse.urlsplit(url)
    out = [url]
    default = {"https": 443, "http": 80}.get(parts.scheme)
    host = parts.hostname or ""
    if parts.port:
        out.append(urllib.parse.urlunsplit((parts.scheme, host, parts.path, parts.query, parts.fragment)))
    elif default:
        out.append(urllib.parse.urlunsplit((parts.scheme, f"{host}:{default}", parts.path, parts.query, parts.fragment)))
    return out


def verify_twilio_request(request) -> bool:
    """True only when X-Twilio-Signature matches the auth token for the address Twilio called."""
    token = _setting("TWILIO_AUTH_TOKEN")
    signature = request.headers.get("X-Twilio-Signature", "")
    if not token or not signature:
        return False
    params = list(request.form.items(multi=True))
    candidates = []
    base = _setting("PUBLIC_BASE_URL").rstrip("/")
    query = request.query_string.decode("utf-8", "replace")
    if base:  # behind Render's proxy the request URL may say http://; the configured address is what Twilio used
        candidates.append(base + request.path + (f"?{query}" if query else ""))
    candidates.append(request.url)
    for url in candidates:
        for form in _with_and_without_port(url):
            if hmac.compare_digest(twilio_signature(form, params, token), signature):
                return True
    return False


def apply_status_callback(form) -> Optional[TextMessage]:
    """Record one verified delivery report. Replays and out-of-order reports never move a status back."""
    sid = (form.get("MessageSid") or form.get("SmsSid") or "").strip()[:80]
    raw = (form.get("MessageStatus") or form.get("SmsStatus") or "").strip().lower()[:30]
    error = (form.get("ErrorCode") or "").strip()[:20] or None
    if not sid or not raw:
        return None
    text = TextMessage.query.filter_by(provider_message_id=sid).first()
    applied = False
    if text is not None:
        new = _TWILIO_STATUS.get(raw)
        detail = detail_for(text)
        now = datetime.utcnow()
        if new and _RANK.get(new, 0) > _RANK.get(text.status, 0):
            text.status = new
            if error and new in FAILED_STATUSES:
                text.error_code = f"TWILIO_{error}"[:80]
            applied = True
        if detail is not None and (applied or detail.provider_status is None):
            detail.provider_status = raw
            detail.status_updated_at = now
            if new == TEXT_DELIVERED and detail.delivered_at is None:
                detail.delivered_at = now
        if error == TWILIO_OPTED_OUT_ERROR:
            _opt_out_number(text.to_phone, METHOD_PROVIDER, note="Twilio error 21610: the number has opted out (STOP)")
    db.session.add(SmsDeliveryEvent(text_message_id=text.id if text is not None else None, provider_message_id=sid,
                                    provider_status=raw, error_code=error, applied=applied,
                                    received_at=datetime.utcnow()))
    db.session.commit()
    return text


def _opt_out_number(phone: str, method: str, *, note: str) -> int:
    count = 0
    for contact in NotificationContact.query.filter_by(mobile_phone=phone, sms_opt_in=True).all():
        contact.sms_opt_in = False
        contact.opted_out_at = datetime.utcnow()
        contact.updated_at = contact.opted_out_at
        _record_consent(contact.user_id, None, CONSENT_OPTED_OUT, method, phone, None, note)
        count += 1
    return count


def apply_inbound_reply(form) -> str:
    """A verified reply to our number. STOP-type words record an opt-out; START after a STOP records the
    opt-in again (only for someone whose last change was that STOP reply). Other replies are ignored:
    nobody reads replies, which the consent wording and Field page say."""
    try:
        phone = normalize_phone(form.get("From") or "")
    except TextSettingsError:
        return "ignored"
    word = (form.get("Body") or "").strip().upper()
    word = re.sub(r"[^A-ZÊ]", "", word)
    if word in STOP_WORDS:
        _opt_out_number(phone, METHOD_REPLY_STOP, note=f"Replied {word}")
        db.session.commit()
        return "opted_out"
    if word in START_WORDS:
        count = 0
        for contact in NotificationContact.query.filter_by(mobile_phone=phone, sms_opt_in=False).all():
            last = (SmsConsentEvent.query.filter_by(user_id=contact.user_id)
                    .order_by(SmsConsentEvent.id.desc()).first())
            if last is not None and last.method == METHOD_REPLY_STOP:
                contact.sms_opt_in = True
                contact.opted_in_at = datetime.utcnow()
                contact.updated_at = contact.opted_in_at
                _record_consent(contact.user_id, None, CONSENT_OPTED_IN, METHOD_REPLY_START, phone, None,
                                f"Replied {word} after STOP")
                count += 1
        db.session.commit()
        return "opted_in" if count else "ignored"
    return "ignored"
