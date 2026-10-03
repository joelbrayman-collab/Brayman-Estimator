"""Slice 16: paper-space annotation layout. The model does not move."""

from __future__ import annotations

import copy
from io import BytesIO

from pypdf import PdfReader

from app import create_app, db
from app.models import Estimate, Project
from app.plan_intelligence.models import PlanDocument
from app.services.construction_model.annotations import (
    _segment_hits_rect,
    group_connector_notes,
    place_margin_callouts,
    rectangles_overlap,
    route_leader,
)
from app.services.construction_model.dimensions import resolve_dimension_chains
from app.services.construction_model.sheet import compose_construction_wave
from app.services.organizations import ensure_default_organization
from tests.fixtures.construction_model.complete_deck_fixture import (
    deck_model,
    detail_requests,
    section_requests,
    sheet_definition,
    sheet_program,
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
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def test_annotation_layout_does_not_move_model_geometry():
    model = deck_model()
    before = copy.deepcopy(model["members"])
    chains = {
        item["id"]: item["segments"][-1]["display"]
        for item in resolve_dimension_chains(model)
        if item["segments"]
    }
    result = _set(model)
    assert result.composed is True
    assert model["members"] == before
    after = {
        item["id"]: item["segments"][-1]["display"]
        for item in resolve_dimension_chains(model)
        if item["segments"]
    }
    assert after == chains
    assert chains["pier-spacing-y"] == "8'-0\""
    assert chains["section-height"] == "3'-6\""
    assert chains["pier-depth"] == "4'-0\""
    assert chains["baluster-spacing"] == "0'-5\""


def test_leader_refuses_the_shorter_route_through_a_member():
    blocked = [(40, 90, 160, 110)]
    frame = (0, 0, 240, 220)
    first = route_leader((10, 100), (200, 100), blocked, [], frame)
    second = route_leader((10, 100), (200, 100), blocked, [], frame)
    assert first == second
    assert first
    assert first != ((10, 100), (200, 100))
    assert len(first) >= 3
    for start, end in zip(first, first[1:]):
        assert not _segment_hits_rect(start, end, blocked[0])


def test_connector_notes_stay_outside_primary_geometry():
    member = (120, 140, 280, 180)
    content = (100, 100, 300, 300)
    notes = [
        {
            "id": "connector-1",
            "text": "GEOMETRY NOT SUPPLIED\nfixture joist hanger\nbeam-front, joist-1",
            "anchor_x": 200,
            "anchor_y": 150,
            "kind": "connector",
            "element_ids": ("beam-front", "joist-1"),
        }
    ]
    placed, refused = place_margin_callouts(notes, [member], (0, 0, 520, 520), content)
    assert refused == []
    rect = (
        placed[0]["paper_x"],
        placed[0]["paper_y"],
        placed[0]["paper_x"] + placed[0]["width"],
        placed[0]["paper_y"] + placed[0]["height"],
    )
    assert not rectangles_overlap(rect, member)
    assert not rectangles_overlap(rect, content)
    again, _refused = place_margin_callouts(notes, [member], (0, 0, 520, 520), content)
    assert (again[0]["paper_x"], again[0]["paper_y"]) == (placed[0]["paper_x"], placed[0]["paper_y"])


def test_grouped_connector_notes_keep_member_ids_and_do_not_merge_different_connectors():
    notes = [
        {
            "key": ("GEOMETRY NOT SUPPLIED", "fixture gate latch"),
            "element_ids": ("gate-1",),
            "lines": ["GEOMETRY NOT SUPPLIED", "fixture gate latch"],
            "points": ((1, 2),),
            "anchor": (1, 2),
        },
        {
            "key": ("GEOMETRY NOT SUPPLIED", "fixture gate latch"),
            "element_ids": ("guard-left-a",),
            "lines": ["GEOMETRY NOT SUPPLIED", "fixture gate latch"],
            "points": ((3, 4),),
            "anchor": (3, 4),
        },
        {
            "key": ("GEOMETRY SUPPLIED", "fixture post cap"),
            "element_ids": ("post-1", "beam-front"),
            "lines": ["GEOMETRY SUPPLIED", "fixture post cap"],
            "points": ((5, 6),),
            "anchor": (5, 6),
        },
    ]
    grouped = group_connector_notes(notes)
    assert len(grouped) == 2
    assert grouped[0]["element_ids"] == ("gate-1", "guard-left-a")
    assert grouped[1]["element_ids"] == ("post-1", "beam-front")
    assert grouped[0]["lines"][0] == "GEOMETRY NOT SUPPLIED"
    assert grouped[1]["lines"][0] == "GEOMETRY SUPPLIED"


def test_connector_metadata_and_unresolved_text_stay_visible():
    text = _text(_set())
    assert "GEOMETRY SUPPLIED" in text
    assert "GEOMETRY NOT SUPPLIED" in text
    assert "fixture gate latch" in text
    assert "WIDTH 0'-3\"" in text
    assert "THICKNESS 1/4\"" in text
    assert "BOLT 1/2\"" in text
    assert "PIER DEPTH" in text
    assert "BALUSTER SPACING" in text
    assert "SECTION HEIGHT" in text
    assert "8'-0\"" in text
    assert "WIDTH 12'-0\"" in text
    assert "GUARD HEIGHT" in text
    model = deck_model()
    model["connections"] = [item for item in model["connections"] if item["id"] != "connection-guard-gate"]
    refused = _text(_set(model))
    assert "NOT ISSUED" in refused
    assert "You need to provide this information." in refused
    assert "GEOMETRY NOT SUPPLIED" in refused


def test_annotation_layout_is_deterministic_and_writes_no_records():
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
