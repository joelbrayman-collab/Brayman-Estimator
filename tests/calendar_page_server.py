"""Local office for the calendar release browser checks (Joel, 19 Oct 2026).

Temporary database, synthetic data only, dates relative to this week so the checks run any day.
It never reads the hosted database.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import create_app, db  # noqa: E402
import app.models  # noqa: E402,F401  (models load before app.services)
from app.services.local_time import local_today  # noqa: E402  (the office's date, as the app uses)
from tests.auth_fixtures import create_membership, create_user, ensure_office_user  # noqa: E402

KEVIN = ("kevin.calendar@example.invalid", "Synthetic-calendar-pass-1")


def seed() -> dict:
    from app.models import Client, Project
    from app.services.appointments import create_appointment, read_form
    from app.services.organization_crew import add_crew_member, create_crew
    from app.services.organizations import DEFAULT_ORGANIZATION_ID as ORG
    from app.services.schedule import assign_crew, create_schedule_item
    from app.services.work_structure import add_project_element, ensure_baseline_work_catalog

    ensure_baseline_work_catalog()
    office = ensure_office_user(display_name="Ben Synthetic")
    kevin = create_user(email=KEVIN[0], password=KEVIN[1], display_name="Kevin Synthetic")
    create_membership(kevin)
    db.session.commit()
    monday = local_today() - timedelta(days=local_today().weekday())
    day = lambda n: monday + timedelta(days=n)  # noqa: E731
    client = Client(name="Synthetic Calendar Client", organization_id=ORG)
    db.session.add(client)
    db.session.flush()
    mine = Project(name="Synthetic Calendar Deck", client_id=client.id, organization_id=ORG, status="Estimating")
    theirs = Project(name="Synthetic Other Job", client_id=client.id, organization_id=ORG, status="Estimating")
    db.session.add_all([mine, theirs])
    db.session.commit()
    crew = create_crew(name="Synthetic Alpha", organization_id=ORG)
    add_crew_member(crew.id, user_id=office.id, effective_from=monday - timedelta(days=30), organization_id=ORG)
    for project, name, start, end, on_crew in ((mine, "Slab pour", 0, 0, True), (mine, "Deck framing", 1, 3, True),
                                               (theirs, "Wall framing", 2, 4, False)):
        element = add_project_element(project_id=project.id, display_name=name, organization_id=ORG)
        item = create_schedule_item(project_id=project.id, project_work_element_id=element.id,
                                    scheduled_start=day(start), scheduled_end=day(end), organization_id=ORG)
        if on_crew:
            assign_crew(item.id, crew_id=crew.id, organization_id=ORG)

    def appt(who, **fields):
        base = {"appointment_type": "GENERAL", "start_time": "09:00", "end_time": "10:00", "visibility": "COMPANY"}
        base.update(fields)
        return create_appointment(ORG, read_form(base), who)

    appt(office, title="Site visit — new client", appointment_type="SITE_VISIT", appointment_date=day(0).isoformat(),
         location="123 Maple Lane", assigned_user_id=str(office.id))
    appt(office, title="Meet supplier — BMR", appointment_type="SUPPLIER_MEETING", appointment_date=day(0).isoformat(),
         start_time="13:00", end_time="14:00", location="Winchester", assigned_user_id=str(office.id))
    appt(office, title="Estimate consultation — Lee", appointment_type="ESTIMATE_CONSULTATION",
         appointment_date=day(3).isoformat(), start_time="09:00", end_time="10:30", location="Office")
    appt(kevin, title="Weekly office meeting", appointment_date=day(3).isoformat(), start_time="09:30", end_time="10:30",
         location="Office boardroom")
    appt(office, title="Lunch with accountant", appointment_date=day(2).isoformat(), start_time="12:00",
         end_time="13:00", visibility="PERSONAL")
    # A Saturday (Joel, 23 Oct 2026: in Mon–Fri view weekend work must never be missed).
    appt(office, title="Saturday pour check", appointment_date=day(5).isoformat(), start_time="08:00", end_time="09:00",
         location="Synthetic Calendar Deck", assigned_user_id=str(office.id))
    appt(kevin, title="Kevin dentist", appointment_date=day(1).isoformat(), start_time="15:00", end_time="16:00",
         location="Synthetic Clinic", visibility="PERSONAL")
    busy = _seed_busy_months(appt, office, mine, crew, create_schedule_item, add_project_element, assign_crew, ORG)
    return {"monday": monday.isoformat(), "saturday": day(5).isoformat(), "empty_day": day(13).isoformat(), "kevin": list(KEVIN),
            "busy_months": busy}


# Month fit, independent of today (28 Oct 2026): the month grid must fit a 1366 x 670 laptop screen whichever row is
# busiest. Fixed months, so the check never depends on the day it runs: March 2027 (5 rows, its final row holds
# April 1) and August 2027 (6 rows, its final row holds September 1). Each has a busy first, middle and final week:
# four appointments every day and a crew job across the weekdays.
BUSY_MONTHS = (
    {"month": "2027-03", "rows": 5, "weeks": {"first": date(2027, 3, 1), "middle": date(2027, 3, 15), "final": date(2027, 3, 29)}},
    {"month": "2027-08", "rows": 6, "weeks": {"first": date(2027, 7, 26), "middle": date(2027, 8, 9), "final": date(2027, 8, 30)}},
)


def _seed_busy_months(appt, office, project, crew, create_schedule_item, add_project_element, assign_crew, org):
    out = []
    for spec in BUSY_MONTHS:
        weeks = {}
        for name, monday in spec["weeks"].items():
            element = add_project_element(project_id=project.id, display_name=f"Busy framing {monday.isoformat()}",
                                          organization_id=org)
            item = create_schedule_item(project_id=project.id, project_work_element_id=element.id,
                                        scheduled_start=monday, scheduled_end=monday + timedelta(days=4),
                                        organization_id=org)
            assign_crew(item.id, crew_id=crew.id, organization_id=org)
            for n in range(7):
                when = monday + timedelta(days=n)
                for start, end in (("08:00", "09:00"), ("10:00", "11:00"), ("13:00", "14:00"), ("15:00", "16:00")):
                    appt(office, title=f"Busy {start} {when.isoformat()}", appointment_date=when.isoformat(),
                         start_time=start, end_time=end, location="Synthetic site", assigned_user_id=str(office.id))
            weeks[name] = monday.isoformat()
        out.append({"month": spec["month"], "rows": spec["rows"], "weeks": weeks})
    return out


def main():
    database = tempfile.NamedTemporaryFile(prefix="calendar-page-", suffix=".db", delete=False)
    database.close()
    application = create_app({"TESTING": True, "CALIBRAYTAI_HOSTED": "0", "SQLALCHEMY_DATABASE_URI": f"sqlite:///{database.name}",
                              "SECRET_KEY": "test-secret-key"})
    with application.app_context():
        db.create_all()
        facts = seed()
    port = int(os.environ["CALENDAR_PAGE_PORT"])
    print("FACTS " + json.dumps(facts), flush=True)
    print(f"READY {port}", flush=True)
    application.run(host="127.0.0.1", port=port, use_reloader=False, threaded=True)


if __name__ == "__main__":
    main()
