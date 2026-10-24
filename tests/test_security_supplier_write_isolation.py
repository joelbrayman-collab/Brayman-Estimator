"""Security: one supplier cannot write to, open, or read another supplier's records.

Setup follows tests/test_supplier_hub.py: one contractor (ORG-001), supplier A (Tomlinson
concrete, signed in as Darcy) with a confirmed concrete order, an open concrete request and
a pending contractor delivery change, and supplier B (Third supplier) with its own sign-in.
Supplier B tries every supplier-side write against A's records, both with A's supplier id
in the URL and with its own supplier id plus A's share/order/change ids. Synthetic data only.
"""

from __future__ import annotations

from datetime import date, timedelta
from app.services.local_time import local_today
from io import BytesIO

import pytest

from app import db
from app.models.supplier_portal import (
    SupplierBrandProfile,
    SupplierDeliveryChange,
    SupplierPurchaseOrder,
    SupplierRequestEvent,
    SupplierRequestShare,
    TextMessage,
)
from app.models.transactional_message import TransactionalMessage
from tests.test_deck_takeoff_workflow import app, client  # noqa: F401
from tests.test_supplier_hub import (  # noqa: F401
    PNG,
    _concrete_order,
    _fresh_login_per_request,
    _give_sign_in,
    _supplier_client,
    _third,
)

THIRD_EMAIL = "third.isolation@example.invalid"


def _rows(model):
    db.session.expire_all()
    columns = [c.name for c in model.__table__.columns]
    return [
        {name: getattr(row, name) for name in columns}
        for row in model.query.order_by(model.id).all()
    ]


def _state():
    return {
        "shares": _rows(SupplierRequestShare),
        "orders": _rows(SupplierPurchaseOrder),
        "changes": _rows(SupplierDeliveryChange),
        "events": _rows(SupplierRequestEvent),
        "brands": _rows(SupplierBrandProfile),
        "texts": TextMessage.query.count(),
        "mail": TransactionalMessage.query.count(),
    }


@pytest.fixture
def world(app, client):  # noqa: F811
    project, tomlinson, darcy, _darcy_user, order = _concrete_order(app, client)
    # A's logo, so the logo route has something to leak.
    saved = client.post(
        f"/suppliers/{tomlinson.supplier_id}/branding",
        data={"display_name": "Tomlinson", "primary_color": "#123456", "logo": (BytesIO(PNG), "t.png")},
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert b"Branding saved" in saved.data
    # A pending contractor delivery change on A's order.
    client.post(
        f"/projects/{project.id}/orders/{order.id}/delivery-change",
        data={"new_date": (order.scheduled_date + timedelta(days=1)).isoformat(), "reason": "Weather"},
    )
    change = SupplierDeliveryChange.query.one()
    assert change.status == "PENDING" and change.requested_by_side == "CONTRACTOR"
    # A second, still-open concrete request to A (a quote could still be returned on it).
    delivery = (local_today() + timedelta(days=9)).isoformat()
    client.post(f"/projects/{project.id}/concrete-requests", data={
        "volume_m3": "2.0", "strength_mpa": "25", "delivery_date": delivery, "placement": "Chute",
        "contractor_supplier_account_id": tomlinson.id})
    open_share = SupplierRequestShare.query.filter(SupplierRequestShare.id != order.share_id).one()
    assert open_share.status == "SENT" and open_share.supplier_id == tomlinson.supplier_id

    third_account = _third()
    _give_sign_in(client, third_account, name="Third Store Person", email=THIRD_EMAIL)
    other = _supplier_client(app, email=THIRD_EMAIL)
    return {
        "project": project,
        "a_id": tomlinson.supplier_id,
        "b_id": third_account.supplier_id,
        "b_account": third_account,
        "darcy": darcy,
        "other": other,
        "order": order,
        "change": change,
        "open_share": open_share,
        "delivery": delivery,
    }


def test_supplier_b_cannot_write_to_or_open_supplier_a_records(app, world):
    a_id, b_id, other = world["a_id"], world["b_id"], world["other"]
    order, change, open_share = world["order"], world["change"], world["open_share"]
    new_day = (order.scheduled_date + timedelta(days=3)).isoformat()
    before = _state()

    attempts = []
    for supplier_id in (a_id, b_id):
        attempts += [
            ("POST", f"/supplier/{supplier_id}/requests/{open_share.id}/quote",
             {"quote_number": "FORGED-1", "price_per_m3": "1.00", "valid_until": world["delivery"]}),
            ("POST", f"/supplier/{supplier_id}/requests/{order.share_id}/quote",
             {"quote_number": "FORGED-2", "price_per_m3": "1.00", "valid_until": world["delivery"]}),
            ("POST", f"/supplier/{supplier_id}/orders/{order.id}/confirm",
             {"action": "confirm", "expected_delivery": new_day}),
            ("POST", f"/supplier/{supplier_id}/orders/{order.id}/confirm",
             {"action": "problem", "note": "forged problem"}),
            ("POST", f"/supplier/{supplier_id}/orders/{order.id}/delivery-change",
             {"new_date": new_day, "new_window": "7:00–9:00", "reason": "Weather", "note": "forged"}),
            ("POST", f"/supplier/{supplier_id}/delivery-changes/{change.id}/answer", {"action": "accept"}),
            ("POST", f"/supplier/{supplier_id}/delivery-changes/{change.id}/answer",
             {"action": "decline", "note": "forged decline"}),
            ("POST", f"/supplier/{supplier_id}/delivery-changes/{change.id}/withdraw", {}),
            ("GET", f"/supplier/{supplier_id}/requests/{open_share.id}", None),
            ("GET", f"/supplier/{supplier_id}/requests/{order.share_id}", None),
        ]
    attempts += [
        ("GET", f"/supplier/{a_id}/logo", None),
        ("GET", f"/supplier/{a_id}/", None),
        ("GET", f"/supplier/{a_id}/dashboard", None),
        ("GET", f"/supplier/{a_id}/deliveries", None),
        ("POST", f"/supplier/{a_id}/text-numbers",
         {"name": "Forged", "mobile_phone": "613-555-0199", "consent": "yes"}),
    ]

    for method, path, data in attempts:
        response = other.open(path, method=method, data=data, follow_redirects=False)
        assert response.status_code == 404, (method, path, response.status_code)
        assert PNG not in response.data
        assert order.number.encode() not in response.data
        assert open_share.number.encode() not in response.data

    assert _state() == before
    # The open request was not marked opened by B's GETs.
    assert db.session.get(SupplierRequestShare, open_share.id).status == "SENT"
    assert db.session.get(SupplierRequestShare, open_share.id).opened_at is None
    # Control: A's own person still reaches the same records.
    assert world["darcy"].get(f"/supplier/{a_id}/logo").data == PNG
    assert world["darcy"].get(f"/supplier/{a_id}/requests/{order.share_id}").status_code == 200


def test_supplier_b_quote_on_the_same_job_never_shows_on_supplier_a_pages(app, client, world):  # noqa: F811
    project, b_account, other, darcy = world["project"], world["b_account"], world["other"], world["darcy"]
    a_id, b_id = world["a_id"], world["b_id"]
    client.post(f"/projects/{project.id}/concrete-requests", data={
        "volume_m3": "3.0", "strength_mpa": "30", "delivery_date": world["delivery"], "placement": "Pump",
        "contractor_supplier_account_id": b_account.id})
    b_share = SupplierRequestShare.query.filter_by(supplier_id=b_id).one()
    assert b_share.project_id == world["open_share"].project_id  # the same contractor job
    returned = other.post(f"/supplier/{b_id}/requests/{b_share.id}/quote", data={
        "quote_number": "THIRD-QN-7731", "price_per_m3": "987.65", "valid_until": world["delivery"]})
    assert returned.status_code == 302
    b_share = db.session.get(SupplierRequestShare, b_share.id)
    assert b_share.status == "RETURNED" and b_share.quote_json["quote_number"] == "THIRD-QN-7731"
    b_page = other.get(f"/supplier/{b_id}/requests/{b_share.id}")
    assert b"THIRD-QN-7731" in b_page.data  # control: B sees its own quote

    pages = [
        f"/supplier/{a_id}/",
        f"/supplier/{a_id}/requests/{world['open_share'].id}",
        f"/supplier/{a_id}/requests/{world['order'].share_id}",
        f"/supplier/{a_id}/dashboard",
        f"/supplier/{a_id}/demand",
        f"/supplier/{a_id}/deliveries",
        "/supplier/",
    ]
    for path in pages:
        response = darcy.get(path, follow_redirects=True)
        assert response.status_code == 200, path
        assert b"THIRD-QN-7731" not in response.data, path
        assert b"987.65" not in response.data, path
        assert b_share.number.encode() not in response.data, path
        assert b"Third supplier (synthetic)" not in response.data, path
    assert darcy.get(f"/supplier/{a_id}/requests/{b_share.id}").status_code == 404
    assert darcy.get(f"/supplier/{b_id}/requests/{b_share.id}").status_code == 404
