"""Local office and Supplier Hub for the Supplier Unit Pricing browser walk (tools/release/evidence_unit_pricing.mjs).

Temporary database, mail captured to a temporary folder, synthetic data only. Seeds only what exists before the walk:
the office sign-in, one project with a job town, a synthetic store with its own Supplier Hub sign-in, and a second
synthetic store with no sign-in (it gets the approved PDF form). Every request, price, conversion, approval, order,
signature and confirmation the walk proves is done in the browser. It never reads the hosted database.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from app import create_app, db  # noqa: E402
import app.models  # noqa: E402,F401

OFFICE = ("office@example.com", "office-test-password")
STORE = ("Riley Synthetic (store)", "riley.store@example.invalid", "Synthetic-riley-pass-1")


def seed() -> dict:
    from app.models import Client, Project
    from app.services import supplier_hub as H
    from app.services.auth import hash_password
    from app.services.jurisdiction import ensure_jurisdiction_seed
    from app.services.organizations import DEFAULT_ORGANIZATION_ID as ORG, ensure_default_organization
    from app.services.supplier_catalogue import (
        create_contractor_supplier_account,
        create_supplier,
        create_supplier_location,
    )
    from tests.auth_fixtures import ensure_office_user

    ensure_default_organization()
    ensure_jurisdiction_seed(commit=True)
    ensure_office_user()
    db.session.commit()
    store = create_supplier(code="SYN-UNIT", legal_name="Lakeside Building Supply (synthetic)", demo_synthetic=True)
    loc = create_supplier_location(supplier_id=store.id, code="MAIN", display_name="Main", demo_synthetic=True)
    account = create_contractor_supplier_account(organization_id=ORG, supplier_id=store.id,
                                                 supplier_location_id=loc.id, demo_synthetic=True)
    riley, _ = H.add_supplier_user(organization_id=ORG, supplier=store, display_name=STORE[0], email=STORE[1],
                                   actor_name="Synthetic setup")
    riley.password_hash = hash_password(STORE[2])
    offline = create_supplier(code="SYN-OFFLINE", legal_name="Hillside Lumber (synthetic, no sign-in)",
                              demo_synthetic=True)
    oloc = create_supplier_location(supplier_id=offline.id, code="MAIN", display_name="Main", demo_synthetic=True)
    oaccount = create_contractor_supplier_account(organization_id=ORG, supplier_id=offline.id,
                                                  supplier_location_id=oloc.id, demo_synthetic=True)
    owner = Client(name="Sam Synthetic Owner", organization_id=ORG)
    db.session.add(owner)
    db.session.flush()
    project = Project(name="Elm Street siding (synthetic)", address="5 Elm Street, Winchester (synthetic)",
                      client_id=owner.id, status="Active", organization_id=ORG)
    db.session.add(project)
    db.session.commit()
    return {"project_id": project.id, "supplier_id": store.id, "account_id": account.id,
            "offline_account_id": oaccount.id, "store_name": store.legal_name, "offline_name": offline.legal_name}


def main():
    workdir = tempfile.mkdtemp(prefix="unit-pricing-")
    port = int(os.environ["UNIT_PRICING_PAGE_PORT"])
    mail = f"{workdir}/mail"
    os.makedirs(mail, exist_ok=True)
    application = create_app({"TESTING": True, "CALIBRAYTAI_HOSTED": "0",
                              "SQLALCHEMY_DATABASE_URI": f"sqlite:///{workdir}/unit.db",
                              "SECRET_KEY": "test-secret-key", "TRANSACTIONAL_EMAIL_PROVIDER": "local",
                              "MAIL_CAPTURE_ROOT": mail, "PUBLIC_BASE_URL": f"http://127.0.0.1:{port}"})
    with application.app_context():
        db.create_all()
        facts = seed()
    facts.update({"office": list(OFFICE), "store": [STORE[1], STORE[2]]})
    print("FACTS " + json.dumps(facts), flush=True)
    print(f"READY {port}", flush=True)
    application.run(host="127.0.0.1", port=port, use_reloader=False, threaded=True)


if __name__ == "__main__":
    main()
