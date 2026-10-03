"""Slice 17: blocking is a construction member when the fixture supplies it."""

from __future__ import annotations

import copy
from io import BytesIO

from pypdf import PdfReader

from app import create_app, db
from app.models import Estimate, Project
from app.plan_intelligence.models import PlanDocument
from app.services.construction_model import assess_construction_model, project_construction_wave
from app.services.construction_model.sheet import compose_construction_wave
from app.services.construction_model.views import group_member_rows
from app.services.organizations import ensure_default_organization
from tests.fixtures.construction_model.complete_deck_fixture import (
    FIXTURE_NAME,
    deck_model,
    detail_requests,
    section_requests,
    sheet_definition,
    sheet_program,
)

_ABSENT = {
    "ledger",
    "landing",
    "hinge",
    "bottom_rail",
    "guard_post",
}


def _set(model=None):
    return compose_construction_wave(
        deck_model() if model is None else model,
        sheet_definition(),
        sections=section_requests(),
        details=detail_requests(),
        sheet_program=sheet_program(),
    )


def _text(result) -> str:
    reader = PdfReader(BytesIO(result.pdf_bytes))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _pages(result) -> list:
    reader = PdfReader(BytesIO(result.pdf_bytes))
    return [page.extract_text() or "" for page in reader.pages]


def _without_blocking(model):
    changed = copy.deepcopy(model)
    identifiers = {item["id"] for item in changed["members"] if item.get("role") == "blocking"}
    changed["members"] = [item for item in changed["members"] if item["id"] not in identifiers]
    changed["relationships"] = [
        item
        for item in changed["relationships"]
        if item.get("from_id") not in identifiers and item.get("to_id") not in identifiers
    ]
    for chain in changed.get("dimension_chains") or []:
        chain["references"] = [item for item in chain.get("references") or [] if item not in identifiers]
    return changed


def test_blocking_is_a_member_with_fixture_provenance():
    assessment = assess_construction_model(deck_model())
    assert assessment.complete is True
    members = [item for item in assessment.accepted["members"] if item["role"] == "blocking"]
    assert len(members) == 18
    for member in members:
        assert member["member_size"] == "2x8"
        assert member["material_id"] == "joist-stock"
        assert member["section_width"] > 0
        assert member["section_depth"] > 0
        assert member["geometry"]["kind"] == "segment"
        assert len(member["geometry"]["coordinates"]) == 2
        assert member["provenance"]["source"] == "instance_configuration"
        assert member["provenance"]["reference"] == FIXTURE_NAME


def test_blocking_relationships_name_the_members_they_fasten():
    assessment = assess_construction_model(deck_model())
    member_ids = {item["id"] for item in assessment.accepted["members"]}
    relationships = [
        item
        for item in assessment.accepted["relationships"]
        if str(item["id"]).startswith("rel-fasten-blocking-")
    ]
    assert len(relationships) == 36
    for item in relationships:
        assert item["kind"] == "fastened_to"
        assert item["from_id"].startswith("blocking-")
        assert item["from_id"] in member_ids
        assert item["to_id"] in member_ids
        assert item["to_id"].startswith("joist-") or item["to_id"].startswith("rim-")
        assert item["provenance"]["source"] == "instance_configuration"
        assert item["provenance"]["reference"] == FIXTURE_NAME


def test_blocking_is_the_same_member_on_the_plan_the_section_and_the_schedule():
    wave = project_construction_wave(deck_model(), sections=section_requests(), details=detail_requests())
    assert wave.projected is True
    plan_ids = {item["id"] for item in wave.plan.elements if item.get("role") == "blocking"}
    assert len(plan_ids) == 18
    section = wave.sections[0]
    assert section.projected is True
    section_ids = {item["id"] for item in section.elements if item.get("role") == "blocking"}
    assert section_ids == {f"blocking-{index}" for index in range(1, 10)}
    grouped = group_member_rows(wave.schedule.members, "imperial")
    blocking = [row for row in grouped if row["role"] == "blocking"]
    assert len(blocking) == 1
    assert blocking[0]["quantity"] == 18
    assert blocking[0]["member_size"] == "2x8"
    assert set(blocking[0]["member_ids"]) == plan_ids
    result = _set()
    assert result.composed is True
    pages = _pages(result)
    framing = next(page for page in pages if "Framing Plan" in page)
    section_page = next(page for page in pages if "Section A" in page and "DRAWING INDEX" not in page)
    schedule = "\n".join(page for page in pages if "MEMBER SCHEDULE" in page or "blocking-" in page)
    assert "BLOCKING" in framing
    assert "BLOCKING" in section_page
    assert "blocking" in schedule
    assert "blocking-1 to blocking-18" in schedule
    elevation = next(page for page in pages if "Front Elevation" in page)
    assert "BLOCKING" not in elevation


def test_blocking_adds_no_dimension_and_no_unsupported_fact():
    model = deck_model()
    roles = {item["role"] for item in model["members"]}
    assert "blocking" in roles
    assert roles.isdisjoint(_ABSENT)
    for chain in model["dimension_chains"]:
        assert not any(str(item).startswith("blocking-") for item in chain["references"])
    by_id = {item["id"]: item for item in model["connections"]}
    for identifier in (
        "connection-stringer-tread",
        "connection-beam-joist",
        "connection-stair-header",
        "connection-guard-gate",
    ):
        assert "connector_geometry" not in by_id[identifier]


def test_removing_blocking_omits_it_and_restoring_it_draws_it():
    removed_model = _without_blocking(deck_model())
    removed_assessment = assess_construction_model(removed_model)
    assert removed_assessment.complete is True
    assert not any(item["role"] == "blocking" for item in removed_assessment.accepted["members"])
    removed = _set(removed_model)
    assert removed.composed is True
    removed_text = _text(removed)
    assert "BLOCKING" not in removed_text
    assert "You need to provide this information." not in removed_text
    restored = _set(deck_model())
    assert restored.composed is True
    assert "BLOCKING" in _text(restored)


def test_blocking_writes_no_project_plan_or_estimate():
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        before = (Project.query.count(), PlanDocument.query.count(), Estimate.query.count())
        first = _set()
        second = _set()
        after = (Project.query.count(), PlanDocument.query.count(), Estimate.query.count())
    assert before == after == (0, 0, 0)
    assert first.composed is True
    assert first.manifest["pdf_sha256"] == second.manifest["pdf_sha256"]
