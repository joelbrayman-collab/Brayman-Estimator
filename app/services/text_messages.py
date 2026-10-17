"""Text messages (SMS) for delivery schedule notices (Joel, 17 Oct 2026).

Twilio, configured only through environment settings set by Joel in Render:
TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER. Nothing secret is in the code.
A text goes only to a person who entered a mobile number and ticked the consent box.
Without settings, the text is recorded as NOT_CONFIGURED and email still goes out.
"""

from __future__ import annotations

import base64
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from typing import Optional

from flask import current_app

from app import db
from app.models.supplier_portal import (
    TEXT_FAILED,
    TEXT_LOCAL_CAPTURED,
    TEXT_NOT_CONFIGURED,
    TEXT_SENT,
    NotificationContact,
    TextMessage,
)

MAX_BODY = 480  # about three SMS segments


class TextSettingsError(Exception):
    """A mobile number or consent that cannot be saved."""


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


def contact_for(user) -> Optional[NotificationContact]:
    if user is None or not getattr(user, "id", None):
        return None
    return NotificationContact.query.filter_by(user_id=user.id).first()


def save_contact(user, *, mobile_phone: str, opt_in: bool) -> NotificationContact:
    phone = normalize_phone(mobile_phone)
    if opt_in and not phone:
        raise TextSettingsError("Enter your mobile number to receive texts.")
    contact = contact_for(user) or NotificationContact(user_id=user.id, sms_opt_in=False)
    now = datetime.utcnow()
    if opt_in and not contact.sms_opt_in:
        contact.opted_in_at = now
    if not opt_in and contact.sms_opt_in:
        contact.opted_out_at = now
    contact.mobile_phone = phone or None
    contact.sms_opt_in = bool(opt_in and phone)
    contact.updated_at = now
    db.session.add(contact)
    db.session.commit()
    return contact


def _setting(name: str) -> str:
    value = current_app.config.get(name)
    if value in (None, ""):
        value = os.environ.get(name, "")
    return (value or "").strip()


def texting_configured() -> bool:
    return all(_setting(n) for n in ("TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_FROM_NUMBER"))


def send_text_to_user(user, body: str, *, related_type: str = "", related_id=None) -> Optional[TextMessage]:
    contact = contact_for(user)
    if contact is None or not contact.sms_opt_in or not contact.mobile_phone:
        return None
    return send_text(contact.mobile_phone, body, user_id=user.id, related_type=related_type, related_id=related_id)


def send_text(phone: str, body: str, *, user_id=None, related_type: str = "", related_id=None) -> TextMessage:
    text = (body or "").strip()
    if len(text) > MAX_BODY:
        text = text[: MAX_BODY - 1] + "…"
    row = TextMessage(user_id=user_id, to_phone=phone, body=text, provider="twilio",
                      related_type=(related_type or "")[:40] or None,
                      related_id=None if related_id is None else str(related_id)[:80], created_at=datetime.utcnow())
    transport = current_app.config.get("TEXT_TRANSPORT")
    if transport is not None:  # tests: a fake transport
        row.provider = "fake"
        try:
            row.provider_message_id = str(transport(phone, text))
            row.status = TEXT_SENT
        except Exception as exc:  # pragma: no cover - fake transport failure
            row.status, row.error_code = TEXT_FAILED, type(exc).__name__
    elif current_app.config.get("TESTING") and not texting_configured():
        row.provider, row.status = "local", TEXT_LOCAL_CAPTURED
    elif not texting_configured():
        row.status, row.error_code = TEXT_NOT_CONFIGURED, "TWILIO_SETTINGS_MISSING"
    else:
        row.status, row.provider_message_id, row.error_code = _twilio(phone, text)
    db.session.add(row)
    db.session.commit()
    return row


def _twilio(to_phone: str, body: str):
    sid, token, sender = (_setting("TWILIO_ACCOUNT_SID"), _setting("TWILIO_AUTH_TOKEN"), _setting("TWILIO_FROM_NUMBER"))
    url = f"https://api.twilio.com/2010-04-01/Accounts/{urllib.parse.quote(sid)}/Messages.json"
    data = urllib.parse.urlencode({"To": to_phone, "From": sender, "Body": body}).encode()
    request = urllib.request.Request(url, data=data, method="POST")
    request.add_header("Authorization", "Basic " + base64.b64encode(f"{sid}:{token}".encode()).decode())
    opener = current_app.config.get("TWILIO_URLOPEN") or urllib.request.urlopen
    try:
        with opener(request, timeout=10) as response:
            payload = json.loads(response.read().decode() or "{}")
        return TEXT_SENT, str(payload.get("sid") or "")[:80] or None, None
    except urllib.error.HTTPError as exc:
        try:
            code = json.loads(exc.read().decode() or "{}").get("code")
        except Exception:
            code = None
        return TEXT_FAILED, None, f"HTTP_{exc.code}" + (f"_{code}" if code else "")
    except Exception as exc:
        return TEXT_FAILED, None, type(exc).__name__[:80]
