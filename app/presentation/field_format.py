"""Field-facing date and name formatting. No record ownership."""

from __future__ import annotations

from calendar import monthrange
from datetime import date
from typing import Optional
from urllib.parse import quote

from app.presentation import contractor_copy

_WEEKDAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
_WEEKDAYS_LONG = (
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
)
_MONTHS = (
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
)


def field_date_phrase(value: date, *, today: Optional[date] = None) -> str:
    today = today or date.today()
    if value == today:
        return contractor_copy.FIELD_NAV_TODAY
    return f"{_WEEKDAYS[value.weekday()]} {value.day} {_MONTHS[value.month - 1]}"


def field_date_range(
    start: date,
    end: date,
    *,
    today: Optional[date] = None,
) -> str:
    today = today or date.today()
    if start == end:
        return field_date_phrase(start, today=today)
    return (
        f"{field_date_phrase(start, today=today)} – "
        f"{field_date_phrase(end, today=today)}"
    )


_MONTHS_LONG = (
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)


def field_today_weekday(today: Optional[date] = None) -> str:
    today = today or date.today()
    return _WEEKDAYS_LONG[today.weekday()]


def field_today_natural_date(today: Optional[date] = None) -> str:
    today = today or date.today()
    return f"{_MONTHS_LONG[today.month - 1]} {today.day}"


def field_today_heading(today: Optional[date] = None) -> str:
    today = today or date.today()
    return f"{field_today_weekday(today)}, {field_today_natural_date(today)}"


def field_given_name(display_name: str) -> str:
    raw = (display_name or "").strip()
    if not raw:
        return ""
    return raw.split()[0]


def field_my_work_heading(display_name: str) -> str:
    given = field_given_name(display_name)
    if not given:
        return contractor_copy.FIELD_MY_WORK
    return f"My Work — {given}"


def field_project_label(name: str) -> str:
    raw = (name or "").strip()
    if " — " in raw:
        return raw.split(" — ", 1)[0].strip() or raw
    return raw


def field_usable_address(raw: Optional[str]) -> str:
    return (raw or "").strip()


_PROVINCE_SHORT = {
    "ontario": "ON",
    "on": "ON",
    "ca-on": "ON",
}


def field_province_short(raw: Optional[str]) -> str:
    usable = field_usable_address(raw)
    if not usable:
        return ""
    return _PROVINCE_SHORT.get(usable.lower(), usable)


def field_address_display_lines(raw: str) -> str:
    usable = field_usable_address(raw)
    if ", " not in usable:
        return usable
    street, rest = usable.split(", ", 1)
    rest = rest.strip()
    if not street.strip() or not rest:
        return usable
    return f"{street.strip()}\n{rest}"


def field_job_site(project) -> dict:
    """Project job-site for Field. Prefers civic ProjectLocation, else Project.address."""
    empty = {"address": "", "destination": "", "directions_url": None}
    if project is None:
        return empty
    location = getattr(project, "location", None)
    street = field_usable_address(getattr(location, "street", None) if location else None)
    if street:
        municipality = field_usable_address(
            getattr(location, "municipality", None) if location else None
        )
        province = field_province_short(
            getattr(location, "province_state", None) if location else None
        )
        lines = [street]
        locality = ", ".join(part for part in (municipality, province) if part)
        if locality:
            lines.append(locality)
        destination = ", ".join(part for part in (street, municipality, province) if part)
        return {
            "address": "\n".join(lines),
            "destination": destination,
            "directions_url": field_directions_url(destination),
        }
    raw = field_usable_address(getattr(project, "address", None))
    if not raw:
        return empty
    return {
        "address": field_address_display_lines(raw),
        "destination": raw,
        "directions_url": field_directions_url(raw),
    }


def field_directions_url(address: Optional[str]) -> Optional[str]:
    usable = field_usable_address(address)
    if not usable:
        return None
    usable = " ".join(usable.split())
    return "https://maps.apple.com/?daddr=" + quote(usable, safe="")


def field_group_schedule_cards(cards: list[dict]) -> list[dict]:
    groups = []
    index = {}
    for card in cards:
        key = card.get("project_id")
        if key not in index:
            index[key] = len(groups)
            groups.append(
                {
                    "project_id": key,
                    "project_name": card.get("project_name") or "",
                    "project_label": card.get("project_label")
                    or card.get("project_name")
                    or "",
                    "address": card.get("address") or "",
                    "destination": card.get("destination") or "",
                    "directions_url": card.get("directions_url"),
                    "cards": [],
                }
            )
        groups[index[key]]["cards"].append(card)
    return groups


def field_month_title(year: int, month: int) -> str:
    return f"{_MONTHS_LONG[month - 1]} {year}"


def field_calendar_weekday_headings() -> tuple[str, ...]:
    return _WEEKDAYS


def field_adjacent_month(year: int, month: int, delta: int) -> tuple[int, int]:
    month += delta
    year += (month - 1) // 12
    month = (month - 1) % 12 + 1
    return year, month


def field_month_calendar(
    *,
    year: int,
    month: int,
    today: date,
    selected: date,
    work_dates,
) -> list[list[dict]]:
    first = date(year, month, 1)
    lead = first.weekday()
    n_days = monthrange(year, month)[1]
    work_dates = set(work_dates or ())
    cells = [
        {
            "in_month": False,
            "date": None,
            "day": None,
            "label": "",
            "is_today": False,
            "is_selected": False,
            "has_work": False,
        }
        for _ in range(lead)
    ]
    for day in range(1, n_days + 1):
        value = date(year, month, day)
        cells.append(
            {
                "in_month": True,
                "date": value,
                "day": day,
                "label": str(day),
                "is_today": value == today,
                "is_selected": value == selected,
                "has_work": value in work_dates,
            }
        )
    while len(cells) % 7:
        cells.append(
            {
                "in_month": False,
                "date": None,
                "day": None,
                "label": "",
                "is_today": False,
                "is_selected": False,
                "has_work": False,
            }
        )
    return [cells[index : index + 7] for index in range(0, len(cells), 7)]
