"""Schedule-change text notices (Joel, 22 Oct 2026, mandatory V1): office, Field and Twilio pages.

/schedule/text-notices                     office: recent notices and texts, status, failure reason, Retry.
                                           Anyone with scheduling authority (office members; never field-only).
/settings/people/<membership_id>/texts     owner / System Administrator: a worker's mobile number and consent,
                                           entered with the worker's agreement (who, when and how are recorded)
/field/text-messages                       the signed-in person's own number and consent (field.text_messages;
                                           the Field blueprint serves it with field_settings_view below)
/sms/twilio/status, /sms/twilio/inbound    PUBLIC: Twilio's delivery reports and replies (STOP). No sign-in,
                                           no CSRF token (Twilio cannot send one); every request must carry a
                                           valid X-Twilio-Signature for the configured auth token, else 403.
"""

from __future__ import annotations

from flask import Blueprint, Response, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user

from app import csrf, db
from app.models.sms_notification import (
    METHOD_OFFICE_ON_BEHALF,
    METHOD_SELF_FIELD,
    NOTICE_ERROR,
    SmsScheduleNotice,
    SmsTextMessageDetail,
)
from app.models.supplier_portal import TextMessage
from app.services.organizations import get_current_organization_id

sms_notifications_bp = Blueprint("sms_notifications", __name__)

NOTICE_LABELS = {
    "PENDING": "Waiting (sends after edits stop)",
    "SENDING": "Sending",
    "TEXTED": "Texted",
    "NO_CHANGE": "Not sent: no net change",
    "NO_CONSENT": "Not sent: no mobile number or consent",
    "SELF": "Not sent: they made the change",
    "ERROR": "Not sent: could not be prepared",
}
TEXT_LABELS = {
    "SENT": "Sent",
    "DELIVERED": "Delivered",
    "UNDELIVERED": "Not delivered",
    "FAILED": "Failed",
    "NOT_CONFIGURED": "Not sent: texting is not switched on",
    "SKIPPED_ALLOWLIST": "Not sent: number not on the test list",
    "LOCAL_CAPTURED": "Recorded only (test)",
}
ERROR_LABELS = {
    "TWILIO_SETTINGS_MISSING": "Twilio settings are missing",
    "SMS_PROVIDER_OFF": "Texting is switched off (TRANSACTIONAL_SMS_PROVIDER)",
    "NOT_ON_SMS_ALLOWLIST": "Only test numbers may get texts now",
    "TRAINING_SITE_NEVER_TEXTS": "The training site never sends texts",
    "HTTP_400_21610": "The worker replied STOP; Twilio blocks texts to them",
    "TWILIO_21610": "The worker replied STOP; Twilio blocks texts to them",
    "TWILIO_30003": "Phone unreachable or off",
    "TWILIO_30005": "Unknown or inactive number",
    "TWILIO_30006": "Landline or unreachable carrier",
    "TWILIO_30007": "Blocked by the carrier as spam",
    "TWILIO_30008": "Unknown carrier error",
    "TWILIO_30034": "Sender number not registered (A2P 10DLC)",
}
CHANGE_LABELS = {"MOVED": "Moved", "ADDED": "Added", "REMOVED": "Taken off", "CANCELLED": "Cancelled"}


@sms_notifications_bp.app_context_processor
def _sms_helpers():
    def sms_schedule_attention() -> int:
        """Failed or unsent schedule texts, for the office banners (0 for anyone without scheduling authority)."""
        try:
            if not getattr(current_user, "is_authenticated", False):
                return 0
            from app.services.access_domains import has_office_scheduling_authority
            from app.services.crew_notices import attention_count

            org_id = get_current_organization_id()
            if not has_office_scheduling_authority(current_user, org_id):
                return 0
            return attention_count(org_id)
        except Exception:
            return 0

    return {"sms_schedule_attention": sms_schedule_attention}


def _require_scheduling_authority():
    from app.services.access_domains import require_office_scheduling_authority

    return require_office_scheduling_authority()


# ------------------------------------------------------------------ office: notices and texts

@sms_notifications_bp.route("/schedule/text-notices")
def office_notices():
    denied = _require_scheduling_authority()
    if denied is not None:
        return denied
    from app.services.crew_notices import failed_texts, recent_notices, waiting_count, window_phrase, work_label
    from app.services.text_messages import latest_attempt, masked_phone, settings_summary

    org_id = get_current_organization_id()
    notices = recent_notices(org_id)
    text_ids = sorted({n.text_message_id for n in notices if n.text_message_id}, reverse=True)
    texts = []
    for text in TextMessage.query.filter(TextMessage.id.in_(text_ids or [0])).order_by(TextMessage.id.desc()):
        detail = SmsTextMessageDetail.query.filter_by(text_message_id=text.id).first()
        newest = latest_attempt(text)
        attempts = []
        current = newest
        while current is not None and current.id != text.id:
            attempts.append(current)
            prior = SmsTextMessageDetail.query.filter_by(text_message_id=current.id).first()
            current = db.session.get(TextMessage, prior.retry_of_text_message_id) if prior and prior.retry_of_text_message_id else None
        newest_detail = SmsTextMessageDetail.query.filter_by(text_message_id=newest.id).first()
        from app.models.user import User

        person = db.session.get(User, text.user_id) if text.user_id else None
        texts.append({"text": text, "name": person.display_name if person else "Worker", "detail": detail, "newest": newest, "newest_detail": newest_detail,
                      "retries": list(reversed(attempts)), "phone": masked_phone(newest.to_phone),
                      "notices": [n for n in notices if n.text_message_id == text.id],
                      "can_retry": newest.status in ("FAILED", "UNDELIVERED", "NOT_CONFIGURED", "SKIPPED_ALLOWLIST")})
    return render_template(
        "schedule/text_notices.html",
        notices=notices, texts=texts, settings=settings_summary(), waiting=waiting_count(org_id),
        failed=len(failed_texts(org_id)), errors=sum(1 for n in notices if n.status == NOTICE_ERROR),
        notice_labels=NOTICE_LABELS, text_labels=TEXT_LABELS, error_labels=ERROR_LABELS,
        change_labels=CHANGE_LABELS, work_label=work_label, window_phrase=window_phrase,
    )


@sms_notifications_bp.route("/schedule/text-notices/send-now", methods=["POST"])
def office_send_now():
    denied = _require_scheduling_authority()
    if denied is not None:
        return denied
    from app.services.crew_notices import send_due_notices

    summary = send_due_notices(organization_id=get_current_organization_id(), force=True)
    flash(f"Waiting notices sent: {summary['texted']} text(s). Not texted: {summary['no_consent']} without consent, "
          f"{summary['no_change']} with no net change, {summary['self']} changed by the worker.", "success")
    return redirect(url_for("sms_notifications.office_notices"))


@sms_notifications_bp.route("/schedule/text-notices/texts/<int:text_id>/retry", methods=["POST"])
def office_retry(text_id):
    denied = _require_scheduling_authority()
    if denied is not None:
        return denied
    from app.services.crew_notices import RELATED_TYPE
    from app.services.text_messages import TextRetryError, retry_text

    org_id = get_current_organization_id()
    detail = SmsTextMessageDetail.query.filter_by(text_message_id=text_id, organization_id=org_id).first()
    text = db.session.get(TextMessage, text_id) if detail is not None else None
    if text is None or text.related_type != RELATED_TYPE:
        abort(404)  # another company's text, or not a schedule text
    try:
        new = retry_text(text, actor=current_user, organization_id=org_id)
    except TextRetryError as exc:
        flash(str(exc), "error")
    else:
        flash(f"Sent again: {TEXT_LABELS.get(new.status, new.status)}.", "success" if new.status in ("SENT", "DELIVERED", "LOCAL_CAPTURED") else "error")
    return redirect(url_for("sms_notifications.office_notices"))


@sms_notifications_bp.route("/schedule/text-notices/<int:notice_id>/resend", methods=["POST"])
def office_resend_notice(notice_id):
    denied = _require_scheduling_authority()
    if denied is not None:
        return denied
    from app.services.crew_notices import resend_notice, send_due_notices

    org_id = get_current_organization_id()
    notice = SmsScheduleNotice.query.filter_by(id=notice_id, organization_id=org_id).first()
    if notice is None:
        abort(404)
    try:
        resend_notice(notice)
    except ValueError as exc:
        flash(str(exc), "error")
    else:
        send_due_notices(organization_id=org_id, force=True)
        flash("Notice sent again.", "success")
    return redirect(url_for("sms_notifications.office_notices"))


# ------------------------------------------------------------------ owner / administrator: a worker's consent

@sms_notifications_bp.route("/settings/people/<int:membership_id>/texts", methods=["POST"])
def person_texts(membership_id):
    from app.services.instance_authority import require_instance_owner_or_system_administrator
    from app.services.people_access import PERSON_NOT_FOUND, PeopleAccessError, get_person_access, membership_user
    from app.services.text_messages import TextSettingsError, save_contact

    denied = require_instance_owner_or_system_administrator()
    if denied is not None:
        return denied
    org_id = get_current_organization_id()
    try:
        get_person_access(organization_id=org_id, membership_id=membership_id, actor=current_user)
        user = membership_user(organization_id=org_id, membership_id=membership_id, actor=current_user)
    except PeopleAccessError as exc:
        abort(404 if str(exc) == PERSON_NOT_FOUND else 403)
    action = request.form.get("action")
    back = url_for("people_access.detail", membership_id=membership_id) + "#texts-heading"
    try:
        if action == "stop":
            from app.services.text_messages import contact_for

            contact = contact_for(user)
            save_contact(user, mobile_phone=(contact.mobile_phone if contact else "") or "", opt_in=False,
                         method=METHOD_OFFICE_ON_BEHALF, recorded_by=current_user, organization_id=org_id,
                         note=(request.form.get("how") or "Turned off by the office").strip()[:200])
            flash(f"Schedule texts turned off for {user.display_name}.", "success")
            return redirect(back)
        if request.form.get("consent") != "yes":
            raise TextSettingsError(f"Confirm that {user.display_name} agreed to get schedule texts at this number.")
        how = (request.form.get("how") or "").strip()
        if not how:
            raise TextSettingsError("Say how they agreed (for example: in person, 22 Oct, at the shop).")
        save_contact(user, mobile_phone=request.form.get("mobile_phone", ""), opt_in=True,
                     method=METHOD_OFFICE_ON_BEHALF, recorded_by=current_user, organization_id=org_id, note=how[:200])
    except TextSettingsError as exc:
        flash(str(exc), "error")
    else:
        flash(f"Schedule texts on for {user.display_name}. Their consent is recorded.", "success")
    return redirect(back)


# ------------------------------------------------------------------ Field: the person's own setting

def field_settings_view():
    """Served by the Field blueprint at /field/text-messages (endpoint field.text_messages)."""
    from app.services.text_messages import (
        CONSENT_WORDING,
        TextSettingsError,
        consent_history,
        contact_for,
        save_contact,
    )

    org_id = get_current_organization_id()
    if request.method == "POST":
        try:
            if request.form.get("action") == "stop":
                contact = contact_for(current_user)
                save_contact(current_user, mobile_phone=(contact.mobile_phone if contact else "") or "", opt_in=False,
                             method=METHOD_SELF_FIELD, organization_id=org_id, note="Turned off on Field")
                flash("Schedule texts are off. You still see every change on Field.", "success")
            else:
                if request.form.get("consent") != "yes":
                    raise TextSettingsError("Tick the box to agree to schedule texts.")
                save_contact(current_user, mobile_phone=request.form.get("mobile_phone", ""), opt_in=True,
                             method=METHOD_SELF_FIELD, organization_id=org_id, note="Agreed on Field")
                flash("Schedule texts are on.", "success")
        except TextSettingsError as exc:
            flash(str(exc), "error")
        return redirect(url_for("field.text_messages"))
    contact = contact_for(current_user)
    return render_template("field/text_messages.html", contact=contact, wording=CONSENT_WORDING,
                           history=consent_history(current_user.id, limit=5), nav_current="texts")


# ------------------------------------------------------------------ Twilio (public, signature-checked)

@sms_notifications_bp.route("/sms/twilio/status", methods=["POST"])
@csrf.exempt
def twilio_status():
    """PUBLIC (security route sweep, 22 Oct 2026): Twilio's delivery report for a text we sent. Answers 403
    unless X-Twilio-Signature is valid for TWILIO_AUTH_TOKEN; it only updates the status of that text."""
    from app.services.text_messages import apply_status_callback, verify_twilio_request

    if not verify_twilio_request(request):
        abort(403)
    apply_status_callback(request.form)
    return Response("", status=204)


@sms_notifications_bp.route("/sms/twilio/inbound", methods=["POST"])
@csrf.exempt
def twilio_inbound():
    """PUBLIC (security route sweep, 22 Oct 2026): a reply to our number. Signature-checked like the status
    report; it only records STOP / START for that number. Answers empty TwiML (Twilio sends its own STOP reply)."""
    from app.services.text_messages import apply_inbound_reply, verify_twilio_request

    if not verify_twilio_request(request):
        abort(403)
    apply_inbound_reply(request.form)
    return Response('<?xml version="1.0" encoding="UTF-8"?><Response></Response>', mimetype="text/xml")
