"""Postmark delivery reports (sign-in reliability, Joel, 26 Oct 2026).

PUBLIC (security route sweep): no sign-in and no CSRF token, like Twilio's delivery reports. Every request must
carry the HTTP Basic credentials set in POSTMARK_WEBHOOK_USERNAME / POSTMARK_WEBHOOK_PASSWORD (Postmark sends them
from the webhook URL); otherwise 401, and 404 while they are not configured. A report only adds a delivery event
(Delivered, Bounced, spam complaint, delayed) to an email CalibraytAI already sent.
"""

from flask import Blueprint, Response, abort, jsonify, request

from app import csrf

email_webhooks_bp = Blueprint("email_webhooks", __name__)


@email_webhooks_bp.route("/webhooks/postmark", methods=["POST"])
@csrf.exempt
def postmark():
    from app.services.email_delivery import DeliveryError, record_postmark_webhook, webhook_authorized, webhook_configured

    if not webhook_configured():
        abort(404)
    if not webhook_authorized(request.authorization):
        return Response("", status=401, headers={"WWW-Authenticate": 'Basic realm="postmark"'})
    try:
        outcome = record_postmark_webhook(request.get_json(silent=True))
    except DeliveryError:
        return jsonify({"result": "not a delivery report"}), 400
    return jsonify({"result": outcome}), 200
