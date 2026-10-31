"""Local office and Supplier Hub for the Darcy browser walk (tools/release/evidence_supplier_hub.mjs).

Temporary database and takeoff folder, synthetic data only, clearly labelled. Seeds what exists before
the walk starts: the office sign-in, BMR Winchester (synthetic) with Darcy's sign-in, a rival supplier
with its own sign-in, two synthetic deck projects with their Form 2 requests issued, and one earlier
request on the second project that Darcy already quoted (leaving its last line unpriced) and the office
recorded. Everything the walk proves (send, quote, record, approve, order, confirm, delivery change) is
done in the browser. It never reads the hosted database and holds no real prices.
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

from app import create_app, db  # noqa: E402
import app.models  # noqa: E402,F401  (models load before app.services)
from app.services.local_time import local_today  # noqa: E402  (the office's date, as the app uses)

OFFICE = ("office@example.com", "office-test-password")
DARCY = ("Darcy Synthetic", "darcy.store@example.invalid", "Synthetic-darcy-pass-1")
RIVAL = ("Riley Rival (synthetic)", "rival.store@example.invalid", "Synthetic-rival-pass-1")
PROJECT = "Harbour Lane deck (synthetic)"
CLIENT = "Synthetic Client Okonkwo-Lindqvist"
ADDRESS = "12 Harbour Lane, Winchester (synthetic)"
SECOND = "Rideau Street deck (synthetic)"
# Internal office figures a supplier must never see: a company cost, its markup, the labour rate.
INTERNAL_COST = ("INT-ZEPHYR", "Zephyr internal crew allowance (synthetic)", "8765.43", "41.25")
TODAY = local_today()


def _set_password(user, password):
    from app.services.auth import hash_password

    user.password_hash = hash_password(password)
    db.session.commit()


def _facts_form():
    from tests.test_deck_takeoff_linda_j1 import TEST_PRODUCT

    form = {"actor_display_name": "Office Test User", "facts_source": "Synthetic test values, not a product selection"}
    for category, values in TEST_PRODUCT.items():
        for name, value in values.items():
            form[f"{category}.{name}"] = ", ".join(str(v) for v in value) if isinstance(value, list) else str(value)
    return form


def seed_records() -> dict:
    from app.models import Client, CostItem, Project
    from app.services import supplier_hub as H
    from app.services.labour_engine import ensure_org_001_direct_labour_cost_rate_standard
    from app.services.material_catalogue import ensure_canonical_material_seed
    from app.services.organizations import DEFAULT_ORGANIZATION_ID as ORG, ensure_default_organization
    from app.services.project_construction_model import save_construction_model_revision
    from app.services.supplier_catalogue import (
        create_contractor_supplier_account,
        create_supplier,
        create_supplier_location,
    )
    from tests.auth_fixtures import ensure_office_user
    from tests.fixtures.construction_model.linda_j1_takeoff_fixture import SOURCE_REFERENCE, model

    ensure_default_organization()
    ensure_canonical_material_seed()
    ensure_org_001_direct_labour_cost_rate_standard()
    from tests.procurement_support import grant_company_management

    grant_company_management(ensure_office_user(), ORG)
    code, name, cost, markup = INTERNAL_COST
    db.session.add(CostItem(organization_id=ORG, code=code, name=name, category="Labour", unit="day",
                            unit_cost=Decimal(cost), default_markup_percent=Decimal(markup)))
    bmr = create_supplier(code="SYN-BMR", legal_name="BMR Winchester (synthetic)", demo_synthetic=True)
    bmr_loc = create_supplier_location(supplier_id=bmr.id, code="WINCHESTER", display_name="Winchester", demo_synthetic=True)
    bmr_account = create_contractor_supplier_account(organization_id=ORG, supplier_id=bmr.id,
                                                     supplier_location_id=bmr_loc.id, demo_synthetic=True)
    rival = create_supplier(code="SYN-RIVAL", legal_name="Rival Synthetic Supply", demo_synthetic=True)
    rival_loc = create_supplier_location(supplier_id=rival.id, code="MAIN", display_name="Rival main", demo_synthetic=True)
    rival_account = create_contractor_supplier_account(organization_id=ORG, supplier_id=rival.id,
                                                       supplier_location_id=rival_loc.id, demo_synthetic=True)
    darcy, _ = H.add_supplier_user(organization_id=ORG, supplier=bmr, display_name=DARCY[0], email=DARCY[1],
                                   actor_name="Synthetic setup")
    _set_password(darcy, DARCY[2])
    riley, _ = H.add_supplier_user(organization_id=ORG, supplier=rival, display_name=RIVAL[0], email=RIVAL[1],
                                   actor_name="Synthetic setup")
    _set_password(riley, RIVAL[2])
    projects = []
    for project_name, client_name, address in ((PROJECT, CLIENT, ADDRESS),
                                               (SECOND, "Synthetic Client Second", "40 Rideau Street (synthetic)")):
        owner = Client(name=client_name, organization_id=ORG)
        db.session.add(owner)
        db.session.flush()
        project = Project(name=project_name, client_id=owner.id, organization_id=ORG, status="Estimating", address=address)
        db.session.add(project)
        db.session.commit()
        save_construction_model_revision(organization_id=ORG, project_id=project.id, content=model(),
                                         source_kind="source_document", source_reference=SOURCE_REFERENCE,
                                         actor_display_name="Synthetic setup")
        projects.append(project)
    db.session.commit()
    return {"bmr_id": bmr.id, "bmr_account": bmr_account.id, "rival_id": rival.id, "rival_account": rival_account.id,
            "project_id": projects[0].id, "second_id": projects[1].id}


def seed_flow(application, ids: dict) -> dict:
    """Office and Darcy steps that happen before the walk, through the same routes the browser uses."""
    from app.models.supplier_portal import SupplierRequestShare

    application.config["WTF_CSRF_ENABLED"] = False  # seed only; the browser walk runs with CSRF on
    office = application.test_client()
    assert office.post("/login", data={"email": OFFICE[0], "password": OFFICE[1]}).status_code == 302
    request_ids = {}
    for key in ("project_id", "second_id"):
        pid = ids[key]
        assert office.post(f"/projects/{pid}/deck-takeoff/product-facts", data=_facts_form()).status_code in (200, 302)
        issued = office.post(f"/projects/{pid}/deck-takeoff/request",
                             data={"contractor_supplier_account_id": ids["bmr_account"], "actor_display_name": "Office Test User"})
        assert issued.status_code == 200 and issued.mimetype == "application/pdf", issued.data[:300]
        with application.app_context():
            from app.services.deck_takeoff import storage
            from app.services.organizations import DEFAULT_ORGANIZATION_ID as ORG

            request_ids[key] = storage.list_requests(ORG, pid)[0]["request_id"]
    # The earlier request: sent, quoted by Darcy with its last line unpriced, recorded by the office.
    sent = office.post(f"/projects/{ids['second_id']}/deck-takeoff/requests/{request_ids['second_id']}/send-to-supplier",
                       data={"needed_by": (TODAY + timedelta(days=12)).isoformat()})
    assert sent.status_code == 302
    darcy = application.test_client()
    assert darcy.post("/supplier/login", data={"email": DARCY[1], "password": DARCY[2]}).status_code == 302
    with application.app_context():
        from app.services.deck_takeoff import storage
        from app.services.organizations import DEFAULT_ORGANIZATION_ID as ORG

        share = SupplierRequestShare.query.filter_by(project_id=ids["second_id"]).one()
        share_id, lines = share.id, share.shared_json["lines"]
        manifest = storage.load_request(ORG, ids["second_id"], share.source_ref)
        codes = {int(l["number"]): l.get("canonical_material_code") or (l.get("canonical_identity") or {}).get("code")
                 for l in manifest["lines"]}
    form = {"bmr_contact": DARCY[0], "response_date": TODAY.isoformat(),
            "valid_until": (TODAY + timedelta(days=30)).isoformat(), "minutes_reported": "9"}
    # One SKU and one price per product, as a store has: two lines for the same product share them.
    skus = {}
    for line in lines[:-1]:
        n = "%02d" % int(line["number"])
        index = skus.setdefault(codes.get(int(line["number"])) or n, len(skus))
        form.update({f"sku_{n}": f"BMR-{1040 + index * 7:05d}", f"unit_cost_{n}": f"{12 + index * 3}.50", f"discount_{n}": "5"})
    assert darcy.post(f"/supplier/{ids['bmr_id']}/requests/{share_id}/quote", data=form).status_code == 302
    with application.app_context():
        share = db.session.get(SupplierRequestShare, share_id)
        assert share.status == "RETURNED", share.status
        response_ref = share.response_ref
    recorded = office.post(f"/projects/{ids['second_id']}/deck-takeoff/responses/{response_ref}/record",
                           data={"actor_display_name": "Office Test User", "notes_reviewed": "yes"})
    assert recorded.status_code == 302, recorded.data[:300]
    # The rival store's own concrete request, which Darcy must never see.
    office.post(f"/projects/{ids['second_id']}/concrete-requests", data={
        "volume_m3": "3.0", "strength_mpa": "25", "delivery_date": (TODAY + timedelta(days=9)).isoformat(),
        "delivery_window": "8:00–10:00", "placement": "Chute", "contractor_supplier_account_id": ids["rival_account"]})
    with application.app_context():
        rival_share = SupplierRequestShare.query.filter_by(supplier_id=ids["rival_id"]).one()
        rival_number, rival_share_id = rival_share.number, rival_share.id
        earlier_number = db.session.get(SupplierRequestShare, share_id).number
        priced_last = lines[-1]["description"]
    application.config["WTF_CSRF_ENABLED"] = True
    return {"request_id": request_ids["project_id"], "earlier_share_id": share_id, "earlier_number": earlier_number,
            "rival_share_id": rival_share_id, "rival_number": rival_number, "unpriced_description": priced_last,
            "earlier_lines": len(lines)}


def main():
    workdir = tempfile.mkdtemp(prefix="supplier-hub-")
    application = create_app({"TESTING": True, "CALIBRAYTAI_HOSTED": "0",
                              "SQLALCHEMY_DATABASE_URI": f"sqlite:///{workdir}/hub.db",
                              "SECRET_KEY": "test-secret-key", "TRANSACTIONAL_EMAIL_PROVIDER": "local",
                              "DECK_TAKEOFF_ROOT": f"{workdir}/deck_takeoff"})
    with application.app_context():
        db.create_all()
        facts = seed_records()
    facts.update(seed_flow(application, facts))
    facts.update({"office": list(OFFICE), "darcy": [DARCY[1], DARCY[2]], "darcy_name": DARCY[0],
                  "rival": [RIVAL[1], RIVAL[2]], "project": PROJECT, "client": CLIENT, "address": ADDRESS,
                  "internal_cost": list(INTERNAL_COST), "today": TODAY.isoformat()})
    port = int(os.environ["SUPPLIER_HUB_PAGE_PORT"])
    print("FACTS " + json.dumps(facts), flush=True)
    print(f"READY {port}", flush=True)
    application.run(host="127.0.0.1", port=port, use_reloader=False, threaded=True)


if __name__ == "__main__":
    main()
