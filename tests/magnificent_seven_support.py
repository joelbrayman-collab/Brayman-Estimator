"""Synthetic Brayman Construction for the Magnificent Seven tests and browser walk (25 Oct 2026).

Everything is synthetic: Ben (owner), Suzanne (office, accounting), Kevin and Liam (Field-only crew), another company's
owner, the customer Morgan Ellis, the job "Harbour Lane Pool Deck (synthetic)" in Merrickville with a work plan and
Kevin booked on it today, Shop / Company Work, the store "BMR Winchester (synthetic)" with Darcy's Supplier Hub
sign-in, one confirmed purchase order waiting for delivery, and a test QuickBooks Online company (the in-memory fake;
nothing reaches Intuit). Used by tests/test_magnificent_seven.py and tests/magnificent_seven_server.py.
"""

from __future__ import annotations

import base64
import io
from datetime import datetime, timedelta
from decimal import Decimal

from app import db
from app.services.local_time import local_today
from app.services.organizations import DEFAULT_ORGANIZATION_ID as ORG

PEOPLE = {
    "ben": ("ben.mag7@example.invalid", "Synthetic-ben-mag7-1", "Ben Brayman (synthetic)"),
    "suzanne": ("suzanne.mag7@example.invalid", "Synthetic-suzanne-mag7-1", "Suzanne Books (synthetic)"),
    "kevin": ("kevin.mag7@example.invalid", "Synthetic-kevin-mag7-1", "Kevin Field (synthetic crew)"),
    "liam": ("liam.mag7@example.invalid", "Synthetic-liam-mag7-1", "Liam Crew (synthetic crew)"),
    "other": ("other.mag7@example.invalid", "Synthetic-other-mag7-1", "Other Builder Owner (synthetic)"),
    "darcy": ("darcy.mag7@example.invalid", "Synthetic-darcy-mag7-1", "Darcy Store (synthetic)"),
}
OTHER_ORG = "ORG-MAG7-OTHER"
TOKEN_KEY = base64.urlsafe_b64encode(b"m" * 32).decode()


def receipt_jpeg(color=(240, 236, 220), text_shade=40) -> bytes:
    """A small synthetic receipt photo (JPEG)."""
    from PIL import Image, ImageDraw

    image = Image.new("RGB", (360, 520), color)
    draw = ImageDraw.Draw(image)
    draw.rectangle([20, 20, 340, 60], outline=(text_shade,) * 3, width=3)
    for i, y in enumerate(range(90, 460, 34)):
        draw.line([30, y, 330 - (i % 3) * 40, y], fill=(text_shade,) * 3, width=4)
    out = io.BytesIO()
    image.save(out, format="JPEG", quality=85)
    return out.getvalue()


def _user(key, organization_id=ORG):
    from tests.auth_fixtures import ensure_office_user

    email, password, name = PEOPLE[key]
    return ensure_office_user(email=email, password=password, display_name=name, organization_id=organization_id)


def build(application, *, fake_qbo=True, today=None) -> dict:
    """Seed the synthetic company through the same services the pages use. Returns the facts."""
    from app.models import Client, Project
    from app.models.organization import Organization
    from app.models.project import ProjectLocation
    from app.models.supplier_portal import SupplierPurchaseOrder, SupplierRequestShare
    from app.models.user import UserMembership
    from app.services.access_domains import set_field_only
    from app.services.instance_authority import set_instance_owner
    from app.services.material_catalogue import ensure_canonical_material_seed
    from app.services.organizations import ensure_default_organization
    from app.services.schedule import assign_user, create_schedule_item
    from app.services.supplier_catalogue import (
        create_contractor_supplier_account,
        create_supplier,
        create_supplier_location,
    )
    from app.services.supplier_hub import add_supplier_user
    from app.services.time_entry import ensure_company_time_project
    from app.services.work_structure import add_project_activity, add_project_element

    today = today or local_today()
    ensure_default_organization()
    ensure_canonical_material_seed()
    application.config["QBO_TOKEN_KEY"] = TOKEN_KEY
    ben = _user("ben")
    set_instance_owner(ORG, UserMembership.query.filter_by(user_id=ben.id, organization_id=ORG).one().id, ben.id)
    db.session.commit()
    suzanne = _user("suzanne")
    kevin = _user("kevin")
    liam = _user("liam")
    for crew in (kevin, liam):
        set_field_only(UserMembership.query.filter_by(user_id=crew.id, organization_id=ORG).one(), True, ben)
    if db.session.get(Organization, OTHER_ORG) is None:
        db.session.add(Organization(id=OTHER_ORG, legal_name="Other Synthetic Builder",
                                    display_name="Other Synthetic Builder", is_active=True))
        db.session.commit()
    other = _user("other", OTHER_ORG)

    customer = Client(name="Morgan Ellis (synthetic)", organization_id=ORG, email="morgan.ellis@example.invalid")
    db.session.add(customer)
    db.session.flush()
    project = Project(name="Harbour Lane Pool Deck (synthetic)", client_id=customer.id, organization_id=ORG,
                      status="In Progress", project_number="BC-2026-014", address="14 Harbour Lane (synthetic)")
    db.session.add(project)
    db.session.flush()
    db.session.add(ProjectLocation(project_id=project.id, organization_id=ORG, street="14 Harbour Lane",
                                   municipality="Merrickville", province_state="Ontario", postal_zip="K0G 1N0",
                                   country="Canada"))
    second = Project(name="Kemptville Garage (synthetic)", client_id=customer.id, organization_id=ORG,
                     status="In Progress", project_number="BC-2026-015")
    db.session.add(second)
    db.session.commit()
    # The job's original work (from the accepted estimate in real life): not extra work.
    element = add_project_element(project_id=project.id, display_name="Deck framing", organization_id=ORG,
                                  scope_origin="ORIGINAL", actor_display_name="Ben Brayman (synthetic)")
    activity = add_project_activity(project_work_element_id=element.id, display_name="Frame the deck",
                                    organization_id=ORG, scope_origin="ORIGINAL",
                                    actor_display_name="Ben Brayman (synthetic)")
    item = create_schedule_item(project_id=project.id, project_work_element_id=element.id,
                                scheduled_start=today - timedelta(days=1),
                                scheduled_end=today + timedelta(days=2), organization_id=ORG)
    assign_user(item.id, worker_user_id=kevin.id, organization_id=ORG)
    element2 = add_project_element(project_id=second.id, display_name="Garage slab", organization_id=ORG,
                                   scope_origin="ORIGINAL", actor_display_name="Ben Brayman (synthetic)")
    add_project_activity(project_work_element_id=element2.id, display_name="Form the slab", organization_id=ORG,
                         scope_origin="ORIGINAL", actor_display_name="Ben Brayman (synthetic)")
    company = ensure_company_time_project(ORG, actor_display_name="Ben Brayman (synthetic)")
    # The plan was made last week (its history is dated then), so today's reminders see no schedule change.
    from app.models.schedule import WorkScheduleHistory

    for row in WorkScheduleHistory.query.filter_by(work_schedule_item_id=item.id).all():
        row.created_at = datetime.utcnow() - timedelta(days=7)
    db.session.commit()

    supplier = create_supplier(code="MAG7-BMR", legal_name="BMR Winchester (synthetic)", demo_synthetic=True)
    location = create_supplier_location(supplier_id=supplier.id, code="WINCHESTER", display_name="Winchester",
                                        demo_synthetic=True)
    account = create_contractor_supplier_account(organization_id=ORG, supplier_id=supplier.id,
                                                 supplier_location_id=location.id, demo_synthetic=True)
    from app.services.auth import hash_password

    darcy, _ = add_supplier_user(organization_id=ORG, supplier=supplier, display_name=PEOPLE["darcy"][2],
                                 email=PEOPLE["darcy"][0], actor_name="Ben Brayman (synthetic)")
    darcy.password_hash = hash_password(PEOPLE["darcy"][1])
    db.session.commit()

    # One confirmed order waiting for delivery today (synthetic set-up of the existing order records).
    share = SupplierRequestShare(organization_id=ORG, project_id=project.id, supplier_id=supplier.id,
                                 contractor_supplier_account_id=account.id, number="SRQ-MAG7-1", request_kind="MATERIAL",
                                 source_kind="DECK_FORM2", source_ref="MAG7-SEED", shared_json={"lines": []},
                                 status="RETURNED", sent_by_name="Ben Brayman (synthetic)",
                                 returned_at=datetime.utcnow())
    db.session.add(share)
    db.session.flush()
    order = SupplierPurchaseOrder(
        organization_id=ORG, project_id=project.id, share_id=share.id, supplier_id=supplier.id, number="PO-MAG7-1",
        quote_ref="RSP-SEED", total=Decimal("1250.00"), delivery_date=today, scheduled_date=today,
        delivery_address="14 Harbour Lane (synthetic)", status="CONFIRMED", placed_by_name="Ben Brayman (synthetic)",
        placed_at=datetime.utcnow() - timedelta(days=3), supplier_responded_by_name=PEOPLE["darcy"][2],
        supplier_responded_at=datetime.utcnow() - timedelta(days=2),
        lines_json=[
            {"number": 1, "description": "2x8 PT 12 ft (synthetic)", "sku": "PT-2812", "quantity": "40", "unit": "EA",
             "net_unit_cost": "18.50", "line_value": "740.00", "cost_approved": True},
            {"number": 2, "description": "Joist hangers 2x8 (synthetic)", "sku": "LUS28", "quantity": "60", "unit": "EA",
             "net_unit_cost": "8.50", "line_value": "510.00", "cost_approved": True},
        ])
    db.session.add(order)
    db.session.commit()

    fake = None
    if fake_qbo:
        from app.services.quickbooks_online_transport import FakeQuickBooksOnline

        fake = FakeQuickBooksOnline().seed_standard()
        fake.add("Vendor", DisplayName="BMR Winchester (synthetic)", Active=True)
        fake.add("Vendor", DisplayName="Home Hardware Kemptville (synthetic)", Active=True)
        fake.add("Customer", DisplayName="BC-2026-014 Harbour Lane Pool Deck (synthetic)", Job=True, Active=True)
        application.config["QBO_TEST_TRANSPORT"] = fake
    return {"ben": ben, "suzanne": suzanne, "kevin": kevin, "liam": liam, "other": other, "darcy": darcy,
            "project": project, "second": second, "company": company, "element": element, "activity": activity,
            "item": item, "supplier": supplier, "account": account, "order": order, "share": share, "fake": fake}


def connect_fake_qbo(http, fake, *, realm=None):
    """Press Connect to QuickBooks, approve on the (fake) Intuit page and come back through the callback."""
    from urllib.parse import parse_qs, urlparse

    start = http.post("/accounting/quickbooks-online/connect")
    assert start.status_code == 302 and start.headers["Location"].startswith("https://appcenter.intuit.com/connect/oauth2")
    query = parse_qs(urlparse(start.headers["Location"]).query)
    assert query["scope"] == ["com.intuit.quickbooks.accounting"] and query["response_type"] == ["code"]
    code = fake.issue_code()
    back = http.get(f"/accounting/quickbooks/callback?code={code}&realmId={realm or fake.realm_id}"
                    f"&state={query['state'][0]}")
    assert back.status_code == 302
    return query


def map_fake_accounts(http, fake):
    accounts = {r["Name"]: r["Id"] for r in fake.entities["Account"].values()}
    codes = {r["Name"]: r["Id"] for r in fake.entities["TaxCode"].values()}
    return http.post("/accounting/quickbooks-online", data={
        "action": "mapping", "expense_account_id": accounts["Job Materials"],
        "payment_account_id": accounts["Company Visa"], "payment_type": "CreditCard",
        "tax_code_id": codes["HST ON"], "no_tax_code_id": codes["Exempt"], "class_id": "", "auto_send": "1"})
