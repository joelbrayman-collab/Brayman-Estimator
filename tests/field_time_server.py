"""Local office for the Field time browser walk (tools/release/evidence_field_time.mjs, 22 Oct 2026).

A temporary SQLite database built by the real migrations (so the default organization has its
authorized $65 an hour company costing rate, as the hosted office does). On top of that, only:

* Ben Brayman (synthetic), the Instance Owner, who reviews time on a desktop;
* Kevin Fieldhand (synthetic), a field-only crew member who records time on his phone;
* one customer job, Mill Pond Road deck (synthetic), with project work built from its issued estimate
  (Forms: 40 estimated hours at $65), an approved change order (Stair landing framing, 10 hours), and
  Kevin scheduled on the job from today.

Everything else (Kevin's time, Ben's return and approval, the shop and company time set-up, the
QuickBooks time file and check) happens in the browser. CSRF is on, as in production. Synthetic data
only; it never reads the hosted database.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402

from app import create_app, db  # noqa: E402
import app.models  # noqa: E402,F401  (models load before app.services)
from app.services.local_time import local_today  # noqa: E402  (the office's date, as the app uses)

BEN = ("ben.fieldtime@example.invalid", "Synthetic-ben-fieldtime-1", "Ben Brayman (synthetic)")
KEVIN = ("kevin.fieldtime@example.invalid", "Synthetic-kevin-fieldtime-1", "Kevin Fieldhand (synthetic)")
PROJECT = "Mill Pond Road deck (synthetic)"
CLIENT = "Pat Synthetic Homeowner"


def _migrate(uri: str) -> None:
    cfg = Config(str(ROOT / "migrations" / "alembic.ini"))
    cfg.set_main_option("script_location", str(ROOT / "migrations"))
    cfg.set_main_option("sqlalchemy.url", uri)
    command.upgrade(cfg, "head")


def _seed():
    from app.models import Client, Project
    from app.models.user import UserMembership
    from app.models.work_structure import ProjectWorkActivity, ProjectWorkElement
    from app.project_controls.services import create_change_order
    from app.services import create_estimate
    from app.services.access_domains import set_field_only
    from app.services.estimates import set_version_status
    from app.services.instance_authority import set_instance_owner
    from app.services.labour_engine import create_estimate_labour_snapshot, create_labour_task
    from app.services.organizations import DEFAULT_ORGANIZATION_ID as ORG
    from app.services.schedule import assign_user, create_schedule_item
    from app.services.work_scope import add_authorized_change_order_activity
    from app.services.work_structure import ensure_baseline_work_catalog, seed_project_work_structure
    from tests.auth_fixtures import ensure_office_user

    ensure_baseline_work_catalog()
    ben = ensure_office_user(email=BEN[0], password=BEN[1], display_name=BEN[2])
    db.session.commit()
    set_instance_owner(ORG, UserMembership.query.filter_by(user_id=ben.id, organization_id=ORG).one().id, ben.id)
    kevin = ensure_office_user(email=KEVIN[0], password=KEVIN[1], display_name=KEVIN[2])
    db.session.commit()
    set_field_only(UserMembership.query.filter_by(user_id=kevin.id, organization_id=ORG).one(), True, ben)

    client = Client(name=CLIENT, organization_id=ORG, email="pat.homeowner@example.invalid")
    db.session.add(client)
    db.session.flush()
    project = Project(name=PROJECT, client_id=client.id, organization_id=ORG, status="Contracted",
                      project_number="MPR-SYN-1")
    db.session.add(project)
    db.session.commit()
    task = create_labour_task(task_code="LT-SYN-DECK-FORMS", canonical_name="Forms", production_unit="sq ft",
                              unit_of_measure="sqft", trade="Concrete", category="Foundation",
                              organization_id=ORG, created_by=BEN[2])
    estimate = create_estimate(project_id=project.id, estimate_number="EST-SYN-FIELDTIME",
                               title="Mill Pond Road deck estimate (synthetic)")
    version = estimate.current_version
    create_estimate_labour_snapshot(estimate_version_id=version.id, labour_task_id=task.id, quantity=Decimal("800"),
                                    override_production_rate=Decimal("0.05"), override_production_reason="Synthetic walk",
                                    override_direct_labour_cost_rate=Decimal("65"),
                                    override_direct_labour_reason="Synthetic walk", created_by=BEN[2],
                                    organization_id=ORG)
    set_version_status(version, "Issued")
    db.session.refresh(version)
    seed_project_work_structure(project_id=project.id, estimate_version_id=version.id, seeded_by=BEN[2])
    activity = ProjectWorkActivity.query.join(ProjectWorkElement).filter(ProjectWorkElement.project_id == project.id).one()
    co = create_change_order(project=project, title="Add stair landing", status="Approved")
    co_activity = add_authorized_change_order_activity(
        project_work_element_id=activity.project_work_element_id, change_order_id=co.id,
        display_name="Stair landing framing", estimated_hours="10", created_by=BEN[2])
    item = create_schedule_item(project_id=project.id, project_work_element_id=activity.project_work_element_id,
                                scheduled_start=local_today(), scheduled_end=local_today() + timedelta(days=3),
                                organization_id=ORG)
    assign_user(item.id, worker_user_id=kevin.id, organization_id=ORG)
    db.session.commit()
    return {
        "ben": [BEN[0], BEN[1]], "ben_name": BEN[2], "kevin": [KEVIN[0], KEVIN[1]], "kevin_name": KEVIN[2],
        "project_id": project.id, "project": PROJECT, "client": CLIENT,
        "element": activity.element.display_name, "activity_id": activity.id, "activity": activity.display_name,
        "co_activity_id": co_activity.id, "co_activity": co_activity.display_name, "co_number": co.number,
    }


def main():
    workdir = tempfile.mkdtemp(prefix="field-time-")
    uri = f"sqlite:///{workdir}/field_time.db"
    config = {"TESTING": True, "CALIBRAYTAI_HOSTED": "0", "SQLALCHEMY_DATABASE_URI": uri,
              "SECRET_KEY": "field-time-secret-key", "WTF_CSRF_ENABLED": True,
              "TRANSACTIONAL_EMAIL_PROVIDER": "local", "MAIL_CAPTURE_ROOT": os.path.join(workdir, "mail")}
    application = create_app(config)
    with application.app_context():
        _migrate(uri)
        facts = _seed()
        facts["workdir"] = workdir
    port = int(os.environ["FIELD_TIME_PORT"])
    print("FACTS " + json.dumps(facts), flush=True)
    print(f"READY {port}", flush=True)
    application.run(host="127.0.0.1", port=port, use_reloader=False, threaded=True)


if __name__ == "__main__":
    main()
