"""Local office, signing pages and Supplier Hub for the CaliSIGN browser walk (tools/release/evidence_calisign.mjs).

Temporary database, mail captured to a temporary folder, synthetic data only, clearly labelled. Seeds only what
exists before the walk starts, through the same services and routes the tests use:

* a generated Brayman V1 contract (Ontario interim package, from the governed Family 05 master) on a project whose
  client has an email, ready to send;
* an approved change order on a second project, ready to send;
* a concrete request the rival-free synthetic store has quoted and the office has approved, ready to order, with
  the store's own Supplier Hub sign-in.

Nothing is signed here. Every send, signature, countersignature, order, confirmation and delivery change the walk
proves is done in the browser. It never reads the hosted database.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from datetime import timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from app import create_app, db  # noqa: E402
import app.models  # noqa: E402,F401
from app.services.local_time import local_today  # noqa: E402

OFFICE = ("office@example.com", "office-test-password")
STORE = ("Morgan Synthetic (store)", "morgan.store@example.invalid", "Synthetic-morgan-pass-1")
CLIENT_EMAIL = "pat.owner@example.invalid"
TODAY = local_today()


def _set_password(user, password):
    from app.services.auth import hash_password

    user.password_hash = hash_password(password)
    db.session.commit()


def seed_records() -> dict:
    from app.models import Client, Project
    from app.services import supplier_hub as H
    from app.services.brayman_v1_interim_contract import ensure_brayman_v1_interim_ontario_package
    from app.services.commercial_context import create_initial_commercial_context
    from app.services.jurisdiction import ensure_jurisdiction_seed
    from app.services.organizations import DEFAULT_ORGANIZATION_ID as ORG, ensure_default_organization
    from app.services.supplier_catalogue import (
        create_contractor_supplier_account,
        create_supplier,
        create_supplier_location,
    )
    from tests.auth_fixtures import ensure_office_user
    from tests.test_brayman_v1_interim_contract import COMMERCIAL_CREATE, _generate, _issued, _ottawa_project
    from tests.test_native_signing_sign_a_fg033 import _approved_change_order

    ensure_default_organization()
    ensure_jurisdiction_seed(commit=True)
    ensure_office_user()
    ensure_brayman_v1_interim_ontario_package()
    db.session.commit()

    # Contract: generated from the accepted proposal, not sent.
    contract_project = _ottawa_project(name="Maple Court addition (synthetic)", address="100 Test Civic Street, Ottawa")
    contract_project.client.name = "Pat Synthetic Owner"
    contract_project.client.email = CLIENT_EMAIL
    db.session.commit()
    version, proposal = _issued(contract_project, number="EST-CALISIGN-1")
    generated = _generate(contract_project, version, proposal)
    assert generated.generated, generated

    # Change order: approved, not sent.
    owner = Client(name="Robin Synthetic Owner", email="robin.owner@example.invalid", organization_id=ORG)
    db.session.add(owner)
    db.session.flush()
    co_project = Project(name="Birch Lane kitchen (synthetic)", address="22 Birch Lane, Ottawa (synthetic)",
                         client_id=owner.id, status="Active", organization_id=ORG)
    db.session.add(co_project)
    db.session.flush()
    create_initial_commercial_context(project_id=co_project.id, data=COMMERCIAL_CREATE)
    db.session.commit()
    change_order = _approved_change_order(co_project, title="Add pantry pocket door (synthetic)")

    # Supplier: one synthetic store with its Supplier Hub sign-in, and a project to order for.
    store = create_supplier(code="SYN-CALISIGN", legal_name="Northfield Ready-Mix (synthetic)", demo_synthetic=True)
    loc = create_supplier_location(supplier_id=store.id, code="MAIN", display_name="Main yard", demo_synthetic=True)
    account = create_contractor_supplier_account(organization_id=ORG, supplier_id=store.id,
                                                 supplier_location_id=loc.id, demo_synthetic=True)
    morgan, _ = H.add_supplier_user(organization_id=ORG, supplier=store, display_name=STORE[0], email=STORE[1],
                                    actor_name="Synthetic setup")
    _set_password(morgan, STORE[2])
    yard = Client(name="Synthetic Client Supplier Walk", organization_id=ORG)
    db.session.add(yard)
    db.session.flush()
    order_project = Project(name="Cedar Row garage slab (synthetic)", address="8 Cedar Row, Winchester (synthetic)",
                            client_id=yard.id, status="Active", organization_id=ORG)
    db.session.add(order_project)
    db.session.commit()
    return {"contract_project_id": contract_project.id, "contract_id": generated.contract_id,
            "co_project_id": co_project.id, "change_order_id": change_order.id, "change_order_number": change_order.number,
            "supplier_id": store.id, "supplier_account": account.id, "order_project_id": order_project.id}


def seed_flow(application, ids: dict) -> dict:
    """The concrete request: asked by the office, quoted by the store, approved by the office (no order yet)."""
    from app.models.supplier_portal import SupplierRequestShare

    application.config["WTF_CSRF_ENABLED"] = False  # seed only; the browser walk runs with CSRF on
    office = application.test_client()
    assert office.post("/login", data={"email": OFFICE[0], "password": OFFICE[1]}).status_code == 302
    asked = office.post(f"/projects/{ids['order_project_id']}/concrete-requests", data={
        "volume_m3": "6.5", "strength_mpa": "32", "delivery_date": (TODAY + timedelta(days=10)).isoformat(),
        "delivery_window": "7:00–9:00", "placement": "Chute", "contractor_supplier_account_id": ids["supplier_account"]})
    assert asked.status_code in (200, 302), asked.data[:300]
    with application.app_context():
        share = SupplierRequestShare.query.filter_by(supplier_id=ids["supplier_id"]).one()
        share_id = share.id
    store = application.test_client()
    assert store.post("/supplier/login", data={"email": STORE[1], "password": STORE[2]}).status_code == 302
    quoted = store.post(f"/supplier/{ids['supplier_id']}/requests/{share_id}/quote",
                        data={"price_per_m3": "212", "valid_until": (TODAY + timedelta(days=20)).isoformat()})
    assert quoted.status_code == 302
    approved = office.post(f"/projects/{ids['order_project_id']}/supplier-requests/{share_id}/approve-quote")
    assert approved.status_code == 302, approved.data[:300]
    with application.app_context():
        share = db.session.get(SupplierRequestShare, share_id)
        number = share.number
    application.config["WTF_CSRF_ENABLED"] = True
    return {"share_id": share_id, "share_number": number}


def main():
    workdir = tempfile.mkdtemp(prefix="calisign-")
    port = int(os.environ["CALISIGN_PAGE_PORT"])
    mail = os.environ.get("CALISIGN_MAIL_ROOT") or f"{workdir}/mail"
    os.makedirs(mail, exist_ok=True)
    application = create_app({"TESTING": True, "CALIBRAYTAI_HOSTED": "0",
                              "SQLALCHEMY_DATABASE_URI": f"sqlite:///{workdir}/calisign.db",
                              "SECRET_KEY": "test-secret-key", "TRANSACTIONAL_EMAIL_PROVIDER": "local",
                              "MAIL_CAPTURE_ROOT": mail, "PUBLIC_BASE_URL": f"http://127.0.0.1:{port}"})
    with application.app_context():
        db.create_all()
        facts = seed_records()
    facts.update(seed_flow(application, facts))
    facts.update({"office": list(OFFICE), "store": [STORE[1], STORE[2]], "store_name": STORE[0],
                  "client_email": CLIENT_EMAIL, "mail": mail, "today": TODAY.isoformat()})
    print("FACTS " + json.dumps(facts), flush=True)
    print(f"READY {port}", flush=True)
    application.run(host="127.0.0.1", port=port, use_reloader=False, threaded=True)


if __name__ == "__main__":
    main()
