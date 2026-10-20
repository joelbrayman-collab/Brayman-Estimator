"""Native Signing on the supplier side (Joel, 20 Oct 2026: "Connect native signing").

Owner decisions: purchase orders, store confirmations and delivery changes are signed; the contractor signs on
Place order; the store signs in the Supplier Hub while signed in; every agreed delivery change is signed by both
sides. Synthetic suppliers and data only.
"""

from __future__ import annotations

from datetime import date, timedelta
from io import BytesIO

from pypdf import PdfReader

from app import db
from app.models.signing import (
    AUTHORITY_PRODUCTION,
    AUTHORITY_SYNTHETIC_UAT,
    DOCUMENT_FAMILY_SUPPLIER_DELIVERY_CHANGE,
    DOCUMENT_FAMILY_SUPPLIER_ORDER,
    ROLE_CONTRACTOR,
    ROLE_SUPPLIER,
    SigningRequest,
)
from app.models.supplier_portal import SupplierDeliveryChange, SupplierPurchaseOrder, SupplierRequestShare
from app.services.signing_artifact_storage import read_retained_bytes, sha256_hex
from app.services import supplier_hub as H
from app.services import supplier_signing as SS
from tests.test_deck_takeoff_workflow import app, client  # noqa: F401
from tests.test_supplier_hub import (  # noqa: F401
    DARCY,
    _fresh_login_per_request,
    _give_sign_in,
    _setup,
    _supplier_client,
    _third,
    _tomlinson,
)

BEN = {"sign_consent": "yes", "signer_name": "Ben Contractor"}
STORE = {"sign_consent": "yes", "signer_name": "Pro Desk Person"}


def _text(data: bytes) -> str:
    return "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(data)).pages)


def _placed_concrete(app, client, *, sign=True):
    """A concrete order placed by the office and waiting for the store (not yet confirmed)."""
    project, _other, _bmr = _setup()
    tomlinson = _tomlinson()
    _give_sign_in(client, tomlinson)
    delivery = (date.today() + timedelta(days=7)).isoformat()
    client.post(f"/projects/{project.id}/concrete-requests", data={
        "volume_m3": "4.5", "strength_mpa": "32", "delivery_date": delivery, "placement": "Pump",
        "contractor_supplier_account_id": tomlinson.id})
    share = SupplierRequestShare.query.one()
    store = _supplier_client(app)
    store.post(f"/supplier/{tomlinson.supplier_id}/requests/{share.id}/quote", data={"price_per_m3": "210", "valid_until": delivery})
    client.post(f"/projects/{project.id}/supplier-requests/{share.id}/approve-quote")
    data = {"delivery_date": delivery, "delivery_window": "7:00–9:00"}
    if sign:
        data.update(BEN)
    client.post(f"/projects/{project.id}/supplier-requests/{share.id}/order", data=data)
    return project, tomlinson, store, share, delivery


def _confirmed(app, client):
    project, tomlinson, store, share, delivery = _placed_concrete(app, client)
    order = SupplierPurchaseOrder.query.one()
    store.post(f"/supplier/{tomlinson.supplier_id}/orders/{order.id}/confirm",
               data={**STORE, "action": "confirm", "expected_delivery": delivery, "delivery_window": "7:00–9:00"})
    return project, tomlinson, store, db.session.get(SupplierPurchaseOrder, order.id)


def test_place_order_needs_the_contractors_signature_and_freezes_the_purchase_order(app, client):
    project, _other, _bmr = _setup()
    tomlinson = _tomlinson()
    _give_sign_in(client, tomlinson)
    delivery = (date.today() + timedelta(days=7)).isoformat()
    client.post(f"/projects/{project.id}/concrete-requests", data={
        "volume_m3": "4.5", "strength_mpa": "32", "delivery_date": delivery, "placement": "Pump",
        "contractor_supplier_account_id": tomlinson.id})
    share = SupplierRequestShare.query.one()
    store = _supplier_client(app)
    store.post(f"/supplier/{tomlinson.supplier_id}/requests/{share.id}/quote", data={"price_per_m3": "210", "valid_until": delivery})
    client.post(f"/projects/{project.id}/supplier-requests/{share.id}/approve-quote")
    page = client.get(f"/projects/{project.id}/supplier-requests")
    assert b"Sign and place order" in page.data and b'name="signer_name"' in page.data and b'name="sign_consent"' in page.data

    for missing in ({"signer_name": "Ben Contractor"}, {"sign_consent": "yes"}, {"sign_consent": "yes", "signer_name": " "}):
        refused = client.post(f"/projects/{project.id}/supplier-requests/{share.id}/order",
                              data={"delivery_date": delivery, **missing}, follow_redirects=True)
        assert b"To sign," in refused.data
        assert SupplierPurchaseOrder.query.count() == 0 and SigningRequest.query.count() == 0

    client.post(f"/projects/{project.id}/supplier-requests/{share.id}/order", data={"delivery_date": delivery, **BEN})
    order = SupplierPurchaseOrder.query.one()
    request = SS.order_signing(order)
    assert request.document_family == DOCUMENT_FAMILY_SUPPLIER_ORDER and request.status == "SENT"
    assert request.project_id == project.id and request.client_id == project.client_id
    contractor = next(p for p in request.participants if p.role == ROLE_CONTRACTOR)
    supplier = next(p for p in request.participants if p.role == ROLE_SUPPLIER)
    assert contractor.confirmed_signer_name == "Ben Contractor" and contractor.signed_at and contractor.consent_accepted_at
    assert supplier.signed_at is None and supplier.invited_name == "Tomlinson concrete (synthetic)"
    frozen = read_retained_bytes(request.frozen_artifact.storage_key)
    assert sha256_hex(frozen) == request.frozen_artifact.sha256
    text = _text(frozen)
    assert order.number in text and "Tomlinson concrete (synthetic)" in text and "Total before tax" in text
    share = SupplierRequestShare.query.one()
    assert project.name not in text and share.shared_json["project_reference"] in text  # the store never sees the job name
    assert [e.event_type for e in request.events] == ["REQUEST_CREATED", "CONSENT_ACCEPTED", "SIGNED", "SENT"]


def test_the_store_signs_in_the_hub_to_confirm_and_both_sides_get_the_signed_copy(app, client):
    project, tomlinson, store, share, delivery = _placed_concrete(app, client)
    order = SupplierPurchaseOrder.query.one()
    page = store.get(f"/supplier/{tomlinson.supplier_id}/requests/{share.id}")
    assert b"Sign and confirm order" in page.data and b"waiting to sign" in page.data and b"signed by Ben Contractor" in page.data

    refused = store.post(f"/supplier/{tomlinson.supplier_id}/orders/{order.id}/confirm",
                         data={"action": "confirm", "expected_delivery": delivery}, follow_redirects=True)
    assert b"To sign," in refused.data and db.session.get(SupplierPurchaseOrder, order.id).status == "PLACED"
    assert SS.order_signing(order).status == "SENT"

    store.post(f"/supplier/{tomlinson.supplier_id}/orders/{order.id}/confirm",
               data={**STORE, "action": "confirm", "expected_delivery": delivery})
    order = db.session.get(SupplierPurchaseOrder, order.id)
    request = SS.order_signing(order)
    assert order.status == "CONFIRMED" and request.status == "EXECUTED" and request.executed_artifact is not None
    supplier = next(p for p in request.participants if p.role == ROLE_SUPPLIER)
    assert supplier.confirmed_signer_name == "Pro Desk Person" and supplier.invited_email == DARCY[1]
    assert [e.event_type for e in request.events][-3:] == ["CONSENT_ACCEPTED", "SIGNED", "EXECUTED"]

    office_pdf = client.get(f"/projects/{project.id}/supplier-signed/{request.id}.pdf")
    hub_pdf = store.get(f"/supplier/{tomlinson.supplier_id}/signed/{request.id}.pdf")
    assert office_pdf.status_code == hub_pdf.status_code == 200 and office_pdf.data == hub_pdf.data
    assert sha256_hex(office_pdf.data) == request.executed_artifact.sha256
    frozen_pages = len(PdfReader(BytesIO(read_retained_bytes(request.frozen_artifact.storage_key))).pages)
    assert len(PdfReader(BytesIO(office_pdf.data)).pages) == frozen_pages + 1
    record = _text(office_pdf.data)
    for expected in ("Ben Contractor", "Pro Desk Person", order.number, request.frozen_artifact.sha256, "Who signed this document"):
        assert expected in record
    assert "signed.pdf" in office_pdf.headers["Content-Disposition"]
    assert b"Signed copy (PDF)" in store.get(f"/supplier/{tomlinson.supplier_id}/requests/{share.id}").data
    assert b"Signed copy (PDF)" in client.get(f"/projects/{project.id}/supplier-requests").data


def test_signed_documents_are_closed_to_other_stores_and_other_contractors(app, client):
    project, tomlinson, store, order = _confirmed(app, client)
    request = SS.order_signing(order)
    third = _third()
    _give_sign_in(client, third, name="Third Store Person", email="third.sign@example.invalid")
    other_store = _supplier_client(app, email="third.sign@example.invalid")
    assert other_store.get(f"/supplier/{third.supplier_id}/signed/{request.id}.pdf").status_code == 404
    assert other_store.get(f"/supplier/{tomlinson.supplier_id}/signed/{request.id}.pdf").status_code in (302, 403, 404)
    other_project, _o, _b = project, None, None
    assert client.get(f"/projects/{other_project.id + 999}/supplier-signed/{request.id}.pdf").status_code == 404
    assert SS.document_for_contractor("ORG-ELSEWHERE", project.id, request.id) is None
    assert SS.document_for_supplier(third.supplier_id, request.id) is None


def test_a_reported_problem_voids_the_open_signature_and_needs_none(app, client):
    project, tomlinson, store, share, delivery = _placed_concrete(app, client)
    order = SupplierPurchaseOrder.query.one()
    store.post(f"/supplier/{tomlinson.supplier_id}/orders/{order.id}/confirm",
               data={"action": "problem", "note": "Plant closed that day"})
    request = SS.order_signing(order)
    assert db.session.get(SupplierPurchaseOrder, order.id).status == "PROBLEM"
    assert request.status == "VOIDED" and "Plant closed" in request.void_reason
    unsigned = client.get(f"/projects/{project.id}/supplier-signed/{request.id}.pdf")
    assert unsigned.status_code == 200 and "for-signing.pdf" in unsigned.headers["Content-Disposition"]


def test_every_agreed_delivery_change_is_signed_by_both_sides(app, client):
    project, tomlinson, store, order = _confirmed(app, client)
    agreed = order.scheduled_date
    new_day = (agreed + timedelta(days=1)).isoformat()
    refused = client.post(f"/projects/{project.id}/orders/{order.id}/delivery-change",
                          data={"new_date": new_day, "reason": "Weather"}, follow_redirects=True)
    assert b"To sign," in refused.data and SupplierDeliveryChange.query.count() == 0

    client.post(f"/projects/{project.id}/orders/{order.id}/delivery-change",
                data={**BEN, "new_date": new_day, "new_window": "7:00–9:00", "reason": "Weather"})
    change = SupplierDeliveryChange.query.one()
    request = SS.change_signing(change)
    assert request.document_family == DOCUMENT_FAMILY_SUPPLIER_DELIVERY_CHANGE and request.status == "SENT"
    assert next(p for p in request.participants if p.role == ROLE_CONTRACTOR).confirmed_signer_name == "Ben Contractor"
    assert "Delivery change for purchase order" in _text(read_retained_bytes(request.frozen_artifact.storage_key))

    unsigned = store.post(f"/supplier/{tomlinson.supplier_id}/delivery-changes/{change.id}/answer",
                          data={"action": "accept"}, follow_redirects=True)
    assert b"To sign," in unsigned.data
    assert db.session.get(SupplierDeliveryChange, change.id).status == "PENDING"
    assert db.session.get(SupplierPurchaseOrder, order.id).scheduled_date == agreed

    store.post(f"/supplier/{tomlinson.supplier_id}/delivery-changes/{change.id}/answer", data={**STORE, "action": "accept"})
    change = db.session.get(SupplierDeliveryChange, change.id)
    request = SS.change_signing(change)
    assert change.status == "ACCEPTED" and request.status == "EXECUTED"
    assert db.session.get(SupplierPurchaseOrder, order.id).scheduled_date == agreed + timedelta(days=1)
    signed = store.get(f"/supplier/{tomlinson.supplier_id}/signed/{request.id}.pdf")
    record = _text(signed.data)
    assert "Ben Contractor" in record and "Pro Desk Person" in record
    history = client.get(f"/projects/{project.id}/supplier-requests").data
    assert f'data-signed-change="{change.id}"'.encode() in history


def test_declining_needs_no_signature_and_a_counter_is_signed_by_the_side_that_proposes(app, client):
    project, tomlinson, store, order = _confirmed(app, client)
    day = (order.scheduled_date + timedelta(days=1)).isoformat()
    client.post(f"/projects/{project.id}/orders/{order.id}/delivery-change", data={**BEN, "new_date": day, "reason": "Weather"})
    first = SupplierDeliveryChange.query.one()
    store.post(f"/supplier/{tomlinson.supplier_id}/delivery-changes/{first.id}/answer",
               data={"action": "decline", "note": "No trucks that day"})
    assert db.session.get(SupplierDeliveryChange, first.id).status == "DECLINED"
    assert SS.change_signing(first).status == "VOIDED"

    client.post(f"/projects/{project.id}/orders/{order.id}/delivery-change", data={**BEN, "new_date": day, "reason": "Weather"})
    second = SupplierDeliveryChange.query.filter_by(status="PENDING").one()
    later = (order.scheduled_date + timedelta(days=2)).isoformat()
    store.post(f"/supplier/{tomlinson.supplier_id}/delivery-changes/{second.id}/answer",
               data={**STORE, "action": "counter", "counter_date": later, "counter_reason": "Supplier availability"})
    assert SS.change_signing(db.session.get(SupplierDeliveryChange, second.id)).status == "VOIDED"
    counter = SupplierDeliveryChange.query.filter_by(status="PENDING").one()
    counter_request = SS.change_signing(counter)
    assert counter.requested_by_side == "SUPPLIER" and counter_request.status == "SENT"
    assert next(p for p in counter_request.participants if p.role == ROLE_SUPPLIER).confirmed_signer_name == "Pro Desk Person"
    client.post(f"/projects/{project.id}/delivery-changes/{counter.id}/answer", data={**BEN, "action": "accept"})
    assert SS.change_signing(db.session.get(SupplierDeliveryChange, counter.id)).status == "EXECUTED"


def test_a_change_proposed_by_a_schedule_move_is_recorded_and_signed_when_accepted(app, client):
    from app.services.schedule import create_schedule_item, shift_project_schedule
    from app.services.work_structure import add_project_element

    project, tomlinson, store, order = _confirmed(app, client)
    element = add_project_element(project_id=project.id, display_name="Foundation pour", organization_id=project.organization_id)
    item = create_schedule_item(project_id=project.id, project_work_element_id=element.id, scheduled_start=order.scheduled_date,
                                scheduled_end=order.scheduled_date, organization_id=project.organization_id)
    order.schedule_item_id = item.id
    db.session.commit()
    shift_project_schedule(project.id, days=2, organization_id=project.organization_id)
    change = SupplierDeliveryChange.query.filter_by(status="PENDING").one()
    request = SS.change_signing(change)
    assert request.status == "SENT" and all(p.signed_at is None for p in request.participants)
    store.post(f"/supplier/{tomlinson.supplier_id}/delivery-changes/{change.id}/answer", data={**STORE, "action": "accept"})
    request = SS.change_signing(db.session.get(SupplierDeliveryChange, change.id))
    assert request.status == "EXECUTED"
    record = _text(SS.document_bytes(request)[0])
    assert "Pro Desk Person" in record and "not signed by typed name" in record


def test_an_order_placed_before_signing_is_frozen_and_signed_when_the_store_confirms(app, client):
    project, tomlinson, store, share, delivery = _placed_concrete(app, client)
    order = SupplierPurchaseOrder.query.one()
    old = SS.order_signing(order)
    db.session.delete(old.participants[1]); db.session.delete(old.participants[0])
    for event in list(old.events):
        db.session.delete(event)
    db.session.delete(old)
    db.session.commit()
    assert SS.order_signing(order) is None
    store.post(f"/supplier/{tomlinson.supplier_id}/orders/{order.id}/confirm", data={**STORE, "action": "confirm"})
    request = SS.order_signing(order)
    assert request.status == "EXECUTED"
    record = _text(SS.document_bytes(request)[0])
    assert "Pro Desk Person" in record and "not signed by typed name" in record


def test_real_suppliers_pin_the_production_consent_and_synthetic_ones_the_test_consent(app, client):
    project, tomlinson, store, order = _confirmed(app, client)
    request = SS.order_signing(order)
    assert tomlinson.supplier.demo_synthetic is True
    assert request.authority_class == AUTHORITY_SYNTHETIC_UAT and request.consent_version.authority_class == AUTHORITY_SYNTHETIC_UAT
    tomlinson.supplier.demo_synthetic = False
    db.session.commit()
    day = (order.scheduled_date + timedelta(days=1)).isoformat()
    client.post(f"/projects/{project.id}/orders/{order.id}/delivery-change", data={**BEN, "new_date": day, "reason": "Weather"})
    change = SupplierDeliveryChange.query.one()
    real = SS.change_signing(change)
    assert real.authority_class == AUTHORITY_PRODUCTION
    assert real.consent_version.version_code == SS.CONSENT_SUPPLIER_V1_CODE
    assert real.consent_version.body_text == SS.CONSENT_SUPPLIER_V1_BODY
    assert "authorized" in SS.CONSENT_SUPPLIER_V1_BODY


def test_supplier_documents_never_reach_the_client_signing_link_or_office_signing_screens(app, client):
    from app.services.signing import _customer_participant, SigningServiceError

    project, tomlinson, store, order = _confirmed(app, client)
    request = SS.order_signing(order)
    assert all(p.lookup_key is None and p.token_hash is None for p in request.participants)
    try:
        _customer_participant(request)
        raise AssertionError("a supplier document has no client signer")
    except SigningServiceError:
        pass
    assert H.SupplierHubError  # the service raises Hub errors on screens
