"""Supplier Unit Pricing & Conversion (Joel, 29 Oct 2026). Synthetic data only.

Takeoff → components and requirements (takeoff units) → Supplier Pricing Request (template library, Supplier
Connection workflow) → the supplier prices each component in its own sell unit → governed conversion and
purchasing-unit rounding → extensions and package price → contractor review → Approve → Purchase Order → the
existing CaliSIGN purchase-order signing. Missing product data is never guessed.
"""

from __future__ import annotations

import json
from datetime import timedelta
from decimal import Decimal
from io import BytesIO

import pytest
from pypdf import PdfReader

from app import db
from app.models.supplier_portal import SupplierPurchaseOrder, SupplierRequestShare
from app.services import supplier_pricing_templates as T
from app.services import supplier_signing as SS
from app.services import unit_pricing as U
from app.services.local_time import local_today
from app.services.supplier_catalogue import (
    create_contractor_supplier_account,
    create_supplier,
    create_supplier_location,
)
from app.services.organizations import DEFAULT_ORGANIZATION_ID
from tests.test_deck_takeoff_workflow import app, client  # noqa: F401
from tests.test_supplier_hub import (  # noqa: F401
    _fresh_login_per_request,
    _give_sign_in,
    _setup,
    _supplier_client,
)
from tests.test_supplier_native_signing import BEN, STORE

V2 = "hardie-vertical-aluminum-v2"
MEASURED = {"siding_sf": "1750", "batten_lf": "1313", "joint_lf": "200", "trim_joint_lf": "600", "soffit_sf": "400",
            "fascia_lf": "315", "corner_lf": "125", "window_trim_lf": "205", "door_trim_lf": "115", "drip_lf": "70",
            "freeze_lf": "125", "jchannel_lf": "315"}
# Calibrayt's quantity in the default sell unit for every line with a verified conversion (the 29 Oct job's).
RESOLVED = {"hpanel": "61", "hbatten": "121", "hflash": "22", "htouch": "1", "soffit": "28", "fascia": "29",
            "corner": "14", "wtrim": "19", "dtrim": "11", "drip": "8", "freeze": "12", "jchan": "29"}
UNRESOLVED = {"hnails", "hcaulk", "anails", "screws"}
VALID = (local_today() + timedelta(days=30)).isoformat()


def _n(share, key):
    return next(f"{int(l['number']):02d}" for l in share.shared_json["lines"] if l["key"] == key)


def _create(client, project, account, **extra):
    data = {"template": V2, "contractor_supplier_account_id": str(account.id),
            **{f"m_{k}": v for k, v in MEASURED.items()}, **extra}
    return client.post(f"/projects/{project.id}/unit-pricing", data=data, follow_redirects=True)


def _prices(share, overrides=None):
    """$10.00 per unit on every line in its default unit, then the overrides."""
    values = {"valid_until": VALID, "quote_number": "Q-SYN-1"}
    for line in share.shared_json["lines"]:
        n = f"{int(line['number']):02d}"
        values[f"sell_unit_{n}"] = line["default_unit"]
        values[f"unit_price_{n}"] = "10.00"
    values.update(overrides or {})
    return values


# ---------------------------------------------------------------------------------------------- requirements
def test_requirements_are_in_takeoff_units_and_only_verified_conversions_give_a_quantity():
    package = U.requirement_lines(V2, MEASURED)
    by_key = {l["key"]: l for l in package["lines"]}
    assert {k: l["qty"] for k, l in by_key.items() if l["qty"] is not None} == RESOLVED
    assert {k for k, l in by_key.items() if l["qty"] is None} == UNRESOLVED
    assert by_key["hpanel"]["requirement"] == {"qty": "1925", "unit": "SF", "basis": "1,750 SF + 10% waste"}
    assert by_key["hpanel"]["conversion"]["per"] == "32" and "4 ft x 8 ft" in by_key["hpanel"]["conversion"]["basis"]
    assert by_key["hbatten"]["requirement"]["qty"] == "1444.3"
    # Fasteners are counted from the pieces they fasten; how many a box covers is not known, so no box count.
    assert by_key["hnails"]["requirement"]["qty"] == "182" and by_key["hnails"]["requirement"]["unit"] == "PC fastened"
    assert by_key["anails"]["requirement"]["qty"] == "150" and by_key["screws"]["requirement"]["qty"] == "28"
    assert by_key["hcaulk"]["requirement"] == {"qty": "600", "unit": "LF", "basis": "600 LF"}


def test_the_template_holds_no_invented_ratio():
    template = T.load_template(V2)
    for item in template["items"]:
        for unit in item["sell_units"]:
            if item["key"] in UNRESOLVED:
                assert unit["per"] is None and "no verified product data" in unit["basis"], item["key"]
            else:
                assert unit["per"] and unit["basis"], item["key"]
    text = json.dumps(template)
    assert "per_unit" not in text and "4,500" not in text and "1,100" not in text and "25 LF/tube" not in text


def test_v1_is_superseded_kept_loadable_and_not_offered():
    keys = [t["key"] for t in T.list_templates()]
    assert V2 in keys and "hardie-vertical-aluminum-v1" not in keys
    assert T.load_template("hardie-vertical-aluminum-v1")["superseded_by"] == V2
    with pytest.raises(U.UnitPricingError):
        U.requirement_lines("hardie-vertical-aluminum-v1", MEASURED)


def test_purchasing_unit_rounding_is_always_up_and_exact_stays_exact():
    assert U.round_up(Decimal("1925") / Decimal("32")) == 61
    assert U.round_up(Decimal("3520") / Decimal("32")) == 110
    assert U.round_up(Decimal("440") / Decimal("16")) == 28
    assert U.round_up(Decimal("220") / Decimal("10")) == 22


def test_bad_or_missing_measurements_are_refused():
    for bad in ({k: v for k, v in MEASURED.items() if k != "drip_lf"}, {**MEASURED, "drip_lf": "lots"},
                {**MEASURED, "drip_lf": "-1"}, {**MEASURED, "deck_sf": "10"}):
        with pytest.raises(U.UnitPricingError):
            U.requirement_lines(V2, bad)


# ---------------------------------------------------------------------------------------------- the workflow
def test_end_to_end_supplier_units_conversion_review_approve_order_and_calisign(app, client):
    project, _other, account = _setup()
    _give_sign_in(client, account)
    page = _create(client, project, account)
    assert b"It is in their Supplier Hub now" in page.data
    share = SupplierRequestShare.query.one()
    assert share.source_kind == "UNIT_PRICING" and share.request_kind == "MATERIAL" and share.status == "SENT"
    # The supplier sees only the shared fields: no customer, no job name, no address.
    flat = str(share.shared_json)
    assert project.name not in flat and "D'Arcy" not in flat
    office = client.get(f"/projects/{project.id}/supplier-requests").data
    assert b'data-unit-request="' + share.number.encode() + b'"' in office and b"To confirm" in office

    store = _supplier_client(app)
    hub = store.get(f"/supplier/{account.supplier_id}/requests/{share.id}")
    assert hub.status_code == 200 and b"Pricing request: Hardie vertical siding" in hub.data
    assert project.name.encode() not in hub.data and b"data-unit-price-form" in hub.data
    assert db.session.get(SupplierRequestShare, share.id).status == "OPENED"

    # BMR's POS: batten sold per lineal foot, sealant by the tube with the store's own coverage, soffit
    # fasteners by the box with the store's own quantity; the nail boxes are priced but their coverage unknown.
    values = _prices(share, {
        f"sell_unit_{_n(share, 'hbatten')}": "LF", f"unit_price_{_n(share, 'hbatten')}": "1.85",
        f"unit_price_{_n(share, 'hpanel')}": "52.40",
        f"supplier_per_{_n(share, 'hcaulk')}": "30",
        f"supplier_qty_{_n(share, 'screws')}": "2",
    })
    returned = store.post(f"/supplier/{account.supplier_id}/requests/{share.id}/quote", data=values,
                          follow_redirects=True)
    assert b"Quote returned to the contractor" in returned.data
    share = db.session.get(SupplierRequestShare, share.id)
    view = U.price_package(share)
    rows = {r["line"]["key"]: r for r in view["rows"]}
    assert (rows["hpanel"]["qty"], rows["hpanel"]["extension"]) == (61, Decimal("3196.40"))
    assert rows["hbatten"]["unit"] == "LF" and rows["hbatten"]["qty"] == 1445  # 1,444.3 LF rounded up
    assert rows["hbatten"]["conversion"]["source"] == U.SOURCE_IDENTITY
    assert rows["hbatten"]["extension"] == Decimal("2673.25")
    assert rows["hcaulk"]["qty"] == 20 and rows["hcaulk"]["conversion"]["source"] == U.SOURCE_SUPPLIER
    assert rows["screws"]["qty"] == 2 and rows["screws"]["qty_source"] == U.SOURCE_SUPPLIER
    assert rows["hnails"]["status"] == U.CONVERSION_MISSING and rows["hnails"]["qty"] is None
    assert rows["anails"]["status"] == U.CONVERSION_MISSING
    assert any("Hardie siding nails" in b for b in view["blockers"])
    # Nothing is approved or ordered while a conversion is missing.
    refused = client.post(f"/projects/{project.id}/unit-pricing/{share.id}/approve", follow_redirects=True)
    assert b"cannot be approved yet" in refused.data
    assert client.post(f"/projects/{project.id}/supplier-requests/{share.id}/order",
                       data={**BEN}, follow_redirects=True).status_code == 200
    assert SupplierPurchaseOrder.query.count() == 0

    # The contractor records the nail-box coverage with its source, and takes the aluminum nails out.
    no_source = client.post(f"/projects/{project.id}/unit-pricing/{share.id}/conversion",
                            data={"number": int(_n(share, "hnails")), "per": "100", "source": ""},
                            follow_redirects=True)
    assert b"Say where the conversion comes from" in no_source.data
    client.post(f"/projects/{project.id}/unit-pricing/{share.id}/conversion",
                data={"number": int(_n(share, "hnails")), "per": "100", "source": "Synthetic spec sheet (test)"})
    client.post(f"/projects/{project.id}/unit-pricing/{share.id}/exclude",
                data={"number": int(_n(share, "anails")), "reason": "Crew has a stock of them (test)"})
    share = db.session.get(SupplierRequestShare, share.id)
    view = U.price_package(share)
    rows = {r["line"]["key"]: r for r in view["rows"]}
    assert rows["hnails"]["qty"] == 2 and rows["hnails"]["conversion"]["source"] == U.SOURCE_CONTRACTOR  # 182 / 100
    assert rows["anails"]["status"] == U.EXCLUDED and view["blockers"] == []
    expected = sum(r["extension"] for r in view["rows"] if r["status"] == U.PRICED)
    assert view["subtotal"] == expected and view["hst"] == (expected * Decimal("0.13")).quantize(Decimal("0.01"))
    groups = view["groups"]
    assert groups["siding"]["total"] + groups["alum"]["total"] == view["subtotal"]

    approved = client.post(f"/projects/{project.id}/unit-pricing/{share.id}/approve", follow_redirects=True)
    assert b"Package approved" in approved.data
    share = db.session.get(SupplierRequestShare, share.id)
    assert share.quote_json["approved"]["subtotal"] == str(view["subtotal"])
    # Fixed after approval.
    late = client.post(f"/projects/{project.id}/unit-pricing/{share.id}/exclude",
                       data={"number": int(_n(share, "hpanel")), "reason": "too late"}, follow_redirects=True)
    assert b"already approved" in late.data

    # Purchase order through the existing CaliSIGN purchase-order signing.
    client.post(f"/projects/{project.id}/supplier-requests/{share.id}/order",
                data={**BEN, "delivery_date": (local_today() + timedelta(days=7)).isoformat(), "delivery_window": "8:00–10:00"})
    order = SupplierPurchaseOrder.query.one()
    assert order.total == view["subtotal"]
    by_number = {int(l["number"]): l for l in order.lines_json}
    assert len(order.lines_json) == 15  # 16 lines, one not ordered
    panel = by_number[int(_n(share, "hpanel"))]
    assert (panel["quantity"], panel["unit"], panel["net_unit_cost"], panel["line_value"]) == ("61", "PC", "52.4", "3196.40")
    assert by_number[int(_n(share, "hbatten"))]["unit"] == "LF"
    assert SS.order_signing(order).status == "SENT"
    store.post(f"/supplier/{account.supplier_id}/orders/{order.id}/confirm",
               data={**STORE, "action": "confirm", "expected_delivery": (local_today() + timedelta(days=7)).isoformat()})
    assert SS.order_signing(db.session.get(SupplierPurchaseOrder, order.id)).status == "EXECUTED"


def test_a_supplier_without_a_sign_in_gets_the_approved_form_and_the_office_enters_the_prices(app, client):
    project, _other, _account = _setup()
    supplier = create_supplier(code="TEST-OFFLINE", legal_name="Offline Lumber (synthetic)", demo_synthetic=True)
    location = create_supplier_location(supplier_id=supplier.id, code="MAIN", display_name="Main", demo_synthetic=True)
    account = create_contractor_supplier_account(organization_id=DEFAULT_ORGANIZATION_ID, supplier_id=supplier.id,
                                                 supplier_location_id=location.id, demo_synthetic=True)
    page = _create(client, project, account)
    assert b"has no Supplier Hub sign-in" in page.data
    share = SupplierRequestShare.query.one()
    assert share.shared_json["unit_pricing"]["online"] is False
    pdf = client.get(f"/projects/{project.id}/unit-pricing/{share.id}/form.pdf")
    assert pdf.status_code == 200 and pdf.mimetype == "application/pdf"
    reader = PdfReader(BytesIO(pdf.data))
    fields = reader.get_fields()
    assert fields[f"qty_hpanel"].get("/V") == "61" and fields["qty_hbatten"].get("/V") == "121"
    assert not fields["qty_hnails"].get("/V")  # never guessed on the form either
    assert "quantity to confirm" in reader.pages[0].extract_text()
    client.post(f"/projects/{project.id}/unit-pricing/{share.id}/prices",
                data=_prices(share, {f"supplier_qty_{_n(share, k)}": "1" for k in UNRESOLVED}))
    share = db.session.get(SupplierRequestShare, share.id)
    assert share.status == "RETURNED" and "returned form" in share.returned_by_name
    assert U.price_package(share)["blockers"] == []


def test_price_entry_is_checked_and_never_guesses(app, client):
    project, _other, account = _setup()
    _give_sign_in(client, account)
    _create(client, project, account)
    share = SupplierRequestShare.query.one()
    with pytest.raises(U.UnitPricingError, match="valid until"):
        U.record_prices(share, user=None, values={**_prices(share), "valid_until": ""}, side="SUPPLIER")
    with pytest.raises(U.UnitPricingError, match="past"):
        U.record_prices(share, user=None, values={**_prices(share), "valid_until": "2020-01-01"}, side="SUPPLIER")
    with pytest.raises(U.UnitPricingError, match="No prices"):
        U.record_prices(share, user=None, values={"valid_until": VALID}, side="SUPPLIER")
    with pytest.raises(U.UnitPricingError, match="must be a number"):
        U.record_prices(share, user=None, values=_prices(share, {f"unit_price_{_n(share, 'hpanel')}": "abc"}),
                        side="SUPPLIER")
    with pytest.raises(U.UnitPricingError, match="whole number"):
        U.record_prices(share, user=None, values=_prices(share, {f"supplier_qty_{_n(share, 'hnails')}": "1.5"}),
                        side="SUPPLIER")
    with pytest.raises(U.UnitPricingError, match="name the unit"):
        U.record_prices(share, user=None, values=_prices(share, {f"sell_unit_{_n(share, 'hnails')}": "OTHER"}),
                        side="SUPPLIER")
    # A unit the template does not know has no conversion: priced, but no quantity until someone gives one.
    U.record_prices(share, user=None, values=_prices(share, {f"sell_unit_{_n(share, 'hpanel')}": "OTHER",
                                                             f"other_unit_{_n(share, 'hpanel')}": "bundle"}),
                    side="SUPPLIER")
    rows = {r["line"]["key"]: r for r in U.price_package(db.session.get(SupplierRequestShare, share.id))["rows"]}
    assert rows["hpanel"]["unit"] == "BUNDLE" and rows["hpanel"]["status"] == U.CONVERSION_MISSING
    assert rows["htouch"]["status"] == U.PRICED and rows["htouch"]["qty"] == 1


def test_another_supplier_cannot_see_or_price_the_request(app, client):
    project, _other, account = _setup()
    _give_sign_in(client, account)
    _create(client, project, account)
    share = SupplierRequestShare.query.one()
    other = create_supplier(code="TEST-OTHER", legal_name="Other Store (synthetic)", demo_synthetic=True)
    location = create_supplier_location(supplier_id=other.id, code="MAIN", display_name="Main", demo_synthetic=True)
    other_account = create_contractor_supplier_account(organization_id=DEFAULT_ORGANIZATION_ID, supplier_id=other.id,
                                                       supplier_location_id=location.id, demo_synthetic=True)
    _give_sign_in(client, other_account, name="Other Person", email="other.store@example.invalid")
    intruder = _supplier_client(app, email="other.store@example.invalid")
    assert intruder.get(f"/supplier/{other.id}/requests/{share.id}").status_code == 404
    assert intruder.post(f"/supplier/{other.id}/requests/{share.id}/quote", data=_prices(share)).status_code == 404
    assert db.session.get(SupplierRequestShare, share.id).status == "SENT"


def test_a_revised_takeoff_replaces_the_open_request_for_that_supplier_and_template(app, client):
    project, _other, account = _setup()
    _give_sign_in(client, account)
    _create(client, project, account)
    _create(client, project, account, m_siding_sf="2000")
    first, second = SupplierRequestShare.query.order_by(SupplierRequestShare.id).all()
    assert first.status == "SUPERSEDED" and second.status == "SENT"
    assert next(l for l in second.shared_json["lines"] if l["key"] == "hpanel")["qty"] == "69"  # 2,200 / 32


def test_a_missing_measurement_creates_nothing(app, client):
    project, _other, account = _setup()
    page = _create(client, project, account, m_siding_sf="")
    assert b"Vertical siding area is required" in page.data and SupplierRequestShare.query.count() == 0
