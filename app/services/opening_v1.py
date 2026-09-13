"""CalibraytAI Opening V1 playback contract (login brand experience)."""

OPENING_VERSION = "v1"
SUPPRESS_DAYS = 7
TIMEOUT_MS = 10000
SESSION_STORAGE_KEY = "calibraytai.opening.v1.session"
LAST_SHOWN_STORAGE_KEY = "calibraytai.opening.v1.lastShown"
MP4_STATIC = "opening/v1/opening-v1-web.mp4"
WEBM_STATIC = "opening/v1/opening-v1-web.webm"
POSTER_STATIC = "opening/v1/opening-v1-poster.jpg"
REDUCED_MOTION_STATIC = "opening/v1/opening-v1-reduced-motion.jpg"


def opening_v1_config(url_for) -> dict:
    """JSON-serializable config for the login-page controller."""
    return {
        "version": OPENING_VERSION,
        "mp4": url_for("static", filename=MP4_STATIC),
        "webm": url_for("static", filename=WEBM_STATIC),
        "poster": url_for("static", filename=POSTER_STATIC),
        "reducedMotionPoster": url_for("static", filename=REDUCED_MOTION_STATIC),
        "suppressDays": SUPPRESS_DAYS,
        "timeoutMs": TIMEOUT_MS,
        "sessionKey": SESSION_STORAGE_KEY,
        "lastShownKey": LAST_SHOWN_STORAGE_KEY,
    }
