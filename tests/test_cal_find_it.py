"""Cal Assistant, Phase 1 — Find It (Joel, 17 Oct 2026). Synthetic data only.

Cal reads the organization's own records and returns links the user can already open.
No external AI, no invented answers, no database change, no orders, approvals, messages
or schedule moves. Organization isolation, the Company Management grant, ambiguous
project names, missing records, destinations, signed-out access and the existing Help.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
from sqlalchemy import event

from app import db
from app.models import Client, Project
from app.models.organization import Organization
from app.services.estimates import create_estimate
from app.services.organizations import DEFAULT_ORGANIZATION_ID
from tests.auth_fixtures import ensure_office_user
from tests.test_supplier_hub import _concrete_order, _fresh_login_per_request  # noqa: F401
from tests.test_deck_takeoff_workflow import _project, app, client  # noqa: F401

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "app/static/branding/Cal_Assistant_Approved_Identity_2026-10-17.png"
MASTER_SHA = "d8857f1bfef06c709390e8eaedfe437aea49983236c79843ee7845d561617e87"


def _find(client, q):
    response = client.get("/cal/find", query_string={"q": q})
    assert response.status_code == 200, response.data[:300]
    assert response.headers["Content-Type"].startswith("application/json")
    return response.get_json()


def _titles(data):
    return [item["title"] for group in data["groups"] for item in group["items"]]


def _urls(data):
    return [item["url"] for group in data["groups"] for item in group["items"]]


def _other_org():
    org = Organization(id="ORG-CAL-2", legal_name="Other Builder Ltd. (synthetic)", display_name="Other Builder",
                       primary_address="1 Elsewhere Rd", default_region="Ontario", currency="CAD",
                       tax_jurisdiction="Ontario (HST 13%)", is_active=True)
    db.session.add(org)
    db.session.commit()
    return org


@pytest.fixture
def harbour(app):
    ensure_office_user()
    deck = _project("Harbour Lane Pool Deck")
    deck.client.name = "Morgan Ellis"
    deck.address = "48 Harbour Lane, Merrickville, ON"
    fence = _project("Harbour Lane Fence")
    porch = _project("Rideau Street Porch")
    db.session.commit()
    estimate = create_estimate(project_id=deck.id, estimate_number="HL-001", title="Harbour Lane Pool Deck")
    other = _other_org()
    foreign = _project("Harbour Lane Garage", organization_id=other.id)
    create_estimate(project_id=foreign.id, estimate_number="HL-999", title="Foreign estimate", organization_id=other.id)
    return {"deck": deck, "fence": fence, "porch": porch, "estimate": estimate, "foreign": foreign}


# ------------------------------------------------------------------ identity and the header

def test_the_header_shows_the_exact_approved_cal_identity_and_opens_only_when_clicked(app, client, harbour):
    assert hashlib.sha256(MASTER.read_bytes()).hexdigest() == MASTER_SHA
    page = client.get("/").get_data(as_text=True)
    assert 'id="cal-launch"' in page and "img/cal-assistant/cal-64.png" in page
    assert 'id="cal-panel" role="dialog" aria-modal="false" aria-labelledby="cal-panel-title" hidden' in page
    assert "Your CalibraytAI Assistant" in page and "It does not change anything." in page
    for size in (64, 128):
        assert client.get(f"/static/img/cal-assistant/cal-{size}.png").status_code == 200
    # The existing Help and its voice control are still on the page, unchanged.
    assert 'class="contextual-help' in page and "data-help-voice" in page and "js/contextual_help.js" in page


def test_signed_out_visitors_get_no_cal_and_the_endpoint_sends_them_to_sign_in(app):
    anonymous = app.test_client()
    response = anonymous.get("/cal/find?q=harbour")
    assert response.status_code == 302 and "/login" in response.headers["Location"]
    page = anonymous.get("/login").get_data(as_text=True)
    assert 'id="cal-launch"' not in page


def test_the_endpoint_only_answers_get(app, client, harbour):
    assert client.post("/cal/find", data={"q": "harbour"}).status_code == 405


# ------------------------------------------------------------------ projects, ambiguity, isolation

def test_one_project_by_client_name_with_its_records_as_shortcuts(app, client, harbour):
    data = _find(client, "Morgan Ellis")
    assert data["status"] == "results"
    assert _titles(data)[0] == "Harbour Lane Pool Deck"
    assert f"/projects/{harbour['deck'].id}" in _urls(data)
    shortcuts = next(g for g in data["groups"] if g["title"] == "On this project")
    assert shortcuts["items"][0]["title"] == "Estimates"


def test_an_ambiguous_project_name_asks_which_one_and_never_shows_another_company(app, client, harbour):
    data = _find(client, "harbour lane")
    assert data["status"] == "ambiguous"
    assert "More than one project matches “harbour lane”" in data["message"]
    titles = _titles(data)
    assert titles == ["Harbour Lane Fence", "Harbour Lane Pool Deck"]
    assert "Harbour Lane Garage" not in titles


def test_ambiguity_with_a_destination_says_which_projects_have_that_record(app, client, harbour):
    data = _find(client, "harbour lane estimate")
    assert data["status"] == "ambiguous"
    details = {i["title"]: i["detail"] for g in data["groups"] for i in g["items"]}
    assert details["Harbour Lane Pool Deck"].endswith("1 estimates")
    assert details["Harbour Lane Fence"].endswith("no estimates yet")
    deck = next(i for g in data["groups"] for i in g["items"] if i["title"] == "Harbour Lane Pool Deck")
    assert deck["url"] == f"/estimates/{harbour['estimate'].id}"


def test_a_project_and_a_destination_open_that_record(app, client, harbour):
    data = _find(client, "pool deck estimate")
    assert data["status"] == "results"
    assert _titles(data) == ["HL-001 — Harbour Lane Pool Deck"]
    assert _urls(data) == [f"/estimates/{harbour['estimate'].id}"]


def test_another_companys_record_number_is_not_found(app, client, harbour):
    data = _find(client, "HL-999")
    assert data["status"] == "none"
    assert "Cal could not find anything" in data["message"]
    assert _find(client, "HL-001")["groups"][0]["items"][0]["url"] == f"/estimates/{harbour['estimate'].id}"
    assert _find(client, "harbour lane garage")["status"] == "none"


# ------------------------------------------------------------------ missing records and plain answers

def test_nothing_found_is_said_plainly_with_no_invented_answer(app, client, harbour):
    data = _find(client, "zzqx unicorn ranch")
    assert data["status"] == "none" and data["groups"] == []
    assert data["message"] == "Cal could not find anything that matches “zzqx unicorn ranch” in records you can open."
    assert "record number" in data["hint"]


def test_a_project_without_the_record_says_so_and_offers_the_project(app, client, harbour):
    data = _find(client, "rideau porch contract")
    assert data["message"] == "Rideau Street Porch has no contracts yet."
    assert _urls(data) == [f"/projects/{harbour['porch'].id}"]


def test_an_unknown_project_with_a_destination_is_reported(app, client, harbour):
    data = _find(client, "maple ridge proposal")
    assert data["status"] == "none"
    assert data["message"] == "No project you can open matches “maple ridge”."


def test_every_example_in_the_panel_gives_an_answer(app, client, harbour):
    from app.presentation.cal_copy import CAL_EXAMPLES

    for example in CAL_EXAMPLES:
        data = _find(client, example)
        assert data["groups"], example


def test_an_empty_query_explains_what_to_type(app, client, harbour):
    data = _find(client, "   ")
    assert data["status"] == "empty" and "Harbour Lane drawings" in data["message"]


# ------------------------------------------------------------------ destinations

def test_company_wide_destinations_and_calendar_links(app, client, harbour):
    assert "/estimates/" in _urls(_find(client, "estimates"))
    assert "/proposals" in _urls(_find(client, "proposals"))
    assert "/schedule" in _urls(_find(client, "company calendar"))
    data = _find(client, "pool deck schedule")
    assert _urls(data) == [f"/schedule?project_id={harbour['deck'].id}"]
    assert "/deliveries" in _urls(_find(client, "deliveries"))


def test_tools_come_from_the_menu_and_respect_company_management(app, client, harbour):
    data = _find(client, "stair calculator")
    assert "/calculators/stairs" in _urls(data)
    # The office test user has no Company Management grant: Attention is not offered.
    assert "/company-attention" not in " ".join(_urls(_find(client, "attention")))


def test_existing_help_topics_link_to_their_page(app, client, harbour):
    data = _find(client, "how do I use what we pay")
    help_group = next(g for g in data["groups"] if g["title"] == "Help")
    assert help_group["items"][0]["url"].startswith("/cost-library/#help-cost_library")
    for item in help_group["items"]:
        assert client.get(item["url"].split("#")[0]).status_code == 200


def test_supplier_quotation_purchase_order_and_delivery_open_the_supplier_requests(app, client):
    project, tomlinson, _darcy, _user, order = _concrete_order(app, client)
    share = order.share
    quotes = _find(client, f"{project.name} quote")
    assert f"/projects/{project.id}/supplier-requests#share-{share.id}" in _urls(quotes)
    assert any(t.startswith("Concrete request") for t in _titles(quotes))
    orders = _find(client, f"{project.name} purchase order")
    assert _urls(orders) == [f"/projects/{project.id}/supplier-requests#share-{share.id}"]
    deliveries = _find(client, f"{project.name} delivery")
    assert _titles(deliveries) == [f"Delivery — {order.number}"]
    by_number = _find(client, order.number)
    assert by_number["groups"][0]["items"][0]["title"] == f"Purchase order {order.number}"
    for url in set(_urls(quotes) + _urls(orders)):
        assert client.get(url.split("#")[0]).status_code == 200


def test_drawings_and_plans_for_a_project(app, client):
    from tests.test_deck_takeoff_workflow import _setup

    project, _other, _account = _setup()
    client.post(f"/projects/{project.id}/drawings/generate", data={"actor_display_name": "Test office"})
    data = _find(client, "linda bushel drawings")
    assert data["status"] == "results", data
    assert any(u.startswith(f"/projects/{project.id}/drawings/") for u in _urls(data))
    for url in _urls(data):
        assert client.get(url).status_code == 200
    empty = _find(client, "another synthetic deck plans")
    assert empty["message"] == "Another synthetic deck has no drawings and project plans yet."


# ------------------------------------------------------------------ read-only

def test_find_it_never_writes(app, client, harbour):
    writes = []

    def record(conn, cursor, statement, *args):
        if statement.lstrip().split(" ", 1)[0].upper() in ("INSERT", "UPDATE", "DELETE"):
            writes.append(statement)

    event.listen(db.engine, "before_cursor_execute", record)
    try:
        for q in ("harbour lane", "pool deck estimate", "HL-001", "deliveries", "stair calculator",
                  "how do I use what we pay", "nothing at all here", "rideau porch contract"):
            _find(client, q)
    finally:
        event.remove(db.engine, "before_cursor_execute", record)
    # Signing in may touch the user row; Cal itself writes nothing.
    assert [w for w in writes if "users" not in w.lower()] == []


def test_cal_uses_no_external_service():
    source = (ROOT / "app/services/cal_find.py").read_text() + (ROOT / "app/static/js/cal_assistant.js").read_text()
    for marker in ("http://", "https://", "requests.", "openai", "anthropic", "urllib"):
        assert marker not in source
