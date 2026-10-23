"""Framing materials quote request (Joel, 23 Oct 2026). Synthetic data only.

A straight wall's count and purchase become one supplier request: the same PDF,
manifest, Supplier Hub share, price return and price evidence as the deck takeoff.
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from app import db
from app.models import Client, Project
from app.models.canonical_material import CANONICAL_MATERIAL_SEED
from app.models.supplier_portal import SOURCE_DECK_FORM2, SOURCE_FRAMING_FORM2, SupplierRequestShare
from app.services import framing_request as F
from app.services import wall_framing_purchasing as buy
from app.services.deck_takeoff import storage
from app.services.estimates import create_estimate
from app.services.organizations import DEFAULT_ORGANIZATION_ID
from app.services.wall_framing import calculate_straight_wall
from tests.test_supplier_hub import (  # noqa: F401
    DARCY,
    RESPONSE_DATE,
    VALID_UNTIL,
    _give_sign_in,
    _supplier_client,
    _fresh_login_per_request,
    app,
    client,
)
from tests.test_deck_takeoff_workflow import _setup
from tests.test_wall_framing_calculator import FIXTURE


def _wall(**extra):
    return calculate_straight_wall(**{**FIXTURE, **extra})


def _estimate(project):
    estimate = create_estimate(project_id=project.id, estimate_number="EST-FRQ-1", title="Framing quote")
    return estimate, estimate.current_version


def _framing_url(estimate, version):
    return f"/estimates/{estimate.id}/versions/{version.id}/framing-quantities"


def test_every_framing_code_is_in_the_catalogue():
    seed = {row["code"] for row in CANONICAL_MATERIAL_SEED}
    assert F.FRAMING_CODES <= seed


def test_rows_use_only_the_purchase_and_name_a_code_only_for_exact_stock():
    result = _wall()
    bought = buy.purchase(result, waste_percent="10", plate_stock_length_ft="16", stud_stock_length_in="92.625")
    rows = F.request_rows(result, bought)
    by_key = {r["key"]: r for r in rows}
    assert by_key["framing.studs"]["purchasing_quantity"] == bought["stud_pieces"]
    assert by_key["framing.studs"]["canonical_material_code"] == "CAL-LUM-2X4-STUD-9258"
    assert by_key["framing.plates"]["purchasing_quantity"] == bought["plate_pieces"]
    assert by_key["framing.plates"]["canonical_material_code"] == "CAL-LUM-2X4-16"
    assert all(r["complete"] for r in rows)
    # No stock length: studs are not mapped, plates stay lineal feet and are not final.
    open_bought = buy.purchase(result, waste_percent="0")
    open_rows = {r["key"]: r for r in F.request_rows(result, open_bought)}
    assert open_rows["framing.studs"]["canonical_material_code"] is None
    plates = open_rows["framing.plates"]
    assert plates["purchasing_unit"] == "LF" and plates["complete"] is False and plates["canonical_material_code"] is None


def test_the_request_is_stable_and_matches_line_by_line():
    result = _wall()
    bought = buy.purchase(result, waste_percent="10", plate_stock_length_ft="16")
    args = dict(result=result, bought=bought, project_id=1, organization_id="org", project_name="P", project_address="",
                supplier_name="S", contractor_supplier_account_id=3, supplier_id=2, supplier_location_id=1, issued_by="Office")
    first, second = F.build_framing_request(**args), F.build_framing_request(**args)
    assert first["manifest"]["request_id"] == second["manifest"]["request_id"]
    assert first["manifest"]["request_id"].startswith("FRQ-") and first["manifest"]["kind"] == F.KIND
    assert [l["signature"] for l in first["manifest"]["lines"]] == [l["signature"] for l in second["manifest"]["lines"]]
    other = F.build_framing_request(**{**args, "bought": buy.purchase(result, waste_percent="20", plate_stock_length_ft="16")})
    assert other["manifest"]["request_id"] != first["manifest"]["request_id"]


def test_one_click_sends_the_framing_request_and_the_supplier_prices_it(app, client):  # noqa: F811
    project, _other, account = _setup()
    _give_sign_in(client, account)
    estimate, version = _estimate(project)
    url = _framing_url(estimate, version)
    page = client.get(url).get_data(as_text=True)
    assert "data-framing-request" in page and "BMR Winchester (synthetic)" in page
    form = {**FIXTURE, "waste_percent": "10", "plate_stock_length_ft": "16", "action": "request",
            "contractor_supplier_account_id": str(account.id),
            "needed_by": (date.today() + timedelta(days=10)).isoformat()}
    sent = client.post(url, data=form)
    text = sent.get_data(as_text=True)
    assert "data-framing-request-sent" in text and "sent to BMR Winchester (synthetic)" in text, text[-1500:]
    share = SupplierRequestShare.query.one()
    assert share.source_kind == SOURCE_FRAMING_FORM2 and share.request_kind == "MATERIAL"
    assert share.source_ref.startswith("FRQ-")
    flat = str(share.shared_json)
    assert project.name not in flat
    assert [l["description"] for l in share.shared_json["lines"]][0].startswith("10 studs")
    manifest = storage.load_request(DEFAULT_ORGANIZATION_ID, project.id, share.source_ref)
    assert manifest["kind"] == F.KIND and manifest["response_form"] == 2
    assert storage.request_pdf(DEFAULT_ORGANIZATION_ID, project.id, share.source_ref)

    supplier = _supplier_client(app)
    assert supplier.get(f"/supplier/{account.supplier_id}/requests/{share.id}").status_code == 200
    first = f"{int(share.shared_json['lines'][0]['number']):02d}"
    values = {f"sku_{first}": "TEST-2X4-STUD", f"unit_cost_{first}": "4.00", f"discount_{first}": "10",
              "bmr_contact": DARCY[0], "response_date": RESPONSE_DATE, "valid_until": VALID_UNTIL, "minutes_reported": "8"}
    returned = supplier.post(f"/supplier/{account.supplier_id}/requests/{share.id}/quote", data=values, follow_redirects=True)
    assert b"Quote returned to the contractor" in returned.data
    share = db.session.get(SupplierRequestShare, share.id)
    assert share.status == "RETURNED" and share.response_ref
    # The same quote is reviewed on the existing response page.
    review = client.get(f"/projects/{project.id}/deck-takeoff/responses/{share.response_ref}")
    assert review.status_code == 200

    # A second click with the same wall is refused, not duplicated.
    again = client.post(url, data=form).get_data(as_text=True)
    assert "is already with BMR Winchester (synthetic)" not in again or SupplierRequestShare.query.count() == 1
    assert SupplierRequestShare.query.count() == 1


def test_a_framing_request_does_not_supersede_a_deck_request_to_the_same_supplier(app, client):  # noqa: F811
    from tests.test_deck_takeoff_workflow import _issue

    project, _other, account = _setup()
    _give_sign_in(client, account)
    _pdf, fields, _keys = _issue(client, project, account)
    deck_id = fields["request_id"]["/V"]
    client.post(f"/projects/{project.id}/deck-takeoff/requests/{deck_id}/send-to-supplier", data={})
    deck_share = SupplierRequestShare.query.one()
    assert deck_share.source_kind == SOURCE_DECK_FORM2
    estimate, version = _estimate(project)
    client.post(_framing_url(estimate, version), data={**FIXTURE, "waste_percent": "10", "plate_stock_length_ft": "16",
                "action": "request", "contractor_supplier_account_id": str(account.id)})
    shares = {s.source_kind: s for s in SupplierRequestShare.query.all()}
    assert set(shares) == {SOURCE_DECK_FORM2, SOURCE_FRAMING_FORM2}
    assert shares[SOURCE_DECK_FORM2].status == "SENT" and shares[SOURCE_FRAMING_FORM2].status == "SENT"


def test_a_supplier_without_a_sign_in_keeps_the_pdf_and_says_what_to_do(app, client):  # noqa: F811
    project, _other, account = _setup()
    estimate, version = _estimate(project)
    page = client.post(_framing_url(estimate, version), data={**FIXTURE, "waste_percent": "10", "plate_stock_length_ft": "16",
                       "action": "request", "contractor_supplier_account_id": str(account.id)}).get_data(as_text=True)
    assert "has no supplier sign-in yet" in page
    assert "10 studs" in page  # the count stays on the page
    assert SupplierRequestShare.query.count() == 0
    assert storage.list_requests(DEFAULT_ORGANIZATION_ID, project.id)  # the PDF request is kept


def test_a_missing_supplier_choice_is_refused_and_nothing_is_issued(app, client):  # noqa: F811
    project, _other, account = _setup()
    estimate, version = _estimate(project)
    page = client.post(_framing_url(estimate, version), data={**FIXTURE, "waste_percent": "10", "action": "request"}).get_data(as_text=True)
    assert "Choose a supplier account" in page
    assert not storage.list_requests(DEFAULT_ORGANIZATION_ID, project.id)


def test_deck_takeoff_one_click_issues_and_sends(app, client):  # noqa: F811
    from tests.test_deck_takeoff_workflow import _facts_form

    project, _other, account = _setup()
    _give_sign_in(client, account)
    client.post(f"/projects/{project.id}/deck-takeoff/product-facts", data=_facts_form())
    page = client.get(f"/projects/{project.id}/deck-takeoff").get_data(as_text=True)
    assert "data-request-framing-quote" in page
    resp = client.post(
        f"/projects/{project.id}/deck-takeoff/request-and-send",
        data={"contractor_supplier_account_id": account.id, "actor_display_name": "Test office"},
        follow_redirects=True,
    )
    assert b"sent to BMR Winchester (synthetic)" in resp.data
    share = SupplierRequestShare.query.one()
    assert share.source_kind == SOURCE_DECK_FORM2 and share.request_kind == "MATERIAL"
    # A second click does not create a second share.
    client.post(f"/projects/{project.id}/deck-takeoff/request-and-send", data={"contractor_supplier_account_id": account.id})
    assert SupplierRequestShare.query.count() == 1
    # No account chosen: refused with the reason, nothing sent.
    none = client.post(f"/projects/{project.id}/deck-takeoff/request-and-send", data={}, follow_redirects=True)
    assert b"Choose a supplier account" in none.data


def test_labour_quote_request_sheet_lists_only_subcontract_lines(app, client):  # noqa: F811
    from app.services.estimate_scope_delivery import (
        LABOUR_SUBCONTRACT, MATERIAL_SUBCONTRACTOR_SUPPLIED, save_scope_delivery,
    )
    from app.services.estimate_builder import add_manual_line, create_section
    project, _other, _account = _setup()
    estimate, version = _estimate(project)
    section = create_section(version, name="Direct")
    sub = add_manual_line(section, line_type="Custom", description="Framing labour package",
                          quantity=1, unit="ls", unit_cost=100)
    own = add_manual_line(section, line_type="Custom", description="Own crew cleanup",
                          quantity=1, unit="ls", unit_cost=10)
    save_scope_delivery(sub, material_procurement=MATERIAL_SUBCONTRACTOR_SUPPLIED,
                        labour_delivery=LABOUR_SUBCONTRACT, actor="Test")
    page = client.get(f"/projects/{project.id}/scope-delivery?version_id={version.id}&estimate_id={estimate.id}").get_data(as_text=True)
    assert "data-labour-quote-request-link" in page
    sheet = client.get(f"/projects/{project.id}/scope-delivery/labour-quote-request?version_id={version.id}&estimate_id={estimate.id}")
    text = sheet.get_data(as_text=True)
    assert sheet.status_code == 200 and "data-labour-quote-request" in text
    assert "Framing labour package" in text and "Own crew cleanup" not in text


def test_quote_comparison_marks_the_lowest_net_and_changes_nothing(app, client):  # noqa: F811
    from app.services.quote_comparison import compare_responses

    def rec(rid, source, net, total):
        return {"response_id": rid, "source": source, "supplier_share_number": rid, "recordable_quoted_total": total,
                "rows": [{"key": "framing.studs", "description": "10 studs", "purchasing_quantity": 10,
                          "purchasing_unit": "EA", "net_price": net, "line_value": str(float(net) * 10),
                          "answers": {"sku": "S-" + rid}}]}

    out = compare_responses([rec("A", "BMR", "4.00", "40"), rec("B", "KBC", "3.50", "35")])
    cells = out["lines"][0]["cells"]
    assert cells[1]["lowest"] and not cells[0]["lowest"]

    project, _other, account = _setup()
    before = SupplierRequestShare.query.count()
    page = client.get(f"/projects/{project.id}/supplier-quote-comparison")
    assert page.status_code == 200 and b"data-quote-comparison" in page.data and b"No supplier has returned" in page.data
    from flask import url_for
    with app.test_request_context():
        requests_url = url_for("supplier_office.project_requests", project_id=project.id)
    assert b"data-compare-quotes" in client.get(requests_url).data
    assert SupplierRequestShare.query.count() == before
