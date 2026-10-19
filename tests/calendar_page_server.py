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
    monday = date.today() - timedelta(days=date.today().weekday())
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
    appt(kevin, title="Kevin dentist", appointment_date=day(1).isoformat(), start_time="15:00", end_time="16:00",
         location="Synthetic Clinic", visibility="PERSONAL")
    return {"monday": monday.isoformat(), "empty_day": day(13).isoformat(), "kevin": list(KEVIN)}


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
