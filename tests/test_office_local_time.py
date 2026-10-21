"""Office times read in the company's time zone, labelled (defect 6, 21 Oct 2026). Synthetic data only.

A field observation made at 11:31 on a phone in Ottawa is stored as 15:31 UTC and must read 11:31 EDT
in the office, not 15:31. Stored values stay UTC.
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from app import db
from app.models.build import FieldCaptureEvent
from app.services.local_time import format_local, local_date, local_input_to_utc
from tests.test_build_field_observation_fg020 import _add_project, app, client  # noqa: F401

TEMPLATES = Path(__file__).resolve().parents[1] / "app" / "templates"


def test_stored_utc_reads_in_toronto_time_with_the_zone_named(app):
    assert format_local(datetime(2026, 10, 21, 15, 31)) == "2026-10-21 11:31 EDT"
    assert format_local(datetime(2026, 1, 15, 15, 31)) == "2026-01-15 10:31 EST"
    assert format_local("2026-10-21T15:31:00") == "2026-10-21 11:31 EDT"  # JSON-kept stamps too
    assert format_local(None) == "—"
    # Late evening in Ottawa is already the next day in UTC: the office date is the Ottawa date.
    assert local_date(datetime(2026, 11, 21, 2, 30)).isoformat() == "2026-11-20"


def test_company_time_zone_setting_is_used(app):
    app.config["COMPANY_TIME_ZONE"] = "America/Vancouver"
    assert format_local(datetime(2026, 10, 21, 15, 31)) == "2026-10-21 08:31 PDT"


def test_office_typed_time_is_the_office_clock_and_is_stored_as_utc(app):
    assert local_input_to_utc("2026-10-21T11:31") == datetime(2026, 10, 21, 15, 31)
    assert local_input_to_utc("2026-01-15T11:31") == datetime(2026, 1, 15, 16, 31)
    assert local_input_to_utc("") is None


def test_field_observation_shows_the_phone_clock_time_in_the_office(app, client):
    project = _add_project(name="Local Time House")
    response = client.post(f"/projects/{project.id}/field-events/new",
                           data={"text": "Footing forms checked", "occurred_at": "2026-10-21T11:31"})
    assert response.status_code in (302, 303)
    event = FieldCaptureEvent.query.one()
    assert event.occurred_at == datetime(2026, 10, 21, 15, 31)  # stored UTC
    page = client.get(f"/projects/{project.id}/field-events/{event.id}").get_data(as_text=True)
    assert "2026-10-21 11:31 EDT" in page
    assert "15:31" not in page
    hub = client.get(f"/projects/{project.id}").get_data(as_text=True)
    assert "11:31 EDT" in hub and "15:31" not in hub


def test_no_template_prints_a_raw_utc_clock_time():
    """Every time-of-day shown to people goes through local_time (or is a wall-clock time, not a stamp)."""
    wall_clock = {"appointment.start_time", "appointment.end_time", "h.prior_start_time"}
    offenders = []
    for path in TEMPLATES.rglob("*.html"):
        for number, line in enumerate(path.read_text().splitlines(), 1):
            for match in re.finditer(r"([\w\.]+)\.strftime\(['\"][^'\"]*%[HI]", line):
                if match.group(1) not in wall_clock:
                    offenders.append(f"{path.relative_to(TEMPLATES)}:{number}")
            if re.search(r"\}\}\s*UTC", line):
                offenders.append(f"{path.relative_to(TEMPLATES)}:{number} (UTC label)")
    assert offenders == []
