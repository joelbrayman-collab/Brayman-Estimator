"""Local office for the Guided Tasks browser walk (tools/release/evidence_guided_tasks.mjs, 1 Nov 2026).

Built by the real migrations on an empty temporary SQLite database, CSRF on. Adds: Ben (owner and estimator), Pat (a
project manager: office member with Company Management), Kevin (Field-only crew, booked today on one job), a
customer with an address, the company costs and a proposal template. Synthetic data only; it never reads a hosted
database. Prints ``FACTS <json>`` and ``READY <port>``.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402

from app import create_app, db  # noqa: E402

PEOPLE = {
    "ben": ("ben.tasks.walk@example.invalid", "Synthetic-ben-tasks-1", "Ben Brayman (synthetic)"),
    "pat": ("pat.tasks.walk@example.invalid", "Synthetic-pat-tasks-1", "Pat Manager (synthetic)"),
    "kevin": ("kevin.tasks.walk@example.invalid", "Synthetic-kevin-tasks-1", "Kevin Field (synthetic crew)"),
}


def main():
    workdir = tempfile.mkdtemp(prefix="guided-tasks-walk-")
    uri = f"sqlite:///{workdir}/office.db"
    application = create_app({"TESTING": True, "CALIBRAYTAI_HOSTED": "0", "SQLALCHEMY_DATABASE_URI": uri,
                              "SECRET_KEY": "guided-tasks-walk-secret", "WTF_CSRF_ENABLED": True,
                              "PLAN_UPLOAD_ROOT": os.path.join(workdir, "plans"),
                              "DOCUMENT_ROOT": os.path.join(workdir, "documents"),
                              "DECK_TAKEOFF_ROOT": os.path.join(workdir, "deck_takeoff")})
    with application.app_context():
        cfg = Config(str(ROOT / "migrations" / "alembic.ini"))
        cfg.set_main_option("script_location", str(ROOT / "migrations"))
        cfg.set_main_option("sqlalchemy.url", uri)
        command.upgrade(cfg, "head")
        from app.models import Client, CostItem, Project
        from app.models.user import UserMembership
        from app.services.access_domains import ACCESS_DOMAIN_COMPANY_MANAGEMENT, grant_access_domain, set_field_only
        from app.services.instance_authority import set_instance_owner
        from app.services.local_time import local_today
        from app.services.organizations import DEFAULT_ORGANIZATION_ID as ORG
        from app.services.permit_foundation import establish_project_location_and_profile
        from app.services.proposals import create_proposal_template
        from app.services.schedule import assign_user, create_schedule_item
        from app.services.work_structure import add_project_element, ensure_baseline_work_catalog
        from tests.auth_fixtures import ensure_office_user
        from tests.guided_support import COST_ITEMS

        def membership(user):
            return UserMembership.query.filter_by(user_id=user.id, organization_id=ORG).one()

        ben = ensure_office_user(email=PEOPLE["ben"][0], password=PEOPLE["ben"][1], display_name=PEOPLE["ben"][2])
        set_instance_owner(ORG, membership(ben).id, ben.id)
        pat = ensure_office_user(email=PEOPLE["pat"][0], password=PEOPLE["pat"][1], display_name=PEOPLE["pat"][2])
        grant_access_domain(membership_id=membership(pat).id, domain_key=ACCESS_DOMAIN_COMPANY_MANAGEMENT)
        kevin = ensure_office_user(email=PEOPLE["kevin"][0], password=PEOPLE["kevin"][1],
                                   display_name=PEOPLE["kevin"][2])
        set_field_only(membership(kevin), True, ben)
        customer = Client(name="Jordan Avery (synthetic)", organization_id=ORG, email="jordan.avery@example.invalid",
                          phone="613-555-0101", street_address="12 Synthetic Lane", city="Merrickville",
                          province_state="Ontario", postal_code="K0G 1N0", country="Canada")
        db.session.add(customer)
        for code, name, unit, cost in COST_ITEMS:
            db.session.add(CostItem(code=code, name=name, category="Material", unit=unit, unit_cost=Decimal(cost),
                                    default_markup_percent=Decimal("0"), organization_id=ORG, is_active=True))
        db.session.commit()
        create_proposal_template(name="Synthetic standard", organization_id=ORG, is_default=True)
        # Kevin's job today (Field Today at phone width).
        job = Project(name="Harbour Lane deck (synthetic)", client_id=customer.id, organization_id=ORG,
                      status="Active")
        db.session.add(job)
        db.session.flush()
        establish_project_location_and_profile(job.id, {"street": "40 Harbour Lane", "municipality": "Merrickville",
                                                        "province_state": "Ontario", "postal_zip": "K0G 1N0",
                                                        "country": "Canada"}, None, organization_id=ORG,
                                               generated_by="Seed (synthetic)", commit=False)
        db.session.commit()
        ensure_baseline_work_catalog()
        element = add_project_element(project_id=job.id, display_name="Deck framing (synthetic)", organization_id=ORG)
        item = create_schedule_item(project_id=job.id, project_work_element_id=element.id,
                                    scheduled_start=local_today(), scheduled_end=local_today(), organization_id=ORG)
        assign_user(item.id, worker_user_id=kevin.id, organization_id=ORG)
        db.session.commit()
        facts = {"people": PEOPLE, "customer_id": customer.id, "field_job_id": job.id, "database_uri": uri}
    port = int(os.environ["GUIDED_TASKS_PAGE_PORT"])
    print("FACTS " + json.dumps(facts), flush=True)
    print(f"READY {port}", flush=True)
    application.run(host="127.0.0.1", port=port, use_reloader=False, threaded=True)


if __name__ == "__main__":
    main()
