"""Private calendar feeds (Joel, 19 Oct 2026). Public by design: the secret key in the address is
the only credential, so Outlook, Google Calendar and Apple Calendar can fetch it without signing
in. A wrong, turned-off or replaced key, or a person who has left the company, gets 404."""

from flask import Blueprint, Response, abort

calendar_feed_bp = Blueprint("calendar_feed", __name__, url_prefix="/calendar-feed")


@calendar_feed_bp.route("/<key>.ics")
def feed(key):
    from app.routes.schedule import _site_base_url
    from app.services.appointments import feed_for_key

    body = feed_for_key(key, base_url=_site_base_url())
    if body is None:
        abort(404)
    response = Response(body, mimetype="text/calendar")
    response.headers["Content-Disposition"] = 'inline; filename="calibraytai.ics"'
    response.headers["Cache-Control"] = "private, max-age=300"
    response.headers["X-Robots-Tag"] = "noindex, nofollow"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response
