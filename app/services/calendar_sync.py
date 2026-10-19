"""Calendar files and private calendar feeds for Outlook, Google Calendar and Apple Calendar.

Joel, 19 Oct 2026. Built once in CalibraytAI and meant to be reused by AiRIA, so this module knows
nothing about construction: it turns plain event dictionaries into an iCalendar (RFC 5545) file and
handles the secret feed keys. It sends nothing anywhere: a person downloads a file, or their
calendar program fetches their private feed address.

Event dictionary keys:
    uid (str, stable), title (str), date (date), all_day (bool),
    start (time | None), end (time | None), location (str), description (str),
    cancelled (bool), sequence (int), updated (datetime, UTC), url (str, optional)
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import date, datetime, timedelta
from typing import Iterable

PRODUCT_ID = "-//CalibraytAI//Company Calendar//EN"
DEFAULT_TZID = "America/Toronto"

# Eastern Time with the North American daylight-saving rules in force since 2007.
_VTIMEZONES = {
    "America/Toronto": (
        "BEGIN:VTIMEZONE",
        "TZID:America/Toronto",
        "X-LIC-LOCATION:America/Toronto",
        "BEGIN:DAYLIGHT",
        "TZOFFSETFROM:-0500",
        "TZOFFSETTO:-0400",
        "TZNAME:EDT",
        "DTSTART:19700308T020000",
        "RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=2SU",
        "END:DAYLIGHT",
        "BEGIN:STANDARD",
        "TZOFFSETFROM:-0400",
        "TZOFFSETTO:-0500",
        "TZNAME:EST",
        "DTSTART:19701101T020000",
        "RRULE:FREQ=YEARLY;BYMONTH=11;BYDAY=1SU",
        "END:STANDARD",
        "END:VTIMEZONE",
    ),
}


def _escape(text) -> str:
    value = "" if text is None else str(text)
    return (
        value.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,")
        .replace("\r\n", "\\n").replace("\n", "\\n").replace("\r", "\\n")
    )


def _fold(line: str) -> list[str]:
    """Lines longer than 75 octets continue on the next line after a space (RFC 5545 3.1)."""
    out, current, size = [], "", 0
    for char in line:
        width = len(char.encode("utf-8"))
        if size + width > 75:
            out.append(current)
            current, size = " ", 1
        current += char
        size += width
    out.append(current)
    return out


def _utc(value: datetime) -> str:
    return value.strftime("%Y%m%dT%H%M%SZ")


def _event_lines(event: dict, tzid: str, stamp: datetime) -> list[str]:
    lines = ["BEGIN:VEVENT", f"UID:{event['uid']}", f"DTSTAMP:{_utc(stamp)}"]
    day: date = event["date"]
    if event.get("all_day"):
        lines.append(f"DTSTART;VALUE=DATE:{day.strftime('%Y%m%d')}")
        lines.append(f"DTEND;VALUE=DATE:{(day + timedelta(days=1)).strftime('%Y%m%d')}")
    else:
        start = datetime.combine(day, event["start"])
        end = datetime.combine(day, event["end"])
        lines.append(f"DTSTART;TZID={tzid}:{start.strftime('%Y%m%dT%H%M%S')}")
        lines.append(f"DTEND;TZID={tzid}:{end.strftime('%Y%m%dT%H%M%S')}")
    lines.append(f"SUMMARY:{_escape(event.get('title'))}")
    if event.get("location"):
        lines.append(f"LOCATION:{_escape(event['location'])}")
    if event.get("description"):
        lines.append(f"DESCRIPTION:{_escape(event['description'])}")
    if event.get("url"):
        lines.append(f"URL:{event['url']}")
    if event.get("updated"):
        lines.append(f"LAST-MODIFIED:{_utc(event['updated'])}")
    lines.append(f"SEQUENCE:{int(event.get('sequence') or 0)}")
    lines.append(f"STATUS:{'CANCELLED' if event.get('cancelled') else 'CONFIRMED'}")
    lines.append("TRANSP:OPAQUE")
    lines.append("END:VEVENT")
    return lines


def build_calendar(
    events: Iterable[dict],
    *,
    name: str,
    tzid: str = DEFAULT_TZID,
    refresh_minutes: int = 60,
    now: datetime | None = None,
) -> str:
    """One iCalendar file. Times are wall-clock times in ``tzid`` (the office's time zone)."""
    if tzid not in _VTIMEZONES:
        raise ValueError(f"No time zone rules for {tzid}.")
    stamp = now or datetime.utcnow()
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        f"PRODID:{PRODUCT_ID}",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{_escape(name)}",
        f"X-WR-TIMEZONE:{tzid}",
        f"REFRESH-INTERVAL;VALUE=DURATION:PT{int(refresh_minutes)}M",
        f"X-PUBLISHED-TTL:PT{int(refresh_minutes)}M",
        *_VTIMEZONES[tzid],
    ]
    for event in events:
        lines.extend(_event_lines(event, tzid, stamp))
    lines.append("END:VCALENDAR")
    folded = []
    for line in lines:
        folded.extend(_fold(line))
    return "\r\n".join(folded) + "\r\n"


# ---------------------------------------------------------------------------------------------
# Secret feed keys. Only a hash is stored; the full key is shown to the person once.


def new_feed_key() -> str:
    return secrets.token_urlsafe(32)


def hash_feed_key(key: str) -> str:
    return hashlib.sha256((key or "").encode("utf-8")).hexdigest()


def feed_addresses(base_url: str, path: str) -> dict:
    """The https address, and the webcal:// form that opens Apple Calendar or Outlook directly."""
    base = base_url.rstrip("/")
    https = f"{base}{path}"
    webcal = "webcal://" + https.split("://", 1)[1] if "://" in https else https
    return {"https": https, "webcal": webcal}
