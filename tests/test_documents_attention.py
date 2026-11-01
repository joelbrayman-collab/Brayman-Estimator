"""Documents in "What needs your attention": only confirmed dates on the current version of an active document, in
the reminder window or passed; proposed dates only as one roll-up; viewer permissions respected. Synthetic data."""

from __future__ import annotations

from datetime import timedelta

import pytest

from app.models.documents import (
    CONTEXT_COMPANY,
    CONTEXT_EQUIPMENT,
    CONTEXT_PERSON,
    CONTEXT_SUBCONTRACTOR,
    DATE_EXPIRES,
    DATE_INSPECTION_DUE,
    DATE_ISSUED,
    DATE_WARRANTY_ENDS,
)
from app.models.user import UserMembership
from app.services.documents import ingest
from app.services.documents.attention import document_attention_items
from app.services.documents.ingest import Actor, prepare_upload
from app.services.equipment import create_equipment
from app.services.needs_attention import assemble
from tests.documents_support import ORG, TODAY, app, file_pdf, make_world, text_pdf  # noqa: F401


@pytest.fixture
def world(app):
    return make_world(crew=True)


def _titles(items):
    """Per-document date items (the roll-ups have no " — ")."""
    return [i["title"] for i in items if i["kind"] == "documents" and " — " in i["title"]]


def test_confirmed_expiry_within_window_or_passed_is_listed(world):
    actor = Actor.of(world["staff"])
    wsib = file_pdf(world["staff"], CONTEXT_SUBCONTRACTOR, world["sub"].id, "WSIB clearance.pdf", "WSIB")
    ingest.enter_date(wsib, actor, DATE_EXPIRES, TODAY + timedelta(days=12))
    late = file_pdf(world["staff"], CONTEXT_COMPANY, None, "liability insurance.pdf", "COI")
    ingest.enter_date(late, actor, DATE_EXPIRES, TODAY - timedelta(days=3))
    far = file_pdf(world["staff"], CONTEXT_COMPANY, None, "licence.pdf", "Licence")
    ingest.enter_date(far, actor, DATE_EXPIRES, TODAY + timedelta(days=90))
    issued = file_pdf(world["staff"], CONTEXT_COMPANY, None, "permit.pdf", "Permit")
    ingest.enter_date(issued, actor, DATE_ISSUED, TODAY)  # not an action date
    items = document_attention_items(ORG, world["staff"], TODAY)
    by_title = {i["title"]: i for i in items}
    assert "WSIB clearance — expires" in by_title and "liability insurance — expired" in by_title
    assert not any(t.startswith("licence") or t.startswith("permit") for t in by_title)
    wsib_item = by_title["WSIB clearance — expires"]
    assert wsib_item["due_date"] == TODAY + timedelta(days=12) and wsib_item["severity"] == "soon"
    assert wsib_item["status"] == "In 12 days" and "Acme Framing" in wsib_item["who"]
    assert wsib_item["url"] == f"/documents/{wsib.public_id}" and wsib_item["href"] == wsib_item["url"]
    assert by_title["liability insurance — expired"]["severity"] == "overdue"
    # A longer reminder brings the far date in.
    ingest.enter_date(far, actor, DATE_EXPIRES, TODAY + timedelta(days=90), remind_days_before=120, reason="Longer")
    assert any(t.startswith("licence") for t in _titles(document_attention_items(ORG, world["staff"], TODAY)))


def test_equipment_inspection_and_warranty(world):
    actor = Actor.of(world["staff"])
    item = create_equipment(ORG, world["staff"], {"name": "Kubota KX040", "category": "HEAVY_EQUIPMENT"})
    report = file_pdf(world["staff"], CONTEXT_EQUIPMENT, item.id, "annual inspection.pdf", "Inspection")
    ingest.enter_date(report, actor, DATE_INSPECTION_DUE, TODAY + timedelta(days=5))
    warranty = file_pdf(world["staff"], CONTEXT_EQUIPMENT, item.id, "warranty.pdf", "Warranty")
    ingest.enter_date(warranty, actor, DATE_WARRANTY_ENDS, TODAY)
    titles = _titles(document_attention_items(ORG, world["staff"], TODAY))
    assert "annual inspection — inspection due" in titles and "warranty — warranty ends today" in titles


def test_proposed_dates_only_create_one_roll_up(world):
    file_pdf(world["staff"], CONTEXT_COMPANY, None, "a.pdf", "Expires 2026-11-05")
    file_pdf(world["staff"], CONTEXT_COMPANY, None, "b.pdf", "Valid until 2026-11-06")
    items = document_attention_items(ORG, world["staff"], TODAY)
    assert [i["title"] for i in items if "dates to confirm" in i["title"]] == ["2 documents have dates to confirm"]
    assert not any("expires" in i["title"] for i in items)
    roll_up = next(i for i in items if "dates to confirm" in i["title"])
    assert "dates=proposed" in roll_up["url"]


def test_archived_document_and_new_version_stop_the_item(world):
    actor = Actor.of(world["staff"])
    doc = file_pdf(world["staff"], CONTEXT_COMPANY, None, "insurance.pdf", "Insurance")
    ingest.enter_date(doc, actor, DATE_EXPIRES, TODAY + timedelta(days=3))
    assert _titles(document_attention_items(ORG, world["staff"], TODAY)) == ["insurance — expires"]
    ingest.add_version(doc, actor, prepare_upload("insurance-2027.pdf", text_pdf("Renewed")))
    assert _titles(document_attention_items(ORG, world["staff"], TODAY)) == []
    ingest.enter_date(doc, actor, DATE_EXPIRES, TODAY + timedelta(days=3))
    ingest.archive(doc, actor, "Cancelled policy")
    assert _titles(document_attention_items(ORG, world["staff"], TODAY)) == []


def test_people_documents_only_for_people_administrators_and_never_for_crew(world):
    membership = UserMembership.query.filter_by(user_id=world["staff"].id, organization_id=ORG).one()
    ticket = file_pdf(world["owner"], CONTEXT_PERSON, membership.id, "first aid ticket.pdf", "First aid")
    ingest.enter_date(ticket, Actor.of(world["owner"]), DATE_EXPIRES, TODAY + timedelta(days=7))
    assert _titles(document_attention_items(ORG, world["owner"], TODAY)) == ["first aid ticket — expires"]
    assert _titles(document_attention_items(ORG, world["staff"], TODAY)) == []
    assert document_attention_items(ORG, world["crew"], TODAY) == []


def test_review_roll_up_for_suggested_types(world):
    from app.services.documents.contexts import resolve_context

    ingest.file_document(ORG, Actor.of(world["staff"]), blob=prepare_upload("wsib.pdf", text_pdf("x")),
                         context=resolve_context(ORG, CONTEXT_COMPANY), type_confirmed=False)
    titles = [i["title"] for i in document_attention_items(ORG, world["staff"], TODAY)]
    assert "1 document to review" in titles


def test_wired_into_what_needs_your_attention(world):
    doc = file_pdf(world["staff"], CONTEXT_SUBCONTRACTOR, world["sub"].id, "WSIB clearance.pdf", "WSIB")
    ingest.enter_date(doc, Actor.of(world["staff"]), DATE_EXPIRES, TODAY - timedelta(days=1))
    result = assemble(ORG, world["staff"], today=TODAY, include_company_facts=False)
    item = next(i for i in result["items"] if i["kind"] == "documents" and i["due_date"])
    assert item["what"] == "WSIB clearance — expired" and item["urgency"] == "overdue"
    assert result["items"][0] is item  # overdue sorts first
    assert assemble(ORG, world["crew"], today=TODAY)["hidden"] is True
