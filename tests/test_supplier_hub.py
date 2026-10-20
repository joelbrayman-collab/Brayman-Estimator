"""Supplier Hub (Joel, 17 Oct 2026; ADR-047). Synthetic data only.

Separate supplier sign-in, isolation both ways, send one request to one supplier,
the supplier returns prices through the same reconciliation, the contractor records
and approves, places the order, and the supplier confirms it. Concrete is its own
request to its own supplier account, kept apart from material requests.
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from app import db
from app.models.supplier_catalogue import ContractorSupplierAccount
from app.models.supplier_portal import (
    SupplierPurchaseOrder,
    SupplierRequestEvent,
    SupplierRequestShare,
    SupplierUserMembership,
)
from app.models.transactional_message import TransactionalMessage
from app.models.user import User
from app.services.auth import hash_password
from app.services.organizations import DEFAULT_ORGANIZATION_ID
from app.services.supplier_catalogue import (
    create_contractor_supplier_account,
    create_supplier,
    create_supplier_location,
)
from app.services import supplier_hub as H
from tests.test_deck_takeoff_workflow import (  # noqa: F401
    RESPONSE_DATE,
    VALID_UNTIL,
    _issue,
    _setup,
    app,
    client,
)

DARCY = ("Darcy Synthetic", "darcy.store@example.invalid")


@pytest.fixture(autouse=True)
def _fresh_login_per_request(app):
    """The test fixture holds one app context, so flask-login's per-request user cache on g would
    leak between the office and supplier test clients. Production requests each get their own."""
    from flask import g

    def clear():
        g.pop("_login_user", None)

    app.before_request_funcs.setdefault(None, []).insert(0, clear)
    yield
PASSWORD = "Synthetic-supplier-pass-1"


def _supplier_client(app, email=DARCY[1], password=PASSWORD):
    supplier = app.test_client()
    response = supplier.post("/supplier/login", data={"email": email, "password": password})
    assert response.status_code == 302, response.data[:400]
    return supplier


def _give_sign_in(client, account, name=DARCY[0], email=DARCY[1]):
    page = client.post(f"/suppliers/{account.supplier_id}/users", data={"display_name": name, "email": email},
                       follow_redirects=True)
    assert b"can now sign in to the Supplier Hub" in page.data or b"now also has access" in page.data
    user = User.query.filter_by(email=email).one()
    user.password_hash = hash_password(PASSWORD)  # stands in for the emailed set-password link
    db.session.commit()
    return user


def _tomlinson():
    supplier = create_supplier(code="TEST-TOMLINSON", legal_name="Tomlinson concrete (synthetic)", demo_synthetic=True)
    location = create_supplier_location(supplier_id=supplier.id, code="MAIN", display_name="Tomlinson", demo_synthetic=True)
    return create_contractor_supplier_account(organization_id=DEFAULT_ORGANIZATION_ID, supplier_id=supplier.id,
                                              supplier_location_id=location.id, demo_synthetic=True)


def test_supplier_sign_in_is_separate_and_isolated_both_ways(app, client):
    _project, _other, account = _setup()
    _give_sign_in(client, account)
    assert TransactionalMessage.query.filter_by(to_email=DARCY[1]).count() == 1  # set-password link
    supplier = _supplier_client(app)
    home = supplier.get("/supplier/", follow_redirects=True)
    assert b"BMR Winchester (synthetic)" in home.data and b'data-workspace="supplier"' in home.data
    # A supplier never reaches office pages or the office API.
    office = supplier.get("/projects/")
    assert office.status_code == 302 and office.headers["Location"].endswith("/supplier/")
    assert supplier.get("/api/v1/projects").status_code == 403
    # The office sign-in also sends a supplier to the Supplier Hub.
    fresh = app.test_client()
    fresh.post("/login", data={"email": DARCY[1], "password": PASSWORD})
    assert fresh.get("/").headers["Location"].endswith("/supplier/")
    # An office user cannot open supplier pages, and an office person cannot be a supplier.
    office_attempt = client.get("/supplier/")
    assert office_attempt.status_code == 403, office_attempt.headers.get("Location")
    office_user = User.query.filter(User.email != DARCY[1]).first()
    with pytest.raises(H.SupplierHubError, match="cannot be both"):
        H.add_supplier_user(organization_id=DEFAULT_ORGANIZATION_ID, supplier=account.supplier,
                            display_name="Office", email=office_user.email, actor_name="test")
    # An office user cannot sign in on the supplier page.
    assert app.test_client().post("/supplier/login", data={"email": office_user.email, "password": "x"}).status_code == 401


def test_material_request_goes_to_the_supplier_and_comes_back_through_the_same_checks(app, client):
    project, _other, account = _setup()
    _give_sign_in(client, account)
    _pdf, fields, keys = _issue(client, project, account)
    request_id = fields["request_id"]["/V"]
    sent = client.post(f"/projects/{project.id}/deck-takeoff/requests/{request_id}/send-to-supplier",
                       data={"needed_by": (date.today() + timedelta(days=10)).isoformat()}, follow_redirects=True)
    assert b"is in their Supplier Hub inbox now" in sent.data
    share = SupplierRequestShare.query.one()
    # Only the approved shared fields: no customer name, no site address, no costs.
    flat = str(share.shared_json)
    assert project.name not in flat and "D'Arcy's Way" not in flat
    assert set(share.shared_json) == {"company", "contact_name", "contact_email", "project_reference",
                                      "delivery_town", "needed_by", "lines"}

    supplier = _supplier_client(app)
    page = supplier.get(f"/supplier/{account.supplier_id}/requests/{share.id}")
    assert page.status_code == 200 and project.name.encode() not in page.data and b"Arcy" not in page.data
    assert db.session.get(SupplierRequestShare, share.id).status == "OPENED"

    first = next(iter(keys.values()))
    values = {f"sku_{first}": "TEST-SKU-1", f"unit_cost_{first}": "10.00", f"discount_{first}": "10",
              "bmr_contact": DARCY[0], "response_date": RESPONSE_DATE, "valid_until": VALID_UNTIL,
              "minutes_reported": "12"}
    returned = supplier.post(f"/supplier/{account.supplier_id}/requests/{share.id}/quote", data=values,
                             follow_redirects=True)
    assert b"Quote returned to the contractor" in returned.data
    share = db.session.get(SupplierRequestShare, share.id)
    assert share.status == "RETURNED" and share.response_ref and share.minutes_reported == 12

    # The contractor sees it on the existing response page, records and approves, then orders.
    response_page = client.get(f"/projects/{project.id}/deck-takeoff/responses/{share.response_ref}")
    assert response_page.status_code == 200 and b"Ready to record" in response_page.data
    blocked = client.post(f"/projects/{project.id}/supplier-requests/{share.id}/order", follow_redirects=True)
    assert b"Record the supplier" in blocked.data and SupplierPurchaseOrder.query.count() == 0
    client.post(f"/projects/{project.id}/deck-takeoff/responses/{share.response_ref}/record", data={})
    lines, blockers = H.material_order_lines(share)
    assert blockers == ["Approve each line's cost first (on the returned response)."]
    from app.services.deck_takeoff import storage

    follow = next(r for r in storage.list_responses(DEFAULT_ORGANIZATION_ID, project.id)
                  if r.get("records_response") == share.response_ref)
    for result in follow["results"]:
        if result.get("recorded"):
            client.post(f"/projects/{project.id}/deck-takeoff/responses/{share.response_ref}/approve",
                        data={"canonical_material_id": result["canonical_material_id"], "status": "APPROVED"})
    placed = client.post(f"/projects/{project.id}/supplier-requests/{share.id}/order",
                         data={"delivery_date": (date.today() + timedelta(days=12)).isoformat(), "site_contact": "Ben"},
                         follow_redirects=True)
    assert b"It is agreed when they confirm it" in placed.data
    order = SupplierPurchaseOrder.query.one()
    assert order.status == "PLACED" and order.total == Decimal("9.00") * Decimal(str(lines[0]["quantity"]))

    # The order carries the site address; the supplier confirms it.
    order_page = supplier.get(f"/supplier/{account.supplier_id}/requests/{share.id}")
    assert b"Arcy" in order_page.data and b"Confirm order" in order_page.data
    supplier.post(f"/supplier/{account.supplier_id}/orders/{order.id}/confirm",
                  data={"action": "confirm", "expected_delivery": (date.today() + timedelta(days=12)).isoformat()})
    order = db.session.get(SupplierPurchaseOrder, order.id)
    assert order.status == "CONFIRMED" and order.supplier_responded_by_name == DARCY[0]
    events = [e.event_type for e in SupplierRequestEvent.query.filter_by(share_id=share.id).order_by(SupplierRequestEvent.id)]
    assert events == ["SENT", "OPENED", "RETURNED", "ORDER_PLACED", "ORDER_CONFIRMED"]

    figures = H.dashboard(account.supplier_id)
    assert figures["requests_received"] == 1 and figures["quotes_returned"] == 1
    assert figures["lines_recorded"] >= 1 and figures["costs_approved"] >= 1
    assert figures["orders_placed"] == 1 and figures["orders_confirmed"] == 1 and figures["average_minutes"] == 12
    assert supplier.get(f"/supplier/{account.supplier_id}/dashboard").status_code == 200


def test_another_supplier_cannot_see_the_request_and_a_withdrawn_one_disappears(app, client):
    project, _other, account = _setup()
    _give_sign_in(client, account)
    other_account = _tomlinson()
    _give_sign_in(client, other_account, name="Other Store Person", email="other.store@example.invalid")
    _pdf, fields, _keys = _issue(client, project, account)
    client.post(f"/projects/{project.id}/deck-takeoff/requests/{fields['request_id']['/V']}/send-to-supplier")
    share = SupplierRequestShare.query.one()
    other = _supplier_client(app, email="other.store@example.invalid")
    assert other.get(f"/supplier/{other_account.supplier_id}/requests/{share.id}").status_code == 404
    assert other.get(f"/supplier/{account.supplier_id}/").status_code == 404
    darcy = _supplier_client(app)
    client.post(f"/projects/{project.id}/supplier-requests/{share.id}/withdraw")
    assert darcy.get(f"/supplier/{account.supplier_id}/requests/{share.id}").status_code == 404
    assert share.number.encode() not in darcy.get(f"/supplier/{account.supplier_id}/").data


def test_concrete_is_its_own_request_to_its_own_supplier_and_is_ordered_and_confirmed(app, client):
    project, _other, bmr = _setup()
    tomlinson = _tomlinson()
    _give_sign_in(client, bmr)
    _give_sign_in(client, tomlinson)  # Darcy also handles Tomlinson concrete, in a separate area
    assert SupplierUserMembership.query.filter_by(user_id=User.query.filter_by(email=DARCY[1]).one().id).count() == 2
    delivery = (date.today() + timedelta(days=7)).isoformat()
    saved = client.post(f"/projects/{project.id}/concrete-requests", data={
        "volume_m3": "4.5", "strength_mpa": "32", "exposure_class": "C-2", "air_entrainment": "5–8%", "slump_mm": "100",
        "delivery_date": delivery, "delivery_window": "7:00–9:00", "placement": "Chute",
        "contractor_supplier_account_id": tomlinson.id,
    }, follow_redirects=True)
    assert b"sent to Tomlinson concrete (synthetic)" in saved.data
    share = SupplierRequestShare.query.one()
    assert share.request_kind == "CONCRETE" and share.supplier_id == tomlinson.supplier_id

    darcy = _supplier_client(app)
    areas = darcy.get("/supplier/")
    assert b"BMR Winchester (synthetic)" in areas.data and b"Tomlinson concrete (synthetic)" in areas.data
    assert share.number.encode() not in darcy.get(f"/supplier/{bmr.supplier_id}/").data  # never merged with BMR
    assert share.number.encode() in darcy.get(f"/supplier/{tomlinson.supplier_id}/").data
    assert darcy.get(f"/supplier/{bmr.supplier_id}/requests/{share.id}").status_code == 404

    darcy.post(f"/supplier/{tomlinson.supplier_id}/requests/{share.id}/quote", data={
        "quote_number": "TOM-1", "price_per_m3": "210.00", "short_load_charge": "75", "valid_until": delivery,
    })
    share = db.session.get(SupplierRequestShare, share.id)
    assert share.quote_json["concrete_value"] == "945.00" and share.quote_json["total_before_tax"] == "1020.00"
    blocked = client.post(f"/projects/{project.id}/supplier-requests/{share.id}/order", data={"site_contact": "Ben"},
                          follow_redirects=True)
    assert b"Approve the concrete quote first" in blocked.data and SupplierPurchaseOrder.query.count() == 0
    client.post(f"/projects/{project.id}/supplier-requests/{share.id}/approve-quote")  # demo step 5, separate from the order
    assert db.session.get(SupplierRequestShare, share.id).quote_json["approved_by"]
    client.post(f"/projects/{project.id}/supplier-requests/{share.id}/order", data={"site_contact": "Ben"})
    order = SupplierPurchaseOrder.query.one()
    assert order.total == Decimal("1020.00") and order.supplier_id == tomlinson.supplier_id
    problem = darcy.post(f"/supplier/{tomlinson.supplier_id}/orders/{order.id}/confirm",
                         data={"action": "problem", "note": ""}, follow_redirects=True)
    assert b"Describe the problem" in problem.data
    darcy.post(f"/supplier/{tomlinson.supplier_id}/orders/{order.id}/confirm", data={"action": "confirm"})
    assert db.session.get(SupplierPurchaseOrder, order.id).status == "CONFIRMED"
    office_page = client.get(f"/projects/{project.id}/supplier-requests")
    assert b"The order is agreed." in office_page.data
    assert H.dashboard(bmr.supplier_id)["requests_received"] == 0  # BMR figures never include concrete


def test_the_supplier_cannot_return_a_closed_request_or_change_identity(app, client):
    project, _other, account = _setup()
    _give_sign_in(client, account)
    _pdf, fields, keys = _issue(client, project, account)
    client.post(f"/projects/{project.id}/deck-takeoff/requests/{fields['request_id']['/V']}/send-to-supplier")
    share = SupplierRequestShare.query.one()
    darcy = _supplier_client(app)
    first = next(iter(keys.values()))
    values = {f"sku_{first}": "S", f"unit_cost_{first}": "5", f"discount_{first}": "0", "valid_until": VALID_UNTIL,
              "request_id": "DTR-FORGED", "request_project": "999"}
    darcy.post(f"/supplier/{account.supplier_id}/requests/{share.id}/quote", data=values)
    share = db.session.get(SupplierRequestShare, share.id)
    assert share.status == "RETURNED"  # the forged identity fields were ignored
    again = darcy.post(f"/supplier/{account.supplier_id}/requests/{share.id}/quote", data=values, follow_redirects=True)
    assert b"closed or already returned" in again.data


PNG = (b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
       b"\x00\x00\x00\rIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82")


def test_each_supplier_area_carries_that_suppliers_own_branding(app, client):
    from io import BytesIO

    _project, _other, bmr = _setup()
    tomlinson = _tomlinson()
    _give_sign_in(client, bmr)
    _give_sign_in(client, tomlinson)
    refused = client.post(f"/suppliers/{bmr.supplier_id}/branding", data={"primary_color": "blue"}, follow_redirects=True)
    assert b"The colour must look like" in refused.data
    bad = client.post(f"/suppliers/{bmr.supplier_id}/branding", data={"logo": (BytesIO(b"<svg onload=alert(1)>"), "x.svg")},
                      content_type="multipart/form-data", follow_redirects=True)
    assert b"must be a PNG, JPEG or WebP" in bad.data
    saved = client.post(f"/suppliers/{bmr.supplier_id}/branding",
                        data={"display_name": "BMR Winchester", "primary_color": "#e2231a", "logo": (BytesIO(PNG), "bmr.png")},
                        content_type="multipart/form-data", follow_redirects=True)
    assert b"Branding saved" in saved.data
    darcy = _supplier_client(app)
    page = darcy.get(f"/supplier/{bmr.supplier_id}/").get_data(as_text=True)
    assert "--supplier-brand: #E2231A" in page and f"/supplier/{bmr.supplier_id}/logo" in page
    assert 'class="supplier-location">Winchester<small>' in page  # the store location beside the supplier's logo
    assert "Powered by" in page
    logo = darcy.get(f"/supplier/{bmr.supplier_id}/logo")
    assert logo.data == PNG and logo.mimetype == "image/png" and logo.headers["X-Content-Type-Options"] == "nosniff"
    other = darcy.get(f"/supplier/{tomlinson.supplier_id}/").get_data(as_text=True)
    assert "#E2231A" not in other and "Tomlinson concrete (synthetic)<small>" in other  # its own area, not BMR's
    _give_sign_in(client, _third(), name="Third Store", email="third@example.invalid")
    third = _supplier_client(app, email="third@example.invalid")
    assert third.get(f"/supplier/{bmr.supplier_id}/logo").status_code == 404


def _third():
    supplier = create_supplier(code="TEST-THIRD", legal_name="Third supplier (synthetic)", demo_synthetic=True)
    location = create_supplier_location(supplier_id=supplier.id, code="MAIN", display_name="Third", demo_synthetic=True)
    return create_contractor_supplier_account(organization_id=DEFAULT_ORGANIZATION_ID, supplier_id=supplier.id,
                                              supplier_location_id=location.id, demo_synthetic=True)


def _concrete_order(app, client):
    project, _other, _bmr = _setup()
    tomlinson = _tomlinson()
    darcy_user = _give_sign_in(client, tomlinson)
    delivery = (date.today() + timedelta(days=7)).isoformat()
    client.post(f"/projects/{project.id}/concrete-requests", data={
        "volume_m3": "4.5", "strength_mpa": "32", "delivery_date": delivery, "placement": "Pump",
        "contractor_supplier_account_id": tomlinson.id})
    share = SupplierRequestShare.query.one()
    darcy = _supplier_client(app)
    darcy.post(f"/supplier/{tomlinson.supplier_id}/requests/{share.id}/quote",
               data={"price_per_m3": "210", "valid_until": delivery})
    client.post(f"/projects/{project.id}/supplier-requests/{share.id}/approve-quote")
    client.post(f"/projects/{project.id}/supplier-requests/{share.id}/order",
                data={"delivery_date": delivery, "delivery_window": "7:00–9:00"})
    order = SupplierPurchaseOrder.query.one()
    darcy.post(f"/supplier/{tomlinson.supplier_id}/orders/{order.id}/confirm", data={"action": "confirm",
               "expected_delivery": delivery, "delivery_window": "7:00–9:00"})
    return project, tomlinson, darcy, darcy_user, db.session.get(SupplierPurchaseOrder, order.id)


def test_a_weather_change_needs_the_other_sides_acceptance_and_is_texted(app, client):
    from app.models.supplier_portal import SupplierDeliveryChange, TextMessage
    from app.services.text_messages import save_contact
    from tests.auth_fixtures import ensure_office_user

    sent = []
    app.config["TEXT_TRANSPORT"] = lambda phone, body: sent.append((phone, body)) or f"SM{len(sent)}"
    project, tomlinson, darcy, darcy_user, order = _concrete_order(app, client)
    assert order.status == "CONFIRMED" and order.scheduled_window == "7:00–9:00"
    agreed = order.scheduled_date
    save_contact(darcy_user, mobile_phone="613-555-0101", opt_in=True)
    save_contact(ensure_office_user(), mobile_phone="(613) 555-0100", opt_in=True)
    darcy.post(f"/supplier/{tomlinson.supplier_id}/text-numbers", data={"name": "Yard dispatcher", "mobile_phone": "613-555-0102", "consent": "yes"})

    new_day = (agreed + timedelta(days=1)).isoformat()
    client.post(f"/projects/{project.id}/orders/{order.id}/delivery-change",
                data={"new_date": new_day, "new_window": "7:00–9:00", "reason": "Weather", "note": "Rain Thursday"})
    change = SupplierDeliveryChange.query.one()
    assert change.status == "PENDING"
    assert db.session.get(SupplierPurchaseOrder, order.id).scheduled_date == agreed  # nothing changes until accepted
    assert {p for p, _ in sent} >= {"+16135550101", "+16135550102"}  # Darcy and his staff number are texted
    assert any("Rain Thursday" in body and "/supplier/" in body for _, body in sent)
    again = client.post(f"/projects/{project.id}/orders/{order.id}/delivery-change",
                        data={"new_date": new_day, "reason": "Weather"}, follow_redirects=True)
    assert b"already waiting for an answer" in again.data
    # The contractor cannot accept its own request.
    client.post(f"/projects/{project.id}/delivery-changes/{change.id}/answer", data={"action": "accept"})
    assert db.session.get(SupplierDeliveryChange, change.id).status == "PENDING"
    inbox = darcy.get(f"/supplier/{tomlinson.supplier_id}/").get_data(as_text=True)
    assert "Delivery changes waiting for your answer" in inbox
    sent.clear()
    darcy.post(f"/supplier/{tomlinson.supplier_id}/delivery-changes/{change.id}/answer", data={"action": "accept"})
    order = db.session.get(SupplierPurchaseOrder, order.id)
    assert order.scheduled_date.isoformat() == new_day and db.session.get(SupplierDeliveryChange, change.id).status == "ACCEPTED"
    assert any(p == "+16135550100" and "accepted" in body for p, body in sent)  # Ben gets the acceptance by text
    assert TextMessage.query.filter_by(status="SENT").count() >= 3


def test_the_supplier_can_propose_another_time_and_decline_needs_a_reason(app, client):
    from app.models.supplier_portal import SupplierDeliveryChange

    project, tomlinson, darcy, _user, order = _concrete_order(app, client)
    first = (order.scheduled_date + timedelta(days=1)).isoformat()
    client.post(f"/projects/{project.id}/orders/{order.id}/delivery-change", data={"new_date": first, "new_window": "7:00–9:00", "reason": "Weather"})
    change = SupplierDeliveryChange.query.one()
    no_reason = darcy.post(f"/supplier/{tomlinson.supplier_id}/delivery-changes/{change.id}/answer", data={"action": "decline"}, follow_redirects=True)
    assert b"Say why" in no_reason.data
    darcy.post(f"/supplier/{tomlinson.supplier_id}/delivery-changes/{change.id}/answer",
               data={"action": "counter", "counter_date": first, "counter_window": "10:00–12:00", "counter_reason": "Supplier availability"})
    counter = SupplierDeliveryChange.query.filter_by(requested_by_side="SUPPLIER").one()
    assert db.session.get(SupplierDeliveryChange, change.id).status == "COUNTERED" and counter.counter_of_id == change.id
    page = client.get(f"/projects/{project.id}/supplier-requests").get_data(as_text=True)
    assert "Change requested by Darcy Synthetic" in page and "10:00–12:00" in page
    client.post(f"/projects/{project.id}/delivery-changes/{counter.id}/answer", data={"action": "accept"})
    order = db.session.get(SupplierPurchaseOrder, order.id)
    assert order.scheduled_window == "10:00–12:00"
    # Deliveries everywhere: the office list, the supplier list and the Company Calendar.
    assert order.number.encode() in client.get("/deliveries").data
    assert order.number.encode() in darcy.get(f"/supplier/{tomlinson.supplier_id}/deliveries").data
    cal = client.get(f"/schedule?scope=company&year={order.scheduled_date.year}&month={order.scheduled_date.month}&day={order.scheduled_date.day}").get_data(as_text=True)
    assert "Concrete · Tomlinson concrete (synthetic)" in cal and "data-calendar-deliveries" in cal


def test_texts_need_consent_and_wait_for_twilio_settings(app, client):
    from app.models.supplier_portal import TextMessage
    from app.services.text_messages import TextSettingsError, normalize_phone, save_contact, send_text_to_user
    from tests.auth_fixtures import ensure_office_user

    user = ensure_office_user()
    assert normalize_phone("613 555 0100") == "+16135550100"
    with pytest.raises(TextSettingsError):
        normalize_phone("12345")
    assert send_text_to_user(user, "hello") is None  # no consent, no text
    save_contact(user, mobile_phone="613-555-0100", opt_in=True)
    app.config["TESTING"] = False
    try:
        row = send_text_to_user(user, "hello")
    finally:
        app.config["TESTING"] = True
    assert row.status == "NOT_CONFIGURED" and row.error_code == "TWILIO_SETTINGS_MISSING"
    save_contact(user, mobile_phone="613-555-0100", opt_in=False)
    assert send_text_to_user(user, "hello") is None
    assert client.get("/account/text-messages").status_code == 200
    assert b"Text settings" in client.get("/account/text-messages").data


def test_moving_the_project_schedule_proposes_the_linked_delivery_to_the_supplier(app, client):
    """Joel, 17 Oct 2026: a schedule move is proposed to the supplier, who acknowledges it; nothing is imposed."""
    from app.models.supplier_portal import SupplierDeliveryChange
    from app.models.transactional_message import TEMPLATE_DELIVERY_SCHEDULE
    from app.services.schedule import create_schedule_item, shift_project_schedule
    from app.services.work_structure import add_project_element

    project, tomlinson, darcy, darcy_user, order = _concrete_order(app, client)
    agreed = order.scheduled_date
    element = add_project_element(project_id=project.id, display_name="Foundation pour",
                                  organization_id=project.organization_id)
    item = create_schedule_item(project_id=project.id, project_work_element_id=element.id, scheduled_start=agreed,
                                scheduled_end=agreed, organization_id=project.organization_id)
    order.schedule_item_id = item.id
    db.session.commit()
    before = TransactionalMessage.query.filter_by(template_id=TEMPLATE_DELIVERY_SCHEDULE, to_email=DARCY[1]).count()

    shift_project_schedule(project.id, days=2, organization_id=project.organization_id)

    change = SupplierDeliveryChange.query.one()
    assert change.status == "PENDING" and change.reason == "Project schedule change"
    assert change.new_date == agreed + timedelta(days=2) and change.new_window == "7:00–9:00"
    assert "Foundation pour" in change.note and "+2 days" in change.note
    assert db.session.get(SupplierPurchaseOrder, order.id).scheduled_date == agreed  # not imposed
    assert TransactionalMessage.query.filter_by(template_id=TEMPLATE_DELIVERY_SCHEDULE, to_email=DARCY[1]).count() == before + 1
    # Joel, 19 Oct 2026 (release blocker): a second move while our first request is waiting replaces it.
    # The supplier is never left answering a date the work no longer has.
    shift_project_schedule(project.id, days=1, organization_id=project.organization_id)
    first = db.session.get(SupplierDeliveryChange, change.id)
    assert first.status == "WITHDRAWN"
    fresh = SupplierDeliveryChange.query.filter_by(status="PENDING").one()
    assert fresh.new_date == agreed + timedelta(days=3) and fresh.new_window == "7:00–9:00"
    assert "replaces the earlier request" in fresh.note and "+1 day" in fresh.note
    assert db.session.get(SupplierPurchaseOrder, order.id).scheduled_date == agreed  # still not imposed
    assert TransactionalMessage.query.filter_by(template_id=TEMPLATE_DELIVERY_SCHEDULE, to_email=DARCY[1]).count() == before + 2
    # The old request can no longer be accepted; the fresh one can, and then delivery and work agree.
    darcy.post(f"/supplier/{tomlinson.supplier_id}/delivery-changes/{change.id}/answer", data={"action": "accept"})
    assert db.session.get(SupplierPurchaseOrder, order.id).scheduled_date == agreed
    darcy.post(f"/supplier/{tomlinson.supplier_id}/delivery-changes/{fresh.id}/answer", data={"action": "accept"})
    order = db.session.get(SupplierPurchaseOrder, order.id)
    assert order.scheduled_date == agreed + timedelta(days=3) == db.session.get(type(item), item.id).scheduled_start
    events = [e.event_type for e in SupplierRequestEvent.query.filter_by(share_id=order.share_id).order_by(SupplierRequestEvent.id)]
    assert events[-4:] == ["DELIVERY_CHANGE_REQUESTED", "DELIVERY_CHANGE_WITHDRAWN", "DELIVERY_CHANGE_REQUESTED", "DELIVERY_CHANGE_ACCEPTED"]


def _linked_pour(app, client):
    from app.services.schedule import create_schedule_item
    from app.services.work_structure import add_project_element

    project, tomlinson, darcy, darcy_user, order = _concrete_order(app, client)
    agreed = order.scheduled_date
    element = add_project_element(project_id=project.id, display_name="Foundation pour",
                                  organization_id=project.organization_id)
    item = create_schedule_item(project_id=project.id, project_work_element_id=element.id, scheduled_start=agreed,
                                scheduled_end=agreed, organization_id=project.organization_id)
    order.schedule_item_id = item.id
    db.session.commit()
    return project, tomlinson, darcy, order, item, agreed


def test_moving_the_work_back_withdraws_the_waiting_request_and_tells_the_supplier(app, client):
    from app.models.supplier_portal import SupplierDeliveryChange
    from app.models.transactional_message import TEMPLATE_DELIVERY_SCHEDULE
    from app.services.schedule import shift_project_schedule

    project, tomlinson, darcy, order, item, agreed = _linked_pour(app, client)
    shift_project_schedule(project.id, days=2, organization_id=project.organization_id)
    waiting = SupplierDeliveryChange.query.one()
    before = TransactionalMessage.query.filter_by(template_id=TEMPLATE_DELIVERY_SCHEDULE, to_email=DARCY[1]).count()
    shift_project_schedule(project.id, days=-2, organization_id=project.organization_id)  # back on the agreed day
    assert db.session.get(SupplierDeliveryChange, waiting.id).status == "WITHDRAWN"
    assert SupplierDeliveryChange.query.filter_by(status="PENDING").count() == 0
    assert db.session.get(SupplierPurchaseOrder, order.id).scheduled_date == agreed
    assert TransactionalMessage.query.filter_by(template_id=TEMPLATE_DELIVERY_SCHEDULE, to_email=DARCY[1]).count() == before + 1
    assert SupplierRequestEvent.query.filter_by(event_type="DELIVERY_CHANGE_WITHDRAWN").count() == 1


def test_a_suppliers_own_waiting_change_is_left_for_the_office_to_answer_and_the_office_is_told(app, client):
    from app.models.supplier_portal import SupplierDeliveryChange

    project, tomlinson, darcy, order, item, agreed = _linked_pour(app, client)
    darcy.post(f"/supplier/{tomlinson.supplier_id}/orders/{order.id}/delivery-change",
               data={"new_date": (agreed + timedelta(days=1)).isoformat(), "new_window": "8:00–10:00", "reason": "Weather"})
    theirs = SupplierDeliveryChange.query.filter_by(requested_by_side="SUPPLIER", status="PENDING").one()
    page = client.post(f"/schedule/projects/{project.id}/shift", data={"days": "3"}, follow_redirects=True).get_data(as_text=True)
    assert db.session.get(SupplierDeliveryChange, theirs.id).status == "PENDING"  # theirs is not answered for them
    assert SupplierDeliveryChange.query.count() == 1
    assert "waiting for your answer" in page and order.number in page
    assert db.session.get(SupplierPurchaseOrder, order.id).scheduled_date == agreed
    assert SupplierRequestEvent.query.filter_by(event_type="SCHEDULE_MOVED_CHANGE_PENDING").count() == 1


def test_delivery_notices_email_the_right_people_and_texts_stay_not_sent_until_twilio_is_configured(app, client):
    from app.models.supplier_portal import SupplierDeliveryChange, TextMessage
    from app.models.transactional_message import TEMPLATE_DELIVERY_SCHEDULE
    from app.services.text_messages import save_contact
    from tests.auth_fixtures import DEFAULT_OFFICE_EMAIL

    project, tomlinson, darcy, darcy_user, order = _concrete_order(app, client)
    save_contact(darcy_user, mobile_phone="613-555-0101", opt_in=True)
    other = _give_sign_in(client, _bmr_account_of(project), name="BMR only", email="bmr.only@example.invalid")
    sent = TransactionalMessage.query.filter_by(template_id=TEMPLATE_DELIVERY_SCHEDULE)
    assert {m.to_email for m in sent} >= {DARCY[1], DEFAULT_OFFICE_EMAIL}  # order to Darcy, confirmation to Ben
    app.config["TESTING"] = False  # production behaviour without Twilio settings
    try:
        client.post(f"/projects/{project.id}/orders/{order.id}/delivery-change",
                    data={"new_date": (order.scheduled_date + timedelta(days=1)).isoformat(), "reason": "Weather"})
    finally:
        app.config["TESTING"] = True
    texts = TextMessage.query.filter_by(to_phone="+16135550101").all()
    assert texts and all(t.status == "NOT_CONFIGURED" and t.error_code == "TWILIO_SETTINGS_MISSING" for t in texts)
    assert SupplierDeliveryChange.query.one().status == "PENDING"  # the change is recorded although no text went out
    assert not TransactionalMessage.query.filter_by(template_id=TEMPLATE_DELIVERY_SCHEDULE, to_email=other.email).count()


def _bmr_account_of(project):
    return ContractorSupplierAccount.query.join(
        ContractorSupplierAccount.supplier).filter_by(code="TEST-BMR").one()


def test_one_contractors_requests_orders_and_deliveries_are_invisible_to_another_contractor(app, client):
    from app.models import Client, Organization, Project
    from app.models.user import UserMembership
    from tests.auth_fixtures import create_user

    project, tomlinson, darcy, _user, order = _concrete_order(app, client)
    other_org = Organization(id="ORG-SYN-2", legal_name="Other Contractor Inc. (synthetic)", display_name="Other Contractor")
    db.session.add(other_org); db.session.commit()
    outsider = create_user(email="outsider@example.invalid", password="Synthetic-other-1", display_name="Other Office")
    db.session.add(UserMembership(user_id=outsider.id, organization_id=other_org.id, is_active=True)); db.session.commit()
    owner = Client(name="Other client", organization_id=other_org.id); db.session.add(owner); db.session.flush()
    theirs = Project(name="Other contractor job", client_id=owner.id, organization_id=other_org.id, status="Estimating")
    db.session.add(theirs); db.session.commit()
    other = app.test_client()
    assert other.post("/login", data={"email": "outsider@example.invalid", "password": "Synthetic-other-1"}).status_code == 302
    assert other.get(f"/projects/{project.id}/supplier-requests").status_code == 404
    assert order.number.encode() not in other.get("/deliveries").data
    assert other.post(f"/projects/{project.id}/orders/{order.id}/delivery-change",
                      data={"new_date": "2030-01-01", "reason": "Weather"}).status_code == 404
    assert other.post(f"/projects/{theirs.id}/orders/{order.id}/delivery-change",
                      data={"new_date": "2030-01-01", "reason": "Weather"}).status_code == 404
    assert b"Tomlinson concrete (synthetic)" not in other.get("/suppliers").data  # the account belongs to the first contractor
    assert other.post(f"/suppliers/{tomlinson.supplier_id}/users", data={"display_name": "x", "email": "x@example.invalid"}).status_code == 404


def test_supplier_pages_never_show_selling_prices_or_margins(app, client):
    from app.services.estimates import create_estimate
    from app.services.estimate_builder import add_manual_line, create_section
    from tests.proposal_issue_support import approve_for_issue

    project, tomlinson, darcy, _user, order = _concrete_order(app, client)
    estimate = create_estimate(project_id=project.id, estimate_number="EST-MARGIN-1", title="Deck",
                               organization_id=DEFAULT_ORGANIZATION_ID)
    section = create_section(estimate.current_version, name="Work")
    add_manual_line(section, line_type="Custom", description="Composite decking", quantity=100, unit="SF", unit_cost=13.37)
    approve_for_issue(estimate.current_version)
    pricing = estimate.current_version.pricing_snapshot
    secret_values = {f"{pricing.customer_total:.2f}", f"{pricing.pre_tax_selling_price:.2f}", "1337.00", "13.37"}
    pages = [darcy.get(u).get_data(as_text=True) for u in (
        "/supplier/", f"/supplier/{tomlinson.supplier_id}/", f"/supplier/{tomlinson.supplier_id}/dashboard",
        f"/supplier/{tomlinson.supplier_id}/deliveries", f"/supplier/{tomlinson.supplier_id}/requests/{order.share_id}")]
    for page in pages:
        for value in secret_values:
            assert value not in page and f"{float(value):,.2f}" not in page
        for word in ("margin", "markup", "selling price", "customer total", "EST-MARGIN-1"):
            assert word.lower() not in page.lower().replace("contractor margins, labour rates or internal costs", "")


def test_supplier_sign_in_has_show_password_and_a_reset_that_returns_to_the_supplier_page(app, client):
    _project, _other, account = _setup()
    _give_sign_in(client, account)
    page = app.test_client().get("/supplier/login").data.decode()
    assert 'name="password"' in page and "data-password-reveal" in page and "js/password-reveal.js" in page
    assert '/forgot-password?portal=supplier' in page
    office = app.test_client().get("/login").data.decode()
    assert "data-password-reveal" in office and "js/password-reveal.js" in office  # same treatment both pages
    forgot = app.test_client().get("/forgot-password?portal=supplier").data.decode()
    assert 'name="portal" value="supplier"' in forgot and 'href="/supplier/login"' in forgot
    before = TransactionalMessage.query.filter_by(to_email=DARCY[1]).count()
    sent = app.test_client().post("/forgot-password", data={"email": DARCY[1], "portal": "supplier"})
    assert sent.status_code == 302 and sent.headers["Location"].endswith("/forgot-password/sent?portal=supplier")
    assert TransactionalMessage.query.filter_by(to_email=DARCY[1]).count() == before + 1  # reset link to Darcy
    assert 'href="/supplier/login"' in app.test_client().get(sent.headers["Location"]).data.decode()
    # Without the supplier hint the office pages keep their own link.
    assert 'href="/login"' in app.test_client().get("/forgot-password").data.decode()


# ------------------------------------------------------------------ owner review B–D (17 Oct 2026)


def _material_round(app, client, project, account, *, sku="TEST-SKU-1", minutes="12"):
    """Send a deck request to BMR, Darcy prices the first line, Ben records, approves and orders."""
    from app.services.deck_takeoff import storage

    _pdf, fields, keys = _issue(client, project, account)
    request_id = fields["request_id"]["/V"]
    client.post(f"/projects/{project.id}/deck-takeoff/requests/{request_id}/send-to-supplier",
                data={"needed_by": (date.today() + timedelta(days=10)).isoformat()})
    share = SupplierRequestShare.query.filter_by(source_ref=request_id).one()
    supplier = _supplier_client(app)
    first = next(iter(keys.values()))
    supplier.post(f"/supplier/{account.supplier_id}/requests/{share.id}/quote", data={
        f"sku_{first}": sku, f"unit_cost_{first}": "10.00", f"discount_{first}": "10", "bmr_contact": DARCY[0],
        "response_date": RESPONSE_DATE, "valid_until": VALID_UNTIL, "minutes_reported": minutes})
    share = db.session.get(SupplierRequestShare, share.id)
    client.post(f"/projects/{project.id}/deck-takeoff/responses/{share.response_ref}/record", data={})
    follow = next(r for r in storage.list_responses(DEFAULT_ORGANIZATION_ID, project.id)
                  if r.get("records_response") == share.response_ref)
    for result in follow["results"]:
        if result.get("recorded"):
            client.post(f"/projects/{project.id}/deck-takeoff/responses/{share.response_ref}/approve",
                        data={"canonical_material_id": result["canonical_material_id"], "status": "APPROVED"})
    client.post(f"/projects/{project.id}/supplier-requests/{share.id}/order",
                data={"delivery_date": (date.today() + timedelta(days=5)).isoformat(), "site_contact": "Ben"})
    return supplier, share, keys, first


def test_needs_attention_lists_what_waits_for_the_store_and_period_figures_use_actual_records(app, client):
    from app.services import supplier_insights as I

    project, tomlinson, darcy, _user, order = _concrete_order(app, client)
    # A second concrete request is waiting for a quote; the first is ordered and confirmed for next week.
    client.post(f"/projects/{project.id}/concrete-requests", data={
        "volume_m3": "2", "strength_mpa": "25", "delivery_date": (date.today() + timedelta(days=20)).isoformat(),
        "placement": "Chute", "contractor_supplier_account_id": tomlinson.id})
    waiting = SupplierRequestShare.query.filter_by(status="SENT").one()
    attention = I.attention(tomlinson.supplier_id)
    assert attention["quotes_count"] == 1 and attention["quotes"][0].id == waiting.id
    assert attention["orders_count"] == 0 and attention["changes_count"] == 0
    assert attention["upcoming_count"] == 1 and attention["upcoming"][0]["order"].id == order.id
    client.post(f"/projects/{project.id}/orders/{order.id}/delivery-change",
                data={"new_date": (order.scheduled_date + timedelta(days=1)).isoformat(), "reason": "Weather"})
    inbox = darcy.get(f"/supplier/{tomlinson.supplier_id}/").get_data(as_text=True)
    assert 'data-attention-quotes="1"' in inbox and 'data-attention-changes="1"' in inbox
    assert 'data-attention-upcoming="1"' in inbox and waiting.number in inbox
    assert 'data-changes-waiting="1"' in inbox  # the accepted delivery-change banner is still there

    week = I.period_figures(tomlinson.supplier_id, I.resolve_period("week"))
    assert week["quotes_received"] == 2 and week["quotes_returned"] == 1 and week["quotes_ordered"] == 1
    assert week["conversion_percent"] is None  # fewer than five returned quotes: shown as "1 of 1"
    assert week["orders_placed"] == 1 and week["orders_confirmed"] == 1
    assert week["average_order_value"] == Decimal("945.00") and week["ordered_value"] == Decimal("945.00")
    past = I.resolve_period("custom", "2020-01-01", "2020-01-31")
    assert past.key == "custom"
    empty = I.period_figures(tomlinson.supplier_id, past)
    assert empty["quotes_received"] == empty["orders_placed"] == 0 and empty["average_order_value"] is None
    assert I.resolve_period("custom", "2020-02-01", "2020-01-01").key == I.DEFAULT_PERIOD  # unusable dates

    page = darcy.get(f"/supplier/{tomlinson.supplier_id}/dashboard?period=week").get_data(as_text=True)
    assert 'data-period-figures="week"' in page and "1 of 1" in page and "$945.00" in page
    assert "Purchase orders, not invoiced sales." in page and "data-supplier-dashboard" in page
    custom = darcy.get(f"/supplier/{tomlinson.supplier_id}/dashboard?period=custom&from=2020-01-01&to=2020-01-31")
    assert custom.status_code == 200 and "No orders placed in this period." in custom.get_data(as_text=True)
    for word in ("margin", "markup", "selling price"):
        assert word not in page.lower().replace("contractor margins, labour rates or internal costs", "")


def test_quote_to_order_conversion_shows_a_percentage_from_five_returned_quotes(app, client):
    from app.services import supplier_insights as I

    project, tomlinson, darcy, _user, _order = _concrete_order(app, client)
    for n in range(4):
        client.post(f"/projects/{project.id}/concrete-requests", data={
            "volume_m3": "1", "strength_mpa": str(20 + n), "delivery_date": (date.today() + timedelta(days=30)).isoformat(),
            "placement": "Chute", "contractor_supplier_account_id": tomlinson.id})
        share = SupplierRequestShare.query.filter_by(status="SENT").one()
        darcy.post(f"/supplier/{tomlinson.supplier_id}/requests/{share.id}/quote",
                   data={"price_per_m3": "200", "valid_until": (date.today() + timedelta(days=30)).isoformat(),
                         "minutes_reported": "6"})
    figures = I.period_figures(tomlinson.supplier_id, I.resolve_period("90d"))
    assert figures["quotes_returned"] == 5 and figures["quotes_ordered"] == 1 and figures["conversion_percent"] == 20
    assert figures["quotes_with_minutes"] == 4 and figures["average_minutes"] == 6
    assert figures["hours_recorded"] == Decimal("0.4")


def test_material_demand_adds_up_requests_to_this_store_only_without_naming_contractors_or_jobs(app, client):
    from app.services import supplier_insights as I

    project, other, account = _setup()
    _give_sign_in(client, account)
    supplier, share, keys, first = _material_round(app, client, project, account)
    demand = I.material_demand(account.supplier_id, I.resolve_period("90d"))
    assert demand["requests"] == 1 and demand["contractors"] == 1
    rows = [r for c in demand["categories"] for r in c["rows"]]
    assert rows and sum(r["quoted"] for r in rows) == 1
    priced = next(r for r in rows if r["quoted"] == 1)
    assert priced["confirmed_sku"] and priced["ordered_lines"] == 1
    # Every other line came back without a price (a product can sit on two lines of one request).
    assert all(r["not_priced"] >= 1 and r["quoted"] == 0 and r["requests"] == 1 for r in rows if r is not priced)
    assert not demand["possible_gaps"]  # one request is never called a gap

    # A second request for another job: the same products now recur; still only this store's requests.
    supplier2, share2, _keys, _first = _material_round(app, client, other, account)
    demand = I.material_demand(account.supplier_id, I.resolve_period("90d"))
    rows = [r for c in demand["categories"] for r in c["rows"]]
    assert demand["requests"] == 2 and all(r["requests"] == 2 for r in rows)
    assert demand["possible_gaps"] and all(g["quoted"] == 0 and g["unpriced_requests"] == 2 for g in demand["possible_gaps"])
    assert all("E+" not in r["quantity"] for r in rows)  # plain numbers, never scientific notation

    page = supplier.get(f"/supplier/{account.supplier_id}/demand?period=90d").get_data(as_text=True)
    assert "data-demand-requests" in page and "Possible assortment gaps" in page and "Recurring" in page
    for private in (project.name, other.name, "Arcy", "Brayman Construction", "TEST-SKU-1-COST"):
        assert private not in page
    assert "Requested is not purchased" in page and "Neither shows whether a contractor bought it elsewhere" in page
    for word in ("margin", "markup", "selling price"):
        assert word not in page.lower()

    # Another supplier sees none of it, and cannot open BMR's demand page.
    tomlinson = _tomlinson()
    assert I.material_demand(tomlinson.supplier_id, I.resolve_period("all"))["requests"] == 0
    assert supplier.get(f"/supplier/{tomlinson.supplier_id}/demand").status_code == 404


def test_a_confirmed_sku_is_suggested_on_the_next_request_and_staff_can_change_it(app, client):
    from app.services import supplier_insights as I

    project, other, account = _setup()
    _give_sign_in(client, account)
    supplier, _share, keys, first = _material_round(app, client, project, account, sku="BMR-2X12-08")
    # Next request (another job) for the same products: the SKU confirmed when Ben recorded the quote is filled in.
    _pdf, fields, keys2 = _issue(client, other, account)
    request_id = fields["request_id"]["/V"]
    client.post(f"/projects/{other.id}/deck-takeoff/requests/{request_id}/send-to-supplier", data={})
    share = SupplierRequestShare.query.filter_by(source_ref=request_id).one()
    remembered = I.remembered_skus(share)
    assert remembered and {v["sku"] for v in remembered.values()} == {"BMR-2X12-08"}
    page = supplier.get(f"/supplier/{account.supplier_id}/requests/{share.id}").get_data(as_text=True)
    assert 'data-sku-suggested="BMR-2X12-08"' in page and "Your confirmed SKU — check it" in page
    assert "Prices and discounts are never filled in" in page
    # Never a price or discount: those inputs stay empty.
    import re
    for name in re.findall(r'name="(unit_cost_\d+|discount_\d+)"[^>]*>', page):
        assert re.search(rf'name="{name}"[^>]*value="[^"]+"', page) is None
    # Staff correct the suggestion: the typed SKU is what goes back.
    n = next(iter(f"{k:02d}" for k in remembered))
    supplier.post(f"/supplier/{account.supplier_id}/requests/{share.id}/quote", data={
        f"sku_{n}": "BMR-2X12-08-NEW", f"unit_cost_{n}": "11.00", f"discount_{n}": "0", "bmr_contact": DARCY[0],
        "response_date": RESPONSE_DATE, "valid_until": VALID_UNTIL})
    from app.services.deck_takeoff import storage

    share = db.session.get(SupplierRequestShare, share.id)
    record = storage.load_response(DEFAULT_ORGANIZATION_ID, other.id, share.response_ref)
    row = next(r for r in record["rows"] if int(r["number"]) == int(n))
    assert row["answers"]["sku"] == "BMR-2X12-08-NEW"
    assert I.remembered_skus(share) == {}  # a returned request is closed: no suggestions
    # Another supplier never gets BMR's SKUs.
    from app.models.supplier_catalogue import SupplierProduct

    assert {p.supplier_id for p in SupplierProduct.query.filter(SupplierProduct.sku.like("BMR-%"))} == {account.supplier_id}


def test_after_an_accepted_change_every_screen_shows_the_agreed_delivery(app, client):
    """Joel, 19 Oct 2026 (sync review G3): no screen shows an earlier date as the current delivery.

    The first requested date stays visible as the requested date; the agreed date is shown as agreed;
    a waiting change is shown as waiting; nothing changes before the other side agrees.
    """
    from app.models.supplier_portal import ConcreteRequest
    from app.services.cal_find import DEST_QUOTES, DEST_DELIVERIES, records_for_project
    from app.services.supplier_hub import request_delivery_change
    from tests.auth_fixtures import ensure_office_user

    project, tomlinson, darcy, darcy_user, order = _concrete_order(app, client)
    first = order.scheduled_date
    moved = first + timedelta(days=3)
    concrete = ConcreteRequest.query.one()
    change = request_delivery_change(order, side="CONTRACTOR", user=ensure_office_user(), new_date=moved,
                                     new_window="7:00–9:00", reason="Site not ready")
    # Waiting: still the first date everywhere, with the change shown as waiting.
    office = client.get(f"/projects/{project.id}/supplier-requests").get_data(as_text=True)
    assert f'data-concrete-current="{first.isoformat()}"' in office and f"change waiting → {moved.isoformat()}" in office
    with app.test_request_context():
        quotes = [i.detail for i in records_for_project(DEST_QUOTES, project, project.organization_id)]
    assert any("change waiting" in d for d in quotes)
    darcy.post(f"/supplier/{tomlinson.supplier_id}/delivery-changes/{change.id}/answer", data={"action": "accept"})
    order = db.session.get(SupplierPurchaseOrder, order.id)
    assert order.scheduled_date == moved and order.expected_delivery == moved
    # Supplier's own page: the order and the concrete details agree; the request date is labelled as requested.
    page = darcy.get(f"/supplier/{tomlinson.supplier_id}/requests/{order.share_id}").get_data(as_text=True)
    assert f'data-order-delivery="{moved.isoformat()}"' in page
    assert f"Expected delivery {first.isoformat()}" not in page
    assert "Requested delivery" in page and f'data-concrete-agreed="{moved.isoformat()}"' in page
    # Office page: confirmed line and concrete list both show the agreed date; the request date stays labelled.
    office = client.get(f"/projects/{project.id}/supplier-requests").get_data(as_text=True)
    assert f"agreed delivery {moved.isoformat()}" in office and f"delivery {first.isoformat()}. The order is agreed" not in office
    assert f'data-concrete-current="{moved.isoformat()}"' in office and f"requested delivery {first.isoformat()}" in office
    # Cal: the concrete request and the delivery both give the agreed date.
    with app.test_request_context():
        quotes = [i.detail for i in records_for_project(DEST_QUOTES, project, project.organization_id)]
        deliveries = [i.detail for i in records_for_project(DEST_DELIVERIES, project, project.organization_id)]
    assert any(f"agreed {moved.strftime('%a %d %b %Y')}" in d for d in quotes)
    assert not any(first.strftime("%a %d %b %Y") in d for d in quotes)
    assert deliveries and all(moved.strftime("%a %d %b %Y") in d for d in deliveries)
    # Calendar: the delivery is on the agreed day.
    cal = client.get(f"/schedule?scope=company&year={moved.year}&month={moved.month}&day={moved.day}&view=day").get_data(as_text=True)
    assert "Tomlinson concrete (synthetic)" in cal
    # The earlier dates stay in the history.
    assert change.previous_date == first and db.session.get(type(change), change.id).status == "ACCEPTED"


def test_the_project_page_links_to_its_supplier_requests_and_lists_its_purchase_orders(app, client):
    """Job lifecycle walk (20 Oct 2026): a job without a deck takeoff had no way from the Project page to
    its concrete request or orders, and a placed PO never showed on the Project page."""
    from app.models import Project

    project, tomlinson, _darcy, _user, order = _concrete_order(app, client)
    other = Project.query.filter_by(name="Another synthetic deck").one()
    empty = client.get(f"/projects/{other.id}").get_data(as_text=True)
    assert f'href="/projects/{other.id}/supplier-requests">Supplier requests, concrete and orders</a>' in empty
    assert "No purchase orders yet." in empty, empty.split("hub-purchasing")[1][:600]
    assert f"data-hub-po=\"{order.number}\"" not in empty
    page = client.get(f"/projects/{project.id}").get_data(as_text=True)
    row = page.split(f'data-hub-po="{order.number}"', 1)[1].split("</tr>", 1)[0]
    assert f"#share-{order.share_id}" in row and "Tomlinson concrete (synthetic) · concrete" in row
    assert "$945.00" in row and "Confirmed" in row and order.scheduled_date.isoformat() in row
    assert "(requested)" not in row  # the supplier confirmed it, so the date is agreed


def test_the_quote_form_and_order_lines_become_cards_on_a_phone(app, client):
    """Supplier Hub walk, 20 Oct 2026: at 390 px the price boxes sat off screen inside the table. The quote
    lines, the order lines, the inbox and deliveries use the same phone card layout as the PRO Desk."""
    project, _other, account = _setup()
    _give_sign_in(client, account)
    _pdf, fields, _keys = _issue(client, project, account)
    client.post(f"/projects/{project.id}/deck-takeoff/requests/{fields['request_id']['/V']}/send-to-supplier")
    share = SupplierRequestShare.query.one()
    darcy = _supplier_client(app)
    page = darcy.get(f"/supplier/{account.supplier_id}/requests/{share.id}").get_data(as_text=True)
    assert 'class="data-table pd-stack" data-quote-lines="true"' in page
    assert page.count('data-label="Unit cost"') == len(share.shared_json["lines"])
    assert page.count('data-label="Discount %"') == len(share.shared_json["lines"])
    assert 'aria-label="Unit cost, line 1"' in page
    inbox = darcy.get(f"/supplier/{account.supplier_id}/").get_data(as_text=True)
    assert 'class="data-table pd-stack"' in inbox and 'data-label="Status"' in inbox
    css = (Path(app.root_path) / "static/css/supplier-hub.css").read_text()
    assert ".pd-stack td[data-label]::before" in css
