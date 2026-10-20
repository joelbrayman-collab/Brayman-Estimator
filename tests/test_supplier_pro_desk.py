"""Supplier PRO Desk: walk-in quotation owned by a supplier (Joel, 20 Oct 2026; ADR-047 Amendment 1).

Synthetic suppliers, customers and prices only. The reference building is the directive's: 30 × 40 ft,
12 ft walls, one 10 × 10 ft overhead door and one man door. Takeoff numbers below are worked by hand in the
comments, so a change to a rule shows up here.
"""

from __future__ import annotations

import io
import re
from datetime import date, timedelta
from decimal import Decimal

import pytest

from app import db
from app.models import Estimate, Project, Proposal
from app.models.canonical_material import CanonicalMaterial
from app.models.supplier_catalogue import CanonicalMaterialSupplierMap, SupplierProduct
from app.models.supplier_quote import SupplierCustomer, SupplierQuote, SupplierQuoteEvent, SupplierSellingPrice
from app.models.transactional_message import TransactionalMessage
from app.models.user import User
from app.services import supplier_pro_desk as P
from app.services.auth import hash_password
from app.services.drawings import outbuilding as OB
from app.services.outbuilding import spec as S
from app.services.outbuilding import takeoff as T
from app.services.supplier_catalogue import create_contractor_supplier_account, create_supplier, create_supplier_location
from app.services.organizations import DEFAULT_ORGANIZATION_ID
from tests.test_supplier_hub import (  # noqa: F401
    DARCY,
    PASSWORD,
    _fresh_login_per_request,
    _give_sign_in,
    _setup,
    _supplier_client,
    app,
    client,
)

REFERENCE = {
    "building_system": "POST_FRAME_STEEL", "width_ft": "30", "length_ft": "40", "wall_height_ft": "12",
    "roof_type": "GABLE", "roof_pitch": "4", "eave_overhang_in": "12", "gable_overhang_in": "12",
    "post_spacing_ft": "8", "endwall_post_spacing_ft": "10", "post_description": "3-ply 2×6 laminated column, treated",
    "truss_spacing_ft": "8", "purlin_spacing_in": "24", "purlin_lumber": "2×4 SPF", "girt_spacing_in": "24",
    "girt_lumber": "2×4 SPF", "skirt_lumber": "2×8 pressure-treated", "roof_panel_coverage_in": "36",
    "wall_panel_coverage_in": "36", "screws_per_sqft": "", "foundation": "NONE",
    "opening_0_kind": "OVERHEAD_DOOR", "opening_0_wall": "LEFT", "opening_0_width_in": "120", "opening_0_height_in": "120",
    "opening_0_offset_ft": "10",
    "opening_1_kind": "MAN_DOOR", "opening_1_wall": "FRONT", "opening_1_width_in": "36", "opening_1_height_in": "80",
    "opening_1_offset_ft": "4",
}

TODAY = date.today()
PRICE_FILE = (
    "sku,description,unit,pack_qty,price,discount_percent,discount_rule,effective_from,effective_to,availability,store\n"
    f"SYN-2416,2x4x16 SPF (synthetic),EA,,9.00,,,{TODAY - timedelta(days=5)},,IN_STOCK,\n"
    f"SYN-PT2816,2x8x16 treated (synthetic),EA,,30.00,,,{TODAY - timedelta(days=5)},,IN_STOCK,\n"
    f"SYN-PANEL,Steel panel cut to length (synthetic),LF,,4.00,10,Farm promo 10%,{TODAY - timedelta(days=5)},,LIMITED,\n"
    f"SYN-TRIM10,Steel trim 10 ft (synthetic),EA,,20.00,,,{TODAY - timedelta(days=5)},,,\n"
    f"SYN-OH1010,Overhead door 10x10 (synthetic),EA,,1500.00,,,{TODAY - timedelta(days=5)},,SPECIAL_ORDER,\n"
    f"SYN-MAN3068,Man door 3068 (synthetic),EA,,400.00,,,{TODAY - timedelta(days=5)},,,\n"
    f"SYN-POST,Laminated column (synthetic),EA,,60.00,,,{TODAY - timedelta(days=5)},,,\n"
    f"SYN-EXPIRED,Old price (synthetic),EA,,1.00,,,{TODAY - timedelta(days=90)},{TODAY - timedelta(days=30)},,\n"
    "SYN-BAD,Bad row,EA,,not-a-number,,,2026-01-01,,,\n"
    f"SYN-STORE,Store-only item (synthetic),EA,,5.00,,,{TODAY - timedelta(days=1)},,,NOWHERE\n"
)


def _values(**over):
    form = dict(REFERENCE)
    form.update(over)
    values, errors = S.read_answers(form)
    assert errors == []
    return values


def _line(result, code_prefix):
    return next(l for l in result["lines"] if l["code"].startswith(code_prefix))


# ---------------------------------------------------------------------------------------------
# Takeoff rules (hand-worked)


def test_reference_building_takeoff_is_worked_from_the_confirmed_geometry():
    r = T.takeoff(_values())
    assert r["ready"] and r["missing"] == []
    # Posts: 40 ft / 8 ft = 5 bays → 6 per sidewall = 12; endwalls 30/10 = 3 bays → 2 between corners × 2 = 4.
    assert _line(r, "CAL-OB-POST")["qty"] == "16" and _line(r, "CAL-OB-POST")["status"] == T.REVIEW
    # Trusses: 40/8 = 5, + 1 = 6; counted only, design by the truss manufacturer.
    truss = _line(r, "CAL-OB-TRUSS")
    assert truss["qty"] == "6" and truss["status"] == T.REVIEW and "30 ft span, 4/12" in truss["item"]
    # Slope: (180 run + 12 eave) × √(1 + (4/12)²) = 202.39 in → 16'-11"; 42 ft roof / 36 in = 14 panels per side.
    roof = _line(r, "CAL-OB-ROOF-PANEL")
    assert roof["cut_list"] == [("16'-11\"", 28)] and roof["qty"] == "473.67"  # 28 × 203 in / 12
    # Purlins: floor(202.39 / 24) + 1 = 9 rows per slope × 2 × 504 in = 756 LF.
    assert _line(r, "CAL-OB-PURLIN-2X4-SPF")["qty"] == "756.00"
    # Girts: 6 rows × 1680 in perimeter − overhead door 120 in at 4 rows − man door 36 in at 3 rows
    #        + gable rows (60 in rise): 2 × (216 + 72) = 10068 in = 839 LF.
    assert _line(r, "CAL-OB-GIRT-2X4-SPF")["qty"] == "839.00"
    # Wall panels: 2 × 14 sidewall panels @ 12 ft; endwalls 10 panels each up to the gable (13–17 ft);
    # the two panels wholly over the overhead door stop at its head: 17 ft − 10 ft = 7 ft.
    wall = _line(r, "CAL-OB-WALL-PANEL")
    assert dict((length, n) for length, n in wall["cut_list"]) == {
        "17'-0\"": 2, "16'-0\"": 4, "15'-0\"": 4, "14'-0\"": 4, "13'-0\"": 4, "12'-0\"": 28, "7'-0\"": 2}
    assert wall["qty"] == "616.00"
    # Trims and doors.
    assert _line(r, "CAL-OB-RIDGE-CAP")["qty"] == "42.00" and _line(r, "CAL-OB-TRIM-EAVE")["qty"] == "84.00"
    assert _line(r, "CAL-OB-TRIM-BASE")["qty"] == "127.00"  # 140 ft − 10 ft − 3 ft
    assert _line(r, "CAL-OB-DOOR-OH-120X120")["qty"] == "1" and _line(r, "CAL-OB-DOOR-MAN-36X80")["qty"] == "1"
    # The door header is listed for review, never sized or counted.
    framing = _line(r, "CAL-OB-DOOR-FRAMING")
    assert framing["qty"] is None and framing["status"] == T.REVIEW


def test_nothing_is_assumed_when_an_answer_is_missing():
    values = _values(purlin_spacing_in="", roof_panel_coverage_in="", post_description="", foundation="TO_CONFIRM")
    r = T.takeoff(values)
    for prefix in ("CAL-OB-PURLIN", "CAL-OB-ROOF-PANEL", "CAL-OB-POST", "CAL-CONC", "CAL-OB-CLADDING-SCREW"):
        line = _line(r, prefix)
        assert line["qty"] is None and line["status"] == T.NEEDS_ANSWER, prefix
    assert {"Purlin spacing", "Roof panel coverage width"} <= set(S.missing_answers(values))
    # A slab is only quoted from a stated thickness and allowance.
    slab = _line(T.takeoff(_values(foundation="SLAB", slab_thickness_in="5", concrete_waste_percent="5")), "CAL-CONC")
    assert slab["uom"] == "M3" and slab["status"] == T.REVIEW
    assert Decimal(slab["qty"]) == (Decimal("500") * Decimal("0.028316846592") * Decimal("1.05")).quantize(Decimal("0.01"), rounding="ROUND_CEILING")


def test_answers_are_checked_not_corrected():
    _values_, errors = S.read_answers({**REFERENCE, "roof_pitch": "40", "width_ft": "abc", "opening_1_offset_ft": "39"})
    assert any("Roof pitch" in e for e in errors) and any("Width" in e for e in errors)
    assert any("runs past the end" in e for e in errors)
    assert _values_["roof_pitch"] is None  # a bad answer is dropped, not clamped


def test_the_drawing_uses_the_engine_and_says_what_it_is():
    values = _values()
    ident = OB.Identity(company="Synthetic Supply", company_lines=["Synthetic store"], project="Q-TEST", address="Synthetic Rd",
                        date="2026-10-20")
    dset = OB.OutbuildingDrawingSet(values, ident)
    sheets = dset.sheets()
    assert [s.number for s in sheets] == ["A-1", "A-2"]
    assert all(s.title_block.status == "PRELIMINARY SALES DRAWING — NOT FOR CONSTRUCTION" for s in sheets)
    assert len(OB.post_positions(values)) == 16
    assert OB.render(values, ident, fmt="pdf").startswith(b"%PDF")
    assert b"SECTION" in OB.render(values, ident, fmt="dxf")[:4000] or len(OB.render(values, ident, fmt="dxf")) > 1000
    assert OB.render(values, ident, fmt="png").startswith(b"\x89PNG")
    assert OB.fingerprint(values) == OB.fingerprint(dict(values))


def test_no_ai_or_network_service_is_used_by_the_pro_desk():
    import inspect

    from app.routes import supplier_pro_desk as routes
    from app.services import supplier_quote_pdf

    for module in (P, T, S, OB, routes, supplier_quote_pdf):
        source = inspect.getsource(module)
        assert not re.search(r"^\s*(import|from)\s+(openai|anthropic|requests|httpx|urllib)", source, re.M), module.__name__


# ---------------------------------------------------------------------------------------------
# The counter workflow, end to end through the pages


def _sign_in(app, client):
    _project, _other, account = _setup()
    _give_sign_in(client, account)
    return account.supplier, _supplier_client(app)


def _post_building(store, base):
    return store.post(f"{base}/building", data=REFERENCE, follow_redirects=True)


def _ready_supplier(app, client):
    supplier, store = _sign_in(app, client)
    store.post(f"/supplier/{supplier.id}/pro-desk/settings", data={"tax_label": "HST", "tax_rate_percent": "13",
                                                                  "validity_days": "30", "terms_text": "Synthetic terms."})
    page = store.post(f"/supplier/{supplier.id}/pro-desk/prices",
                      data={"authorized_by": "Synthetic manager", "demo_synthetic": "yes",
                            "price_file": (io.BytesIO(PRICE_FILE.encode()), "prices.csv")},
                      content_type="multipart/form-data", follow_redirects=True)
    assert b"8 prices loaded; 2 rows not loaded" in page.data, re.findall(rb"flash-[a-z]+\" role=\"status\">([^<]*)", page.data)
    return supplier, store


def _start(store, supplier, **extra):
    data = {"customer_name": "Synthetic Farmer", "customer_phone": "613-555-0100", "customer_email": "joel.brayman@gmail.com",
            "customer_town": "Winchester", "consent_email": "yes", "demo_synthetic": "yes", **extra}
    response = store.post(f"/supplier/{supplier.id}/pro-desk/new", data=data)
    assert response.status_code == 302, response.data[:300]
    quote = SupplierQuote.query.order_by(SupplierQuote.id.desc()).first()
    return quote, f"/supplier/{supplier.id}/pro-desk/{quote.id}"


MATCHES = {  # takeoff line → (synthetic SKU, selling units per takeoff unit)
    "CAL-OB-POST": ("SYN-POST", "1"),
    "CAL-OB-PURLIN-2X4-SPF": ("SYN-2416", "0.0625"),
    "CAL-OB-GIRT-2X4-SPF": ("SYN-2416", "0.0625"),
    "CAL-OB-SKIRT-2X8-PRESSURE-TREATED": ("SYN-PT2816", "0.0625"),
    "CAL-OB-ROOF-PANEL": ("SYN-PANEL", "1"),
    "CAL-OB-WALL-PANEL": ("SYN-PANEL", "1"),
    "CAL-OB-RIDGE-CAP": ("SYN-TRIM10", "0.1"),
    "CAL-OB-TRIM-EAVE": ("SYN-TRIM10", "0.1"),
    "CAL-OB-TRIM-RAKE": ("SYN-TRIM10", "0.1"),
    "CAL-OB-TRIM-CORNER": ("SYN-TRIM10", "0.1"),
    "CAL-OB-TRIM-BASE": ("SYN-TRIM10", "0.1"),
    "CAL-OB-TRIM-OPENING": ("SYN-TRIM10", "0.1"),
    "CAL-OB-DOOR-OH-120X120": ("SYN-OH1010", "1"),
    "CAL-OB-DOOR-MAN-36X80": ("SYN-MAN3068", "1"),
}


def _match_all(store, base, supplier_id):
    for code, (sku, factor) in MATCHES.items():
        product = SupplierProduct.query.filter_by(supplier_id=supplier_id, sku=sku).one()
        r = store.post(f"{base}/match", data={"code": code, "product_id": product.id, "sales_per_unit": factor})
        assert r.status_code == 302
    store.post(f"{base}/line", data={"code": "CAL-OB-TRUSS-30FT-4-12", "exclude_reason": "Truss quote to follow from the truss manufacturer"})
    store.post(f"{base}/line", data={"code": "CAL-OB-CLADDING-SCREW", "exclude_reason": "Screws chosen with the panel order"})


def test_walk_in_quotation_from_sketch_to_order_ready_package(app, client):
    supplier, store = _ready_supplier(app, client)
    counts_before = (Project.query.count(), Estimate.query.count(), Proposal.query.count())
    index = store.get(f"/supplier/{supplier.id}/pro-desk/").data
    assert b"Quick Quote" in index and b"Detailed quotation" in index
    quote, base = _start(store, supplier)
    assert quote.customer.consent_email and quote.customer.consent_recorded_by_name == DARCY[0]
    png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
    store.post(f"{base}/sketch", data={"sketch": (io.BytesIO(png), "sketch.png")}, content_type="multipart/form-data")
    assert len(P.active_sketches(quote)) == 1
    page = _post_building(store, base)
    assert b"Building confirmed" in page.data and b"PRELIMINARY" not in page.data[:0]
    assert store.get(f"{base}/drawing.png").data.startswith(b"\x89PNG")
    assert store.get(f"{base}/drawing.pdf").data.startswith(b"%PDF")
    page = store.get(base).data.decode()
    assert "Before it can be issued" in page and "choose the product" in page
    _match_all(store, base, supplier.id)
    priced = P.price_quote(db.session.get(SupplierQuote, quote.id))
    assert priced["blockers"] == [], priced["blockers"]
    rows = {r["code"]: r for r in priced["rows"]}
    # Purlins 756 LF × 1/16 → 47.25 → 48 pieces × $9.00; girts 839 LF → 52.4375 → 53 × $9.00.
    assert rows["CAL-OB-PURLIN-2X4-SPF"]["sales_qty"] == "48" and rows["CAL-OB-PURLIN-2X4-SPF"]["extended"] == "432.00"
    assert rows["CAL-OB-GIRT-2X4-SPF"]["sales_qty"] == "53"
    # Panels priced per LF with the file's 10% rule: 473.67 × $4.00 = 1894.68, discount 189.47.
    assert rows["CAL-OB-ROOF-PANEL"]["extended"] == "1894.68" and rows["CAL-OB-ROOF-PANEL"]["line_discount"] == "189.47"
    assert rows["CAL-OB-TRUSS-30FT-4-12"]["price_status"] == P.EXCLUDED
    assert rows["CAL-OB-DOOR-FRAMING"]["price_status"] == P.BY_DESIGN
    t = priced["totals"]
    assert Decimal(t["total"]) == (Decimal(t["taxable"]) * Decimal("1.13")).quantize(Decimal("0.01"))
    store.post(f"{base}/commercials", data={"delivery_charge": "150", "discount_percent": ""})
    issued = store.post(f"{base}/issue", follow_redirects=True)
    quote = db.session.get(SupplierQuote, quote.id)
    assert quote.status == "ISSUED" and quote.issued_sha256 and b"Quotation " + quote.number.encode() + b" issued" in issued.data
    frozen_total = quote.issued_json["totals"]["total"]
    assert Decimal(frozen_total) == quote.total and quote.issued_json["totals"]["delivery"] == "150.00"
    pdf = store.get(f"{base}/quotation.pdf")
    assert pdf.status_code == 200 and pdf.data.startswith(b"%PDF")
    from pypdf import PdfReader

    pages = PdfReader(io.BytesIO(pdf.data)).pages  # quotation, then one page each for A-1 plan and A-2 elevations
    assert sum("Preliminary sales drawing" in p.extract_text() for p in pages) == 2, len(pages)
    # A later price file change does not move the issued quotation.
    product = SupplierProduct.query.filter_by(supplier_id=supplier.id, sku="SYN-PANEL").one()
    P.import_price_file(supplier, filename="new.csv", authorized_by="Synthetic manager", user=User.query.filter_by(email=DARCY[1]).one(),
                        demo_synthetic=True, content=(f"sku,description,unit,price,effective_from\nSYN-PANEL,Steel panel,LF,9.99,{TODAY}\n").encode())
    assert P.current_price(product, None, TODAY).amount == Decimal("9.99")
    assert db.session.get(SupplierQuote, quote.id).issued_json["totals"]["total"] == frozen_total
    # The customer gets an approval link (email with consent, through the allow-listed mail service).
    response = store.post(f"{base}/link", data={"send_email": "yes"})
    credential = re.search(r"link=([^#&]+)", response.headers["Location"]).group(1)
    assert TransactionalMessage.query.filter_by(template_id="SUPPLIER_QUOTE").count() == 1
    customer = app.test_client()
    view = customer.get(f"/quote/{credential}")
    assert view.status_code == 200 and frozen_total.encode() in view.data and view.headers["Cache-Control"] == "no-store"
    assert customer.get(f"/quote/{credential}/quotation.pdf").data.startswith(b"%PDF")
    refused = customer.post(f"/quote/{credential}/answer", data={"customer_name": "Synthetic Farmer", "answer": "accept"})
    assert refused.status_code == 400  # the box must be ticked
    done = customer.post(f"/quote/{credential}/answer", data={"customer_name": "Synthetic Farmer", "answer": "accept", "agree": "yes"})
    assert done.status_code == 200 and b"accepted" in done.data
    quote = db.session.get(SupplierQuote, quote.id)
    assert quote.status == "ACCEPTED" and quote.acceptance_method == "CUSTOMER_LINK" and quote.accepted_sha256 == quote.issued_sha256
    # Order-ready package for the store's own system.
    store.post(f"{base}/order-ready")
    sheet = store.get(f"{base}/order")
    assert sheet.status_code == 200 and b"SYN-PANEL" in sheet.data
    csv_text = store.get(f"{base}/order.csv").data.decode()
    assert "SYN-OH1010" in csv_text and frozen_total in csv_text
    # No contractor record of any kind was made.
    assert (Project.query.count(), Estimate.query.count(), Proposal.query.count()) == counts_before
    kinds = [e.event_type for e in SupplierQuoteEvent.query.filter_by(quote_id=quote.id).order_by(SupplierQuoteEvent.id)]
    for expected in ("CREATED", "SKETCH_ADDED", "BUILDING_CONFIRMED", "PRODUCT_CHOSEN", "LINE_EXCLUDED", "ISSUED",
                     "LINK_CREATED", "EMAILED", "ACCEPTED", "ORDER_READY"):
        assert expected in kinds, expected


def test_an_incomplete_quotation_cannot_be_issued_or_accepted(app, client):
    supplier, store = _ready_supplier(app, client)
    quote, base = _start(store, supplier)
    _post_building(store, base)
    page = store.post(f"{base}/issue", follow_redirects=True)
    assert b"Not ready to issue" in page.data and db.session.get(SupplierQuote, quote.id).status == "DRAFT"
    with pytest.raises(P.ProDeskError):
        P.create_link(db.session.get(SupplierQuote, quote.id), user=User.query.filter_by(email=DARCY[1]).one())
    accept = store.post(f"{base}/accept", data={"customer_name": "X", "method": "in_person"}, follow_redirects=True)
    assert b"already been answered or is no longer open" in accept.data
    assert db.session.get(SupplierQuote, quote.id).status == "DRAFT"


def test_revision_replaces_the_link_and_keeps_the_issued_record(app, client):
    supplier, store = _ready_supplier(app, client)
    quote, base = _start(store, supplier)
    _post_building(store, base)
    _match_all(store, base, supplier.id)
    store.post(f"{base}/issue")
    credential = re.search(r"link=([^#&]+)", store.post(f"{base}/link").headers["Location"]).group(1)
    store.post(f"{base}/revise")
    old = db.session.get(SupplierQuote, quote.id)
    assert old.status == "CANCELLED" and old.issued_json  # kept as issued
    assert app.test_client().get(f"/quote/{credential}").status_code == 410
    new = SupplierQuote.query.filter(SupplierQuote.number == f"{old.number}-R1").one()
    assert new.status == "DRAFT" and new.spec_json == old.spec_json and len(P.active_sketches(new)) == len(P.active_sketches(old))


def test_expired_quotation_cannot_be_accepted(app, client):
    supplier, store = _ready_supplier(app, client)
    quote, base = _start(store, supplier)
    _post_building(store, base)
    _match_all(store, base, supplier.id)
    store.post(f"{base}/issue")
    credential = re.search(r"link=([^#&]+)", store.post(f"{base}/link").headers["Location"]).group(1)
    q = db.session.get(SupplierQuote, quote.id)
    q.valid_until = TODAY - timedelta(days=1)
    db.session.commit()
    answer = app.test_client().post(f"/quote/{credential}/answer", data={"customer_name": "S F", "answer": "accept", "agree": "yes"})
    assert answer.status_code == 400 and b"expired" in answer.data


# ---------------------------------------------------------------------------------------------
# Isolation, privacy and file safety


def test_suppliers_offices_and_strangers_cannot_reach_each_others_quotations(app, client):
    supplier, store = _ready_supplier(app, client)
    quote, base = _start(store, supplier)
    png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
    store.post(f"{base}/sketch", data={"sketch": (io.BytesIO(png), "sketch.png")}, content_type="multipart/form-data")
    sketch_id = P.active_sketches(quote)[0].id
    # A second supplier with its own sign-in sees none of it.
    other = create_supplier(code="TEST-HH", legal_name="Other supply (synthetic)", demo_synthetic=True)
    location = create_supplier_location(supplier_id=other.id, code="MAIN", display_name="Main", demo_synthetic=True)
    account = create_contractor_supplier_account(organization_id=DEFAULT_ORGANIZATION_ID, supplier_id=other.id,
                                                 supplier_location_id=location.id, demo_synthetic=True)
    _give_sign_in(client, account, name="Other Synthetic", email="other.store@example.invalid")
    rival = _supplier_client(app, email="other.store@example.invalid")
    for path in (base, f"{base}/drawing.pdf", f"{base}/sketch/{sketch_id}", f"{base}/quotation.pdf"):
        assert rival.get(path).status_code == 404, path
    assert rival.get(f"/supplier/{other.id}/pro-desk/{quote.id}").status_code == 404
    assert b"Synthetic Farmer" not in rival.get(f"/supplier/{other.id}/pro-desk/").data
    assert rival.post(f"/supplier/{other.id}/pro-desk/{quote.id}/building", data=REFERENCE).status_code == 404
    # The contractor office cannot open supplier quotations at all.
    assert client.get(base).status_code == 403
    assert client.get(f"/supplier/{supplier.id}/pro-desk/").status_code == 403
    # Signed out: sent to the supplier sign-in, never served.
    stranger = app.test_client()
    assert stranger.get(f"{base}/sketch/{sketch_id}").status_code == 302
    # A guessed or tampered approval link is refused.
    assert stranger.get("/quote/abc.def").status_code == 410
    # Supplier customers carry no contractor organization.
    assert "organization_id" not in SupplierCustomer.__table__.columns and "organization_id" not in SupplierQuote.__table__.columns


def test_sketch_files_are_checked_by_their_content(app, client):
    supplier, store = _ready_supplier(app, client)
    quote, base = _start(store, supplier)
    bad = store.post(f"{base}/sketch", data={"sketch": (io.BytesIO(b"<script>alert(1)</script>"), "sketch.png")},
                     content_type="multipart/form-data", follow_redirects=True)
    assert b"must be a JPEG or PNG photo, or a PDF" in bad.data and P.active_sketches(quote) == []
    big = b"\xff\xd8\xff" + b"0" * (P.MAX_SKETCH_BYTES + 10)
    page = store.post(f"{base}/sketch", data={"sketch": (io.BytesIO(big), "big.jpg")}, content_type="multipart/form-data",
                      follow_redirects=True)
    assert b"larger than 10 MB" in page.data
    ok = b"%PDF-1.4\n%synthetic\n"
    store.post(f"{base}/sketch", data={"sketch": (io.BytesIO(ok), "../../etc/passwd.pdf")}, content_type="multipart/form-data")
    row = P.active_sketches(quote)[0]
    assert row.mime == "application/pdf" and "/" not in row.filename
    served = store.get(f"{base}/sketch/{row.id}")
    assert served.headers["X-Content-Type-Options"] == "nosniff" and served.headers["Cache-Control"] == "no-store"


def test_email_needs_the_customers_recorded_consent(app, client):
    supplier, store = _ready_supplier(app, client)
    quote, base = _start(store, supplier, consent_email="")
    _post_building(store, base)
    _match_all(store, base, supplier.id)
    store.post(f"{base}/issue")
    page = store.post(f"{base}/link", data={"send_email": "yes"}, follow_redirects=True)
    assert b"has not agreed to receive this quotation by email" in page.data
    assert TransactionalMessage.query.filter_by(template_id="SUPPLIER_QUOTE").count() == 0
    with pytest.raises(P.ProDeskError, match="Email consent needs an email address"):
        P.start_quote(supplier, {"customer_name": "A", "consent_email": "yes"}, user=User.query.filter_by(email=DARCY[1]).one())


# ---------------------------------------------------------------------------------------------
# Price file and product matches


def test_price_file_rows_are_checked_and_prices_follow_their_dates_and_store(app, client):
    supplier, store = _ready_supplier(app, client)
    record = P.price_imports(supplier.id)[0]
    reasons = {r["sku"]: r["reason"] for r in record.rejections_json}
    assert "price is not a number" in reasons["SYN-BAD"] and "not one of this supplier's stores" in reasons["SYN-STORE"]
    assert record.authorized_by_name == "Synthetic manager" and record.source == "DEMO_SYNTHETIC"
    expired = SupplierProduct.query.filter_by(supplier_id=supplier.id, sku="SYN-EXPIRED").one()
    assert P.current_price(expired, None, TODAY) is None  # outside its dates: no price, never a guess
    darcy = User.query.filter_by(email=DARCY[1]).one()
    with pytest.raises(P.ProDeskError, match="authorized"):
        P.import_price_file(supplier, filename="x.csv", content=b"sku,description,unit,price,effective_from\n", authorized_by="",
                            user=darcy)
    with pytest.raises(P.ProDeskError, match="needs these columns"):
        P.import_price_file(supplier, filename="x.csv", content=b"sku,price\nA,1\n", authorized_by="M", user=darcy)
    unit = P.import_price_file(supplier, filename="u.csv", authorized_by="M", user=darcy,
                               content=f"sku,description,unit,price,effective_from\nSYN-PANEL,Panel,EA,1,{TODAY}\n".encode())
    assert unit.rows_loaded == 0 and "differs from this SKU's selling unit" in unit.rejections_json[0]["reason"]
    # A store's own price wins over the supplier-wide price.
    location = supplier.locations[0]
    P.import_price_file(supplier, filename="s.csv", authorized_by="M", user=darcy,
                        content=f"sku,description,unit,price,effective_from,store\nSYN-2416,2x4,EA,8.50,{TODAY},{location.code}\n".encode())
    lumber = SupplierProduct.query.filter_by(supplier_id=supplier.id, sku="SYN-2416").one()
    assert P.current_price(lumber, location.id, TODAY).amount == Decimal("8.50")
    assert P.current_price(lumber, None, TODAY).amount == Decimal("9.00")
    # Store selling prices never become contractor cost evidence.
    from app.models.supplier_catalogue import SupplierProductPriceEvidence

    assert SupplierProductPriceEvidence.query.count() == 0 and SupplierSellingPrice.query.count() >= 8


def test_product_matches_only_reach_outbuilding_lines_and_never_change(app, client):
    supplier, store = _ready_supplier(app, client)
    darcy = User.query.filter_by(email=DARCY[1]).one()
    product = SupplierProduct.query.filter_by(supplier_id=supplier.id, sku="SYN-2416").one()
    deck_line = {"code": "CAL-PT-2X8-16", "item": "Deck joist", "uom": "EA", "category": "DIMENSIONAL_LUMBER"}
    with pytest.raises(P.ProDeskError, match="Only outbuilding"):
        P.match_product(supplier, deck_line, product_id=product.id, sales_per_unit="1", user=darcy)
    line = {"code": "CAL-OB-PURLIN-2X4-SPF", "item": "Roof purlins, 2×4 SPF", "uom": "LF", "category": "DIMENSIONAL_LUMBER"}
    P.match_product(supplier, line, product_id=product.id, sales_per_unit="0.0625", user=darcy)
    with pytest.raises(P.ProDeskError, match="already matched"):
        P.match_product(supplier, line, product_id=product.id, sales_per_unit="0.08", user=darcy)
    material = CanonicalMaterial.query.filter_by(code="CAL-OB-PURLIN-2X4-SPF").one()
    assert material.category == "DIMENSIONAL_LUMBER" and material.canonical_uom == "LF"
    assert CanonicalMaterialSupplierMap.query.filter_by(canonical_material_id=material.id).count() == 1
    # Another supplier's product cannot be matched by this supplier.
    other = create_supplier(code="TEST-HH2", legal_name="Other (synthetic)", demo_synthetic=True)
    foreign = SupplierProduct(supplier_id=other.id, sku="X", description="X", sales_uom="EA", status="ACTIVE")
    db.session.add(foreign)
    db.session.commit()
    with pytest.raises(P.ProDeskError, match="this supplier's products"):
        P.match_product(supplier, line, product_id=foreign.id, sales_per_unit="1", user=darcy)


def test_pages_render_for_phone_and_desktop_without_errors(app, client):
    supplier, store = _ready_supplier(app, client)
    quote, base = _start(store, supplier)
    for path in (f"/supplier/{supplier.id}/pro-desk/", f"/supplier/{supplier.id}/pro-desk/new", base,
                 f"/supplier/{supplier.id}/pro-desk/quick", f"/supplier/{supplier.id}/pro-desk/standards",
                 f"/supplier/{supplier.id}/pro-desk/timing",
                 f"/supplier/{supplier.id}/pro-desk/prices", f"/supplier/{supplier.id}/pro-desk/settings"):
        page = store.get(path)
        assert page.status_code == 200, path
        assert b'name="viewport"' in page.data
    assert b"PRO Desk quotations" in store.get(f"/supplier/{supplier.id}/").data


# ---------------------------------------------------------------------------------------------
# Quick Quote: store standards plus the answers that change per building (Joel, 20 Oct 2026)

STANDARD = {k: REFERENCE[k] for k in S.ASSEMBLY_KEYS}
QUICK = {"width_ft": "30", "length_ft": "40", "wall_height_ft": "12", "roof_pitch": "4", "foundation": "NONE",
         "qd_0_kind": "OVERHEAD_DOOR", "qd_0_count": "1", "qd_0_width_in": "120", "qd_0_height_in": "120", "qd_0_wall": "LEFT",
         "qd_1_kind": "MAN_DOOR", "qd_1_count": "1", "qd_1_width_in": "36", "qd_1_height_in": "80", "qd_1_wall": "FRONT"}


def test_a_standard_needs_every_answer_and_nothing_is_filled_in_for_the_store():
    values, errors = S.read_assembly({})
    assert all(v is None for v in values.values())
    required = [k for k in S.ASSEMBLY_KEYS if k not in S.ASSEMBLY_OPTIONAL]
    assert len(errors) == len(required)
    values, errors = S.read_assembly({**STANDARD, "post_spacing_ft": "40"})
    assert any("Sidewall post spacing" in e for e in errors)  # same ranges as the detailed form
    values, errors = S.read_assembly(STANDARD)
    assert errors == [] and values["screws_per_sqft"] is None


def test_quick_answers_give_the_same_takeoff_as_the_detailed_form():
    standard, _ = S.read_assembly(STANDARD)
    values, errors = S.read_quick(QUICK, standard)
    assert errors == [] and S.missing_answers(values) == []
    # Openings spaced evenly: endwall 360 in − 120 in → 120 in gaps; sidewall 480 − 36 → 222 in = 18.5 ft.
    assert {(o["wall"], o["offset_ft"]) for o in values["openings"]} == {("LEFT", "10.00"), ("FRONT", "18.50")}
    quick = {l["code"]: (l["qty"], l["status"]) for l in T.takeoff(values)["lines"]}
    detailed = {l["code"]: (l["qty"], l["status"]) for l in T.takeoff(_values())["lines"]}
    assert quick == detailed


def test_quick_answers_are_checked_and_never_guessed():
    standard, _ = S.read_assembly(STANDARD)
    _values_, errors = S.read_quick({}, standard)
    assert {"Width (endwall): required.", "Length (sidewall): required.", "Wall height (eave): required.",
            "Roof pitch: required.", "Floor / foundation: required."} <= set(errors)
    _v, errors = S.read_quick({**QUICK, "qd_0_count": "3"}, standard)  # three 10 ft doors in a 30 ft endwall
    assert any("do not fit" in e for e in errors)
    _v, errors = S.read_quick({**QUICK, "foundation": "SLAB"}, standard)
    assert "Slab thickness: required for a concrete slab." in errors
    _v, errors = S.read_quick({**QUICK, "qd_1_wall": ""}, standard)
    assert any("choose which wall" in e for e in errors)


def _standard(store, supplier, **over):
    data = {"name": "Post-frame steel, 8 ft bays (synthetic)", "basis": "Synthetic store standard for tests",
            "demo_synthetic": "yes", **STANDARD, **over}
    return store.post(f"/supplier/{supplier.id}/pro-desk/standards", data=data)


def test_quick_quote_from_customer_to_printable_quotation_with_timing(app, client):
    from app.models.supplier_quote import SupplierBuildingAssembly

    supplier, store = _ready_supplier(app, client)
    assert b"No standard buildings yet" in store.get(f"/supplier/{supplier.id}/pro-desk/quick").data
    assert _standard(store, supplier, basis="").status_code == 400  # the basis is required
    assert _standard(store, supplier).status_code == 302
    standard = SupplierBuildingAssembly.query.filter_by(supplier_id=supplier.id).one()
    assert standard.approved_by_name == DARCY[0] and standard.values_json["post_spacing_ft"] == "8"
    page = store.get(f"/supplier/{supplier.id}/pro-desk/quick").data.decode()
    started = re.search(r'name="started_at" value="([^"]+)"', page).group(1)
    form = {"customer_name": "Synthetic Farmer", "customer_email": "joel.brayman@gmail.com", "consent_email": "yes",
            "demo_synthetic": "yes", "assembly_id": str(standard.id), "started_at": started, **QUICK}
    before = SupplierQuote.query.count()
    bad = store.post(f"/supplier/{supplier.id}/pro-desk/quick", data={**form, "width_ft": ""})
    assert bad.status_code == 400 and b"Width (endwall): required." in bad.data and SupplierQuote.query.count() == before
    png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
    done = store.post(f"/supplier/{supplier.id}/pro-desk/quick", data={**form, "sketch": (io.BytesIO(png), "sketch.png")},
                      content_type="multipart/form-data")
    assert done.status_code == 302 and done.headers["Location"].endswith("#pricing")
    quote = SupplierQuote.query.order_by(SupplierQuote.id.desc()).first()
    base = f"/supplier/{supplier.id}/pro-desk/{quote.id}"
    assert quote.spec_json["quick"] and quote.spec_json["assembly"]["id"] == standard.id
    assert quote.spec_json["intake_started_at"] == started and len(P.active_sketches(quote)) == 1
    page = store.get(base).data.decode()
    assert "Quick Quote from the store standard" in page and "change any answer (detailed building form)" in page
    _match_all(store, base, supplier.id)
    assert P.price_quote(db.session.get(SupplierQuote, quote.id))["blockers"] == []
    assert store.post(f"{base}/issue").status_code == 302
    quote = db.session.get(SupplierQuote, quote.id)
    assert quote.issued_json["standard"]["name"] == standard.name and quote.issued_json["standard"]["openings_placed"]
    from pypdf import PdfReader

    for _ in range(2):  # printing twice records one printed time
        pdf = store.get(f"{base}/quotation.pdf")
    text = PdfReader(io.BytesIO(pdf.data)).pages[0].extract_text() + PdfReader(io.BytesIO(pdf.data)).pages[1].extract_text()
    assert "store's standard building" in " ".join(text.split())
    assert SupplierQuoteEvent.query.filter_by(quote_id=quote.id, event_type="QUOTATION_PRINTED").count() == 1
    timing = P.quote_timing(quote)
    assert timing["quick"] and timing["started_recorded"] and timing["printed"]
    assert timing["walk_in_seconds"] is not None and timing["walk_in_seconds"] >= 0
    assert timing["exception_actions"] >= len(MATCHES)  # matching products during the quote is exception time
    stages = [r["stage"] for r in timing["rows"]]
    assert stages[0] == "Customer and building answers" and "Open the printable quotation" in stages
    timing_page = store.get(f"/supplier/{supplier.id}/pro-desk/timing").data.decode()
    assert "One-time store setup (not part of quotation time)" in timing_page and quote.number in timing_page


def test_changing_a_standard_answer_on_one_quotation_is_recorded(app, client):
    from app.models.supplier_quote import SupplierBuildingAssembly

    supplier, store = _ready_supplier(app, client)
    _standard(store, supplier)
    standard = SupplierBuildingAssembly.query.filter_by(supplier_id=supplier.id).one()
    store.post(f"/supplier/{supplier.id}/pro-desk/quick",
               data={"customer_name": "Synthetic Farmer", "demo_synthetic": "yes", "assembly_id": str(standard.id), **QUICK})
    quote = SupplierQuote.query.order_by(SupplierQuote.id.desc()).first()
    base = f"/supplier/{supplier.id}/pro-desk/{quote.id}"
    store.post(f"{base}/building", data={**REFERENCE, "purlin_spacing_in": "16"})
    quote = db.session.get(SupplierQuote, quote.id)
    assert quote.spec_json["assembly_overridden"] == ["purlin_spacing_in"] and quote.spec_json["quick"]
    assert "Purlin spacing" in store.get(base).data.decode().split("Changed from the standard")[1][:200]


def test_standards_belong_to_one_store_and_retired_ones_are_not_offered(app, client):
    from app.models.supplier_quote import SupplierBuildingAssembly

    supplier, store = _ready_supplier(app, client)
    _standard(store, supplier)
    standard = SupplierBuildingAssembly.query.filter_by(supplier_id=supplier.id).one()
    other = create_supplier(code="TEST-HH2", legal_name="Other supply (synthetic)", demo_synthetic=True)
    location = create_supplier_location(supplier_id=other.id, code="MAIN", display_name="Main", demo_synthetic=True)
    account = create_contractor_supplier_account(organization_id=DEFAULT_ORGANIZATION_ID, supplier_id=other.id,
                                                 supplier_location_id=location.id, demo_synthetic=True)
    _give_sign_in(client, account, name="Other Synthetic", email="other2.store@example.invalid")
    rival = _supplier_client(app, email="other2.store@example.invalid")
    for path in ("quick", "standards", "timing"):
        assert rival.get(f"/supplier/{supplier.id}/pro-desk/{path}").status_code == 404
    assert standard.name.encode() not in rival.get(f"/supplier/{other.id}/pro-desk/standards").data
    used = rival.post(f"/supplier/{other.id}/pro-desk/quick",
                      data={"customer_name": "X", "assembly_id": str(standard.id), **QUICK})
    assert used.status_code == 400 and SupplierQuote.query.filter_by(supplier_id=other.id).count() == 0
    assert rival.post(f"/supplier/{other.id}/pro-desk/standards", data={"retire": str(standard.id)}).status_code == 404
    store.post(f"/supplier/{supplier.id}/pro-desk/standards", data={"retire": str(standard.id)})
    assert db.session.get(SupplierBuildingAssembly, standard.id).status == "RETIRED"
    assert b"No standard buildings yet" in store.get(f"/supplier/{supplier.id}/pro-desk/quick").data
    refused = store.post(f"/supplier/{supplier.id}/pro-desk/quick", data={"customer_name": "X", "assembly_id": str(standard.id), **QUICK})
    assert refused.status_code == 400 and b"retired" in refused.data
    assert client.get(f"/supplier/{supplier.id}/pro-desk/quick").status_code == 403  # contractor office
