"""Local office for the viewport-density browser walk (tools/release/evidence_density.mjs, 2 Nov 2026).

Built by the real migrations on an empty temporary SQLite database, CSRF on, like tests/guided_tasks_page_server.py
(whose seed it repeats): Ben (owner and estimator), Kevin (Field-only crew booked today on one job), customers with
addresses, the company costs and a proposal template. Adds what a normal office has on its screens, so the density
measurements are taken on representative pages and not on empty ones: a handful of customers and current projects, a
subcontractor, a supplier account, one piece of equipment, and a few filed documents on the company, a project, a
customer, the supplier, the subcontractor, a person and the equipment. Synthetic data only; it never reads a hosted
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
    "ben": ("ben.density.walk@example.invalid", "Synthetic-ben-density-1", "Ben Brayman (synthetic)"),
    "kevin": ("kevin.density.walk@example.invalid", "Synthetic-kevin-density-1", "Kevin Field (synthetic crew)"),
}

CUSTOMERS = (
    ("Jordan Avery (synthetic)", "12 Synthetic Lane", "Merrickville", "K0G 1N0"),
    ("Morgan Lee (synthetic)", "7 Example Road", "Kemptville", "K0G 1J0"),
    ("Riley Chen (synthetic)", "301 Placeholder Street", "Smiths Falls", "K7A 2B3"),
    ("Taylor Brooks (synthetic)", "88 Sample Crescent", "Perth", "K7H 1C4"),
    ("Casey Morin (synthetic)", "5 Fixture Court", "Carleton Place", "K7C 3P2"),
)
PROJECTS = (
    # name, customer index, status
    ("Lee kitchen addition (synthetic)", 1, "Estimating"),
    ("Chen garage (synthetic)", 2, "Proposal Sent"),
    ("Brooks basement finish (synthetic)", 3, "Contracted"),
    ("Morin porch rebuild (synthetic)", 4, "Lead"),
)


def main():
    workdir = tempfile.mkdtemp(prefix="density-walk-")
    uri = f"sqlite:///{workdir}/office.db"
    application = create_app({"TESTING": True, "CALIBRAYTAI_HOSTED": "0", "SQLALCHEMY_DATABASE_URI": uri,
                              "SECRET_KEY": "density-walk-secret", "WTF_CSRF_ENABLED": True,
                              "PLAN_UPLOAD_ROOT": os.path.join(workdir, "plans"),
                              "DOCUMENT_ROOT": os.path.join(workdir, "documents"),
                              "DECK_TAKEOFF_ROOT": os.path.join(workdir, "deck_takeoff")})
    with application.app_context():
        cfg = Config(str(ROOT / "migrations" / "alembic.ini"))
        cfg.set_main_option("script_location", str(ROOT / "migrations"))
        cfg.set_main_option("sqlalchemy.url", uri)
        command.upgrade(cfg, "head")
        from app.models import Client, CostItem, Project
        from app.models.subcontractor import Subcontractor
        from app.models.supplier_catalogue import ContractorSupplierAccount, Supplier, SupplierLocation
        from app.models.user import UserMembership
        from app.services.access_domains import set_field_only
        from app.services.documents.contexts import resolve_context
        from app.services.documents.ingest import Actor, file_document, prepare_upload
        from app.services.equipment import clean_fields, create_equipment
        from app.services.instance_authority import set_instance_owner
        from app.services.local_time import local_today
        from app.services.organizations import DEFAULT_ORGANIZATION_ID as ORG
        from app.services.permit_foundation import establish_project_location_and_profile
        from app.services.proposals import create_proposal_template
        from app.services.schedule import assign_user, create_schedule_item
        from app.services.work_structure import add_project_element, ensure_baseline_work_catalog
        from tests.auth_fixtures import ensure_office_user
        from tests.documents_support import text_pdf
        from tests.guided_support import COST_ITEMS

        def membership(user):
            return UserMembership.query.filter_by(user_id=user.id, organization_id=ORG).one()

        ben = ensure_office_user(email=PEOPLE["ben"][0], password=PEOPLE["ben"][1], display_name=PEOPLE["ben"][2])
        set_instance_owner(ORG, membership(ben).id, ben.id)
        kevin = ensure_office_user(email=PEOPLE["kevin"][0], password=PEOPLE["kevin"][1],
                                   display_name=PEOPLE["kevin"][2])
        set_field_only(membership(kevin), True, ben)
        customers = []
        for name, street, town, postal in CUSTOMERS:
            row = Client(name=name, organization_id=ORG, email=name.split()[0].lower() + "@example.invalid",
                         phone="613-555-0101", street_address=street, city=town, province_state="Ontario",
                         postal_code=postal, country="Canada")
            db.session.add(row)
            customers.append(row)
        for code, name, unit, cost in COST_ITEMS:
            db.session.add(CostItem(code=code, name=name, category="Material", unit=unit, unit_cost=Decimal(cost),
                                    default_markup_percent=Decimal("0"), organization_id=ORG, is_active=True))
        db.session.commit()
        create_proposal_template(name="Synthetic standard", organization_id=ORG, is_default=True)

        def located(project, street, town):
            establish_project_location_and_profile(project.id, {"street": street, "municipality": town,
                                                                "province_state": "Ontario", "postal_zip": "K0G 1N0",
                                                                "country": "Canada"}, None, organization_id=ORG,
                                                   generated_by="Seed (synthetic)", commit=False)

        job = Project(name="Harbour Lane deck (synthetic)", client_id=customers[0].id, organization_id=ORG,
                      status="Active")
        db.session.add(job)
        db.session.flush()
        located(job, "40 Harbour Lane", "Merrickville")
        others = []
        for name, who, status in PROJECTS:
            row = Project(name=name, client_id=customers[who].id, organization_id=ORG, status=status)
            db.session.add(row)
            db.session.flush()
            located(row, CUSTOMERS[who][1], CUSTOMERS[who][2])
            others.append(row)
        db.session.commit()
        ensure_baseline_work_catalog()
        element = add_project_element(project_id=job.id, display_name="Deck framing (synthetic)", organization_id=ORG)
        item = create_schedule_item(project_id=job.id, project_work_element_id=element.id,
                                    scheduled_start=local_today(), scheduled_end=local_today(), organization_id=ORG)
        assign_user(item.id, worker_user_id=kevin.id, organization_id=ORG)
        db.session.commit()

        sub = Subcontractor(organization_id=ORG, code="ACME", legal_name="Acme Framing (synthetic)", status="ACTIVE")
        supplier = Supplier(code="VBS-DENSITY", legal_name="Valley Building Supply (synthetic)", status="ACTIVE")
        db.session.add_all([sub, supplier])
        db.session.flush()
        location = SupplierLocation(supplier_id=supplier.id, code="MAIN", display_name="Main yard", status="ACTIVE")
        db.session.add(location)
        db.session.flush()
        db.session.add(ContractorSupplierAccount(organization_id=ORG, supplier_id=supplier.id,
                                                 supplier_location_id=location.id, status="ACTIVE"))
        db.session.commit()
        equipment = create_equipment(ORG, ben, clean_fields({"name": "Truck 3 (synthetic)", "category": "OTHER"}))

        actor = Actor.of(ben)
        today = local_today()
        filed = (("company", None, ("Company safety policy.pdf", "Health and safety policy (synthetic)")),
                 ("company", None, ("Insurance certificate.pdf", "Certificate of insurance (synthetic)")),
                 ("project", job.id, ("Deck permit drawings.pdf", "Deck drawings (synthetic)")),
                 ("project", job.id, ("Site photos.pdf", "Site photos (synthetic)")),
                 ("customer", customers[0].id, ("Signed contract.pdf", "Customer contract (synthetic)")),
                 ("supplier", supplier.id, ("Price list.pdf", "Supplier price list (synthetic)")),
                 ("subcontractor", sub.id, ("WSIB clearance.pdf", "Clearance certificate (synthetic)")),
                 ("person", membership(kevin).id, ("Working at heights.pdf", "Training certificate (synthetic)")),
                 ("equipment", equipment.id, ("Truck 3 registration.pdf", "Vehicle registration (synthetic)")))
        for kind, target, (filename, line) in filed:
            blob = prepare_upload(filename, text_pdf(line, filename))
            file_document(ORG, actor, blob=blob, context=resolve_context(ORG, kind, target), today=today)
        facts = {"people": PEOPLE, "customer_id": customers[0].id, "field_job_id": job.id,
                 "project_ids": [p.id for p in others], "sub_id": sub.id, "supplier_id": supplier.id,
                 "kevin_membership_id": membership(kevin).id, "equipment_id": equipment.id, "database_uri": uri}
    port = int(os.environ["DENSITY_PAGE_PORT"])
    print("FACTS " + json.dumps(facts), flush=True)
    print(f"READY {port}", flush=True)
    application.run(host="127.0.0.1", port=port, use_reloader=False, threaded=True)


if __name__ == "__main__":
    main()
