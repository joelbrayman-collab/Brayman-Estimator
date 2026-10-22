"""Local office for the SMS schedule-notice browser walk (tools/release/evidence_sms_notifications.mjs, 22 Oct 2026).

A temporary SQLite database built by the real migrations. On top of that, only:

* Ben Brayman (synthetic), the Instance Owner, who reschedules on a desktop;
* Kevin Fieldhand (synthetic), a Field-only crew member on an iPhone-sized screen. The office saved his mobile
  number (without consent), so Field's one-time question shows it filled in;
* Liam Crewhand (synthetic), Field-only, no number, who answers Not now;
* one customer job in Merrickville with one work item scheduled next week and Kevin assigned to it.

Texts go to a fake transport that appends each one to a file (never Twilio, never a phone). CSRF is on, as in
production. Synthetic data only; it never reads the hosted database. Prints ``FACTS <json>`` and ``READY <port>``.
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
os.chdir(ROOT)

from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402

from app import create_app, db  # noqa: E402

BEN = ("ben.sms@example.invalid", "Synthetic-ben-sms-1", "Ben Brayman (synthetic)")
KEVIN = ("kevin.sms@example.invalid", "Synthetic-kevin-sms-1", "Kevin Fieldhand (synthetic)")
LIAM = ("liam.sms@example.invalid", "Synthetic-liam-sms-1", "Liam Crewhand (synthetic)")
PROJECT = "Pat Synthetic-Homeowner deck"
CLIENT = "Pat Synthetic-Homeowner"
WORK = "Footings (synthetic)"


def _migrate(uri: str) -> None:
    cfg = Config(str(ROOT / "migrations" / "alembic.ini"))
    cfg.set_main_option("script_location", str(ROOT / "migrations"))
    cfg.set_main_option("sqlalchemy.url", uri)
    command.upgrade(cfg, "head")


def _seed():
    from app.models import Client, Project
    from app.models.project import ProjectLocation
    from app.models.user import UserMembership
    from app.services.access_domains import set_field_only
    from app.services.crew_notices import send_due_notices
    from app.services.instance_authority import set_instance_owner
    from app.services.organizations import DEFAULT_ORGANIZATION_ID as ORG
    from app.services.schedule import assign_user, create_schedule_item
    from app.services.work_structure import add_project_element, ensure_baseline_work_catalog
    from tests.auth_fixtures import ensure_office_user

    ensure_baseline_work_catalog()
    ben = ensure_office_user(email=BEN[0], password=BEN[1], display_name=BEN[2])
    set_instance_owner(ORG, UserMembership.query.filter_by(user_id=ben.id, organization_id=ORG).one().id, ben.id)
    kevin = ensure_office_user(email=KEVIN[0], password=KEVIN[1], display_name=KEVIN[2])
    set_field_only(UserMembership.query.filter_by(user_id=kevin.id, organization_id=ORG).one(), True, ben)
    liam = ensure_office_user(email=LIAM[0], password=LIAM[1], display_name=LIAM[2])
    set_field_only(UserMembership.query.filter_by(user_id=liam.id, organization_id=ORG).one(), True, ben)
    from app.models.supplier_portal import NotificationContact

    db.session.add(NotificationContact(user_id=kevin.id, mobile_phone="+16135550142", sms_opt_in=False))
    db.session.commit()
    client = Client(name=CLIENT, organization_id=ORG, email="pat.homeowner@example.invalid")
    db.session.add(client)
    db.session.flush()
    project = Project(name=PROJECT, client_id=client.id, organization_id=ORG, status="Contracted",
                      project_number="SMS-SYN-1", address="7 Synthetic Lane, Merrickville, ON")
    db.session.add(project)
    db.session.flush()
    db.session.add(ProjectLocation(project_id=project.id, organization_id=ORG, street="7 Synthetic Lane",
                                   municipality="Merrickville", province_state="ON"))
    db.session.commit()
    element = add_project_element(project_id=project.id, display_name=WORK, organization_id=ORG)
    start = date.today() + timedelta(days=7)
    item = create_schedule_item(project_id=project.id, project_work_element_id=element.id, scheduled_start=start,
                                scheduled_end=start, organization_id=ORG)
    assign_user(item.id, worker_user_id=kevin.id, organization_id=ORG)
    send_due_notices(force=True)  # the set-up assignment: Kevin had not agreed to texts, so nothing is sent
    membership = UserMembership.query.filter_by(user_id=kevin.id, organization_id=ORG).one()
    return {"ben": [BEN[0], BEN[1]], "kevin": [KEVIN[0], KEVIN[1]], "kevin_name": KEVIN[2],
            "liam": [LIAM[0], LIAM[1]], "client": CLIENT,
            "project": PROJECT, "work": WORK, "item_id": item.id, "start": start.isoformat(),
            "kevin_membership_id": membership.id}


def main():
    workdir = tempfile.mkdtemp(prefix="sms-notices-")
    uri = f"sqlite:///{workdir}/sms.db"
    outbox = os.path.join(workdir, "texts.jsonl")

    def transport(phone, body):  # the fake carrier: written to a file, never sent
        with open(outbox, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"to": phone, "body": body}) + "\n")
        return f"SMfakewalk{sum(1 for _ in open(outbox, encoding='utf-8'))}"

    config = {"TESTING": True, "CALIBRAYTAI_HOSTED": "0", "SQLALCHEMY_DATABASE_URI": uri,
              "SECRET_KEY": "sms-notices-secret-key", "WTF_CSRF_ENABLED": True,
              "TRANSACTIONAL_EMAIL_PROVIDER": "local", "MAIL_CAPTURE_ROOT": os.path.join(workdir, "mail"),
              "TEXT_TRANSPORT": transport, "PUBLIC_BASE_URL": "https://calibraytai.example.invalid"}
    application = create_app(config)
    with application.app_context():
        _migrate(uri)
        facts = _seed()
    facts["outbox"] = outbox
    port = int(os.environ["SMS_NOTICES_PORT"])
    print("FACTS " + json.dumps(facts), flush=True)
    print(f"READY {port}", flush=True)
    application.run(host="127.0.0.1", port=port, use_reloader=False, threaded=True)


if __name__ == "__main__":
    main()
