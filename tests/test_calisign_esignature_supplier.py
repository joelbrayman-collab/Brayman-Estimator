"""CaliSIGN native e-signature, supplier side (Joel's brief, 28 Oct 2026, section 26).

The FG-041 supplier signing is the functional authority: the contractor signs on Place order, the store signs in
the Supplier Hub while signed in, every agreed delivery change is signed by both sides, declining needs no
signature. CaliSIGN adds the launch wording, the adopt-signature preview, the status chips and the supplier
invitation email. Brief numbers covered here: 3, 6, 20, 28 (supplier), 32, 33. Synthetic suppliers only.
"""

from __future__ import annotations

from datetime import date, timedelta

from app import db
from app.models.signing import SigningRequest
from app.models.supplier_portal import SupplierDeliveryChange, SupplierPurchaseOrder, SupplierRequestShare
from app.models.transactional_message import TransactionalMessage
from app.services import calisign as C
from app.services import supplier_signing as SS
from tests.test_deck_takeoff_workflow import app, client  # noqa: F401
from tests.test_supplier_hub import DARCY, _fresh_login_per_request, _give_sign_in, _setup, _supplier_client, _tomlinson  # noqa: F401
from tests.test_supplier_native_signing import BEN, STORE, _confirmed, _placed_concrete

INVITE = "SIGNING_SUPPLIER_INVITATION"


def _chips(html: bytes) -> list[str]:
    import re

    return re.findall(r'data-calisign-status="([^"]*)"', html.decode("utf-8"))


def test_03_an_approved_quote_offers_sign_and_send_for_e_signature_and_an_unapproved_one_does_not(app, client):
    project, _other, _bmr = _setup()
    tomlinson = _tomlinson()
    _give_sign_in(client, tomlinson)
    delivery = (date.today() + timedelta(days=7)).isoformat()
    client.post(f"/projects/{project.id}/concrete-requests", data={
        "volume_m3": "4.5", "strength_mpa": "32", "delivery_date": delivery, "placement": "Pump",
        "contractor_supplier_account_id": tomlinson.id})
    share = SupplierRequestShare.query.one()
    before = client.get(f"/projects/{project.id}/supplier-requests").data
    assert b"data-calisign-po-send" not in before, "nothing to sign before a quote is approved"
    store = _supplier_client(app)
    store.post(f"/supplier/{tomlinson.supplier_id}/requests/{share.id}/quote", data={"price_per_m3": "210", "valid_until": delivery})
    client.post(f"/projects/{project.id}/supplier-requests/{share.id}/approve-quote")
    page = client.get(f"/projects/{project.id}/supplier-requests").data
    assert b"data-calisign-po-send" in page and b"Sign &amp; Send for E-Signature" in page
    assert b"data-calisign-po-note" in page and b"Supplier Hub" in page
    assert b"This is how your name will appear as your electronic signature." in page
    assert b'data-calisign-preview' in page and b'name="sign_consent" value="yes">' in page, "consent not preselected"


def test_06_the_store_receives_a_calisign_invitation_for_this_purchase_order(app, client):
    project, tomlinson, _store, share, _delivery = _placed_concrete(app, client)
    order = SupplierPurchaseOrder.query.one()
    invites = TransactionalMessage.query.filter_by(template_id=INVITE).all()
    assert [m.to_email for m in invites] == [DARCY[1]], "only the store's signed-in user is invited"
    assert SS.order_signing(order).status == "SENT"
    page = client.get(f"/projects/{project.id}/supplier-requests").data
    assert "Awaiting Signature" in _chips(page)


def test_20_28_the_store_signs_in_the_hub_and_both_sides_show_executed(app, client):
    project, tomlinson, store, share, delivery = _placed_concrete(app, client)
    order = SupplierPurchaseOrder.query.one()
    hub = store.get(f"/supplier/{tomlinson.supplier_id}/requests/{share.id}").data
    assert "Awaiting Your Signature" in _chips(hub) and b"Sign &amp; Confirm Order" in hub
    unsigned = store.post(f"/supplier/{tomlinson.supplier_id}/orders/{order.id}/confirm",
                          data={"action": "confirm", "expected_delivery": delivery}, follow_redirects=True)
    assert b"To sign," in unsigned.data and SS.order_signing(order).status == "SENT"
    store.post(f"/supplier/{tomlinson.supplier_id}/orders/{order.id}/confirm",
               data={**STORE, "action": "confirm", "expected_delivery": delivery, "delivery_window": "7:00–9:00"})
    request = SS.order_signing(db.session.get(SupplierPurchaseOrder, order.id))
    assert request.status == "EXECUTED"
    assert "Executed" in _chips(store.get(f"/supplier/{tomlinson.supplier_id}/requests/{share.id}").data)
    office = client.get(f"/projects/{project.id}/supplier-requests").data
    assert "Executed" in _chips(office) and b"signed by Ben Contractor" in office and b"signed by Pro Desk Person" in office
    summary = SS.signing_summary(request)
    assert C.supplier_status(summary, our_side="CONTRACTOR").label == C.EXECUTED


def test_32_a_reported_problem_and_a_declined_change_need_no_signature(app, client):
    project, tomlinson, store, share, delivery = _placed_concrete(app, client)
    order = SupplierPurchaseOrder.query.one()
    store.post(f"/supplier/{tomlinson.supplier_id}/orders/{order.id}/confirm", data={"action": "problem", "note": "Out of stock"})
    assert db.session.get(SupplierPurchaseOrder, order.id).status == "PROBLEM"
    assert SS.order_signing(order).status == "VOIDED"


def test_32_33_delivery_change_signed_by_both_sides_decline_unsigned_withdraw_voids(app, client):
    project, tomlinson, store, order = _confirmed(app, client)
    day = (order.scheduled_date + timedelta(days=1)).isoformat()
    client.post(f"/projects/{project.id}/orders/{order.id}/delivery-change", data={**BEN, "new_date": day, "reason": "Weather"})
    first = SupplierDeliveryChange.query.one()
    assert TransactionalMessage.query.filter_by(template_id=INVITE).count() == 2, "order, then the change"
    hub = store.get(f"/supplier/{tomlinson.supplier_id}/requests/{order.share_id}").data
    assert "Awaiting Your Signature" in _chips(hub) and b"Sign &amp; Accept" in hub
    store.post(f"/supplier/{tomlinson.supplier_id}/delivery-changes/{first.id}/answer", data={"action": "decline", "note": "No trucks"})
    assert db.session.get(SupplierDeliveryChange, first.id).status == "DECLINED"
    assert SS.change_signing(first).status == "VOIDED"

    client.post(f"/projects/{project.id}/orders/{order.id}/delivery-change", data={**BEN, "new_date": day, "reason": "Weather"})
    second = SupplierDeliveryChange.query.filter_by(status="PENDING").one()
    client.post(f"/projects/{project.id}/delivery-changes/{second.id}/withdraw")
    assert SS.change_signing(db.session.get(SupplierDeliveryChange, second.id)).status == "VOIDED"

    client.post(f"/projects/{project.id}/orders/{order.id}/delivery-change", data={**BEN, "new_date": day, "reason": "Weather"})
    third = SupplierDeliveryChange.query.filter_by(status="PENDING").one()
    store.post(f"/supplier/{tomlinson.supplier_id}/delivery-changes/{third.id}/answer", data={**STORE, "action": "accept"})
    request = SS.change_signing(db.session.get(SupplierDeliveryChange, third.id))
    assert request.status == "EXECUTED"
    assert SigningRequest.query.filter_by(document_family="SUPPLIER_DELIVERY_CHANGE").count() == 3, "one request per change"
    office = client.get(f"/projects/{project.id}/supplier-requests").data
    assert f'data-signed-change="{third.id}"'.encode() in office
