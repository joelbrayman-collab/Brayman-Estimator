"""Supplier Hub (Joel, 17 Oct 2026; ADR-047). Synthetic data only.

Separate supplier sign-in, isolation both ways, send one request to one supplier,
the supplier returns prices through the same reconciliation, the contractor records
and approves, places the order, and the supplier confirms it. Concrete is its own
request to its own supplier account, kept apart from material requests.
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

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
    cal = client.get(f"/schedule?year={order.scheduled_date.year}&month={order.scheduled_date.month}&day={order.scheduled_date.day}").get_data(as_text=True)
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
