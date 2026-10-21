"""Office times in the company's time zone (Joel, 21 Oct 2026).

Every timestamp is stored as naive UTC (``datetime.utcnow()``) and stays that way. People read
times in the company's time zone: a field observation made at 11:31 on the phone in Ottawa shows
11:31 EDT in the office, not 15:31. One place decides the zone and the conversion; templates use
the ``local_time`` filter, Python text (emails, PDFs) uses :func:`format_local`.

The zone is the ``COMPANY_TIME_ZONE`` setting (environment variable of the same name), default
America/Toronto, the same zone the Company Calendar feeds use. Organizations have no time-zone
column in V1; adding one is a migration for a later release.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from flask import current_app, has_app_context

from app.services.calendar_sync import DEFAULT_TZID

DEFAULT_FORMAT = "%Y-%m-%d %H:%M"


def company_timezone_name() -> str:
    name = ""
    if has_app_context():
        name = (current_app.config.get("COMPANY_TIME_ZONE") or "").strip()
    return name or DEFAULT_TZID


def company_timezone() -> ZoneInfo:
    try:
        return ZoneInfo(company_timezone_name())
    except (ZoneInfoNotFoundError, ValueError):
        return ZoneInfo(DEFAULT_TZID)


def _parse_stamp(value):
    """A stored ISO timestamp string (some records keep JSON text) as a datetime; else the value."""
    if not isinstance(value, str):
        return value
    raw = value.strip()
    if "T" not in raw and ":" not in raw:
        return value  # a plain date, or free text
    try:
        return datetime.fromisoformat(raw[:-1] + "+00:00" if raw.endswith("Z") else raw)
    except ValueError:
        return value


def local_input_to_utc(value: str | None) -> datetime | None:
    """A wall-clock time typed in the office (``<input type="datetime-local">``) as naive UTC.

    The person types the time on their own clock, in the company's zone. A value that already
    carries an offset is converted from that offset. Empty → None; unreadable → the text unchanged
    so the caller's own validation reports it.
    """
    raw = (value or "").strip()
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(raw[:-1] + "+00:00" if raw.endswith("Z") else raw)
    except ValueError:
        return raw
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=company_timezone())
    return parsed.astimezone(timezone.utc).replace(tzinfo=None)


def to_local(value: datetime | None) -> datetime | None:
    """A stored (naive UTC, or aware) datetime as an aware datetime in the company's zone."""
    value = _parse_stamp(value)
    if value is None:
        return None
    if not isinstance(value, datetime):
        return value
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(company_timezone())


def local_date(value: datetime | date | None) -> date | None:
    """The company-zone calendar date of a stored UTC datetime (a plain date is returned as is)."""
    value = _parse_stamp(value)
    if value is None or not isinstance(value, datetime):
        return value
    return to_local(value).date()


def format_local(value: datetime | None, fmt: str = DEFAULT_FORMAT, *, zone_label: bool = True,
                 empty: str = "—") -> str:
    """Format a stored UTC datetime in the company's zone, labelled with the zone (EDT/EST)."""
    value = _parse_stamp(value)
    if value is None or value == "":
        return empty
    if not isinstance(value, datetime):
        return value.strftime(fmt) if hasattr(value, "strftime") else str(value)
    local = to_local(value)
    text = local.strftime(fmt)
    if zone_label:
        text = f"{text} {local.tzname()}"
    return text


def register(app) -> None:
    import os

    app.config.setdefault("COMPANY_TIME_ZONE", os.environ.get("COMPANY_TIME_ZONE") or "")

    def local_time(value, fmt: str = DEFAULT_FORMAT, zone_label: bool = True, empty: str = "—"):
        return format_local(value, fmt, zone_label=zone_label, empty=empty)

    app.add_template_filter(local_time, "local_time")
    app.add_template_filter(local_date, "local_date")

    @app.context_processor
    def _company_time_zone():
        return {"company_time_zone": company_timezone_name()}
