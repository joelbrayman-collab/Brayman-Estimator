"""The PRO Desk quotation link's Accept / Decline form carries a CSRF token (roles walk, 20 Oct 2026).

The customer page is a standalone page without the office script that adds the token to forms, and its form
had none: with CSRF on, as on the hosted office, every customer answer was refused with
"Bad Request: The CSRF token is missing" (found by tools/release/evidence_roles.mjs). Synthetic data only.
"""

from __future__ import annotations

import re

import pytest

from app import db
from app.models.supplier_quote import SupplierQuote
from tests.test_supplier_hub import _fresh_login_per_request, app, client  # noqa: F401
from tests.test_supplier_pro_desk import _match_all, _post_building, _ready_supplier, _start


@pytest.fixture(autouse=True)
def _fresh_csrf_per_request(app):  # noqa: F811
    """As with sign-ins (_fresh_login_per_request): the fixture holds one app context, so flask-wtf's
    per-request token cache on g would be shared by every test client. Production requests each get their own."""
    from flask import g

    def clear():
        g.pop("csrf_token", None)

    app.before_request_funcs.setdefault(None, []).insert(0, clear)
    yield


def _issued_link(app, client):  # noqa: F811
    supplier, store = _ready_supplier(app, client)
    quote, base = _start(store, supplier)
    _post_building(store, base)
    _match_all(store, base, supplier.id)
    store.post(f"{base}/commercials", data={"delivery_charge": "150", "discount_percent": ""})
    store.post(f"{base}/issue")
    assert db.session.get(SupplierQuote, quote.id).status == "ISSUED"
    response = store.post(f"{base}/link")
    return quote.id, "/quote/" + re.search(r"link=([^#&]+)", response.headers["Location"]).group(1)


def _token(page: str) -> str:
    match = re.search(r'name="csrf_token" value="([^"]+)"', page)
    assert match, "the answer form has no CSRF token"
    return match.group(1)


def test_the_customer_accepts_with_csrf_on(app, client):  # noqa: F811
    quote_id, link = _issued_link(app, client)
    app.config["WTF_CSRF_ENABLED"] = True
    try:
        customer = app.test_client()
        page = customer.get(link).get_data(as_text=True)
        refused = customer.post(f"{link}/answer", data={"customer_name": "Synthetic Farmer", "answer": "accept", "agree": "yes"})
        assert refused.status_code == 400  # without the token
        done = customer.post(f"{link}/answer", data={"customer_name": "Synthetic Farmer", "answer": "accept", "agree": "yes",
                                                     "csrf_token": _token(page)})
        assert done.status_code == 200 and b"accepted" in done.data, done.data[-1500:]
    finally:
        app.config["WTF_CSRF_ENABLED"] = False
    assert db.session.get(SupplierQuote, quote_id).status == "ACCEPTED"


def test_the_customer_declines_with_csrf_on(app, client):  # noqa: F811
    quote_id, link = _issued_link(app, client)
    app.config["WTF_CSRF_ENABLED"] = True
    try:
        customer = app.test_client()
        page = customer.get(link).get_data(as_text=True)
        done = customer.post(f"{link}/answer", data={"customer_name": "Synthetic Farmer", "answer": "decline",
                                                     "csrf_token": _token(page)})
        assert done.status_code == 200
    finally:
        app.config["WTF_CSRF_ENABLED"] = False
    assert db.session.get(SupplierQuote, quote_id).status == "DECLINED"
