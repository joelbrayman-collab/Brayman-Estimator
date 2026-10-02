"""Slice 15: explicit fixture facts and the stair riser-count field."""

from __future__ import annotations

from io import BytesIO

from pypdf import PdfReader

from app import create_app, db
from app.models import Estimate, Project
from app.plan_intelligence.models import PlanDocument
from app.services.construction_model.dimensions import resolve_dimension_chains
from app.services.construction_model.sheet import compose_construction_wave
from app.services.construction_model.views import (
    group_connection_rows,
    group_relationship_rows,
    project_construction_wave,
)
from app.services.organizations import ensure_default_organization
from tests.fixtures.construction_model.complete_deck_fixture import (
    FIXTURE_NAME,
    deck_model,
    detail_requests,
    section_requests,
    sheet_definition,
    sheet_program,
)


def _wave(model=None):
    return project_construction_wave(
        deck_model() if model is None else model,
        sections=section_requests(),
        details=detail_requests(),
    )


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
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def _coordinates(view, identifier):
    element = next(item for item in view.elements if item["id"] == identifier)
    return element["source_geometry"]["coordinates"]


def test_new_fixture_facts_keep_fixture_provenance():
    model = deck_model()
    bearings = [
        item
        for item in model["relationships"]
        if item["id"].startswith("rel-bear-post-") or item["id"].startswith("rel-bear-pier-")
    ]
    assert len(bearings) == 8
    for item in bearings:
        assert item["provenance"]["source"] == "instance_configuration"
        assert item["provenance"]["reference"] == FIXTURE_NAME
    guard = next(item for item in model["connections"] if item["id"] == "connection-guard-gate")
    assert guard["provenance"]["reference"] == FIXTURE_NAME
    stair = model["stair_results"][0]
    assert stair["provenance"]["source"] == "governed_calculation_result"
    assert stair["provenance"]["reference"] == f"{FIXTURE_NAME} stair result"
    assert stair["riser_count"] == 6


def test_riser_count_is_stored_and_drawn_without_being_calculated():
    wave = _wave()
    assert ("riser_count", 6) in wave.stairs[0].facts
    text = _text(_set())
    assert "riser count 6" in text
    assert "riser count 7" not in text


def test_complete_stair_result_is_consumed_as_supplied():
    stair = deck_model()["stair_results"][0]
    assert {
        "rise": 7,
        "run": 11,
        "nosing": 1,
        "tread_count": 5,
        "riser_count": 6,
        "stringer_count": 3,
        "throat": 5,
        "stair_width": 36,
    }.items() <= stair.items()
    facts = dict(_wave().stairs[0].facts)
    assert facts["riser_count"] == 6
    assert facts["tread_count"] == 5
    assert facts["stringer_count"] == 3


def test_remaining_post_and_pier_bearings_are_explicit():
    model = deck_model()
    members = {item["id"]: item for item in model["members"]}
    members.update({item["id"]: item for item in model["supports"]})
    rows = group_relationship_rows(model["relationships"], members, model["connections"])
    seen = {}
    for row in rows:
        for source, target in zip(row["from_ids"], row["to_ids"]):
            seen[(source, target)] = row
    for pair in (
        ("post-1", "beam-front"),
        ("post-2", "beam-front"),
        ("post-3", "beam-back"),
        ("post-4", "beam-back"),
        ("pier-1", "post-1"),
        ("pier-2", "post-2"),
        ("pier-3", "post-3"),
        ("pier-4", "post-4"),
    ):
        assert seen[pair]["bearing"] == "supplied"
        assert seen[pair]["contact"] == "0'-3\""


def test_guard_connection_is_metadata_and_post_cap_keeps_geometry():
    model = deck_model()
    connections = {item["id"]: item for item in model["connections"]}
    assert "connector_geometry" not in connections["connection-guard-gate"]
    assert "connector_geometry" not in connections["connection-stringer-tread"]
    assert connections["connection-post-beam"]["connector_geometry"]["geometry"]["coordinates"]
    members = {item["id"]: item for item in model["members"]}
    rows = {row["connector"]: row for row in group_connection_rows(model["connections"], members)}
    assert rows["fixture gate latch"]["geometry"] == "metadata only"
    assert rows["fixture tread clip"]["geometry"] == "metadata only"
    assert rows["fixture post cap"]["geometry"] == "geometry supplied"
    text = _text(_set())
    assert "GEOMETRY NOT SUPPLIED" in text
    assert "GEOMETRY SUPPLIED" in text
    assert "fixture gate latch" in text


def test_dimension_chains_are_model_references():
    model = deck_model()
    chains = {item["id"]: item for item in resolve_dimension_chains(model)}
    assert chains["pier-spacing-y"]["segments"][-1]["display"] == "8'-0\""
    assert chains["section-height"]["segments"][-1]["display"] == "3'-6\""
    assert chains["guard-height"]["segments"][-1]["display"] == "3'-0\""
    assert chains["baluster-spacing"]["segments"][-1]["display"] == "0'-5\""
    assert chains["stair-opening"]["segments"][-1]["display"] == "3'-0\""
    assert chains["pier-depth"]["segments"][-1]["display"] == "4'-0\""
    for chain in (
        chains["pier-spacing-y"],
        chains["section-height"],
        chains["guard-height"],
        chains["baluster-spacing"],
        chains["stair-opening"],
        chains["pier-depth"],
    ):
        assert chain["provenance"]["reference"] == FIXTURE_NAME
    text = _text(_set())
    assert "PIER SPACING" in text
    assert "SECTION HEIGHT" in text
    assert "GUARD HEIGHT" in text
    assert "STAIR OPENING" in text
    assert "Chain pier-depth" in text
    assert "pier-1 to pier-1  4'-0\"" in text
    assert "Chain baluster-spacing" in text
    assert "baluster-1 to baluster-2  0'-5\"" in text


def test_section_reads_foundation_post_beam_joist_and_decking():
    identifiers = {element["id"] for element in _wave().sections[0].elements}
    assert {"pier-1", "post-1", "beam-front", "joist-1", "deck-3"} <= identifiers
    assert "SECTION HEIGHT" in _text(_set())


def test_complete_fixture_generates():
    result = _set()
    assert result.composed is True
    assert result.view_issues == ()
    assert result.manifest["pages"][-1]["kind"] == "index"
    assert "schedule" in [page["kind"] for page in result.manifest["pages"]]


def test_missing_riser_count_refuses_and_restoring_generates():
    model = deck_model()
    stored = model["stair_results"][0].pop("riser_count")
    refused = _wave(model)
    assert refused.stairs[0].projected is False
    assert any("riser count" in issue.message for issue in refused.stairs[0].issues)
    assert all(key != "riser_count" for key, _value in refused.stairs[0].facts)
    model["stair_results"][0]["riser_count"] = stored
    restored = _wave(model)
    assert restored.stairs[0].projected is True
    assert ("riser_count", 6) in restored.stairs[0].facts


def test_cross_view_geometry_matches():
    wave = _wave()
    plan = _coordinates(wave.plan, "post-1")
    front = _coordinates(wave.front_elevation, "post-1")
    side = _coordinates(wave.side_elevation, "post-1")
    section = _coordinates(wave.sections[0], "post-1")
    assert plan == front == side == section
    stair = _coordinates(wave.stairs[0], "stringer-1")
    elevation = _coordinates(wave.side_elevation, "stringer-1")
    assert stair == elevation
    schedule_posts = {
        row["id"]: row["member_size"]
        for row in wave.schedule.members
        if row["id"].startswith("post-")
    }
    assert schedule_posts == {f"post-{index}": "6x6" for index in range(1, 5)}


def test_fixture_completion_does_not_write_project_plan_or_estimate():
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        before = (Project.query.count(), PlanDocument.query.count(), Estimate.query.count())
        _set()
        after = (Project.query.count(), PlanDocument.query.count(), Estimate.query.count())
        assert before == after == (0, 0, 0)
