"""Construction relationships, supplied bearing, and connection geometry."""

from __future__ import annotations

from copy import deepcopy
from io import BytesIO

from pypdf import PdfReader

from app import create_app, db
from app.models import Estimate, Project
from app.plan_intelligence.models import PlanDocument
from app.services.construction_model import assess_construction_model, compose_construction_wave, project_construction_wave
from app.services.construction_model.completeness import CODE_CONFLICTING_GEOMETRY
from app.services.construction_model.sheet import _relationship_note, _schedule_lines
from app.services.organizations import ensure_default_organization
from tests.fixtures.construction_model.complete_deck_fixture import (
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


def _accepted():
    assessment = assess_construction_model(deck_model())
    assert assessment.complete is True
    return assessment.accepted


def test_relationship_can_be_stored_with_supplied_bearing():
    accepted = _accepted()
    stored = next(item for item in accepted["relationships"] if item["id"] == "rel-bear-stringer-2-tread-3")
    assert stored["kind"] == "bears_on"
    assert stored["from_id"] == "stringer-2"
    assert stored["to_id"] == "tread-3"
    assert stored["bearing_surface"]["kind"] == "segment"
    assert stored["bearing_depth"] > 0
    assert stored["provenance"]["source"] == "instance_configuration"
    post = next(item for item in accepted["relationships"] if item["id"] == "rel-bear-post-1-beam-front")
    assert post["kind"] == "bears_on"
    assert post["from_id"] == "post-1"
    assert post["to_id"] == "beam-front"
    assert post["bearing_surface"]["coordinates"]


def test_relationship_requires_explicit_participants():
    payload = deck_model()
    payload["relationships"] = [{"id": "rel-open", "kind": "bears_on", "to_id": "beam-front"}]
    assessment = assess_construction_model(payload)
    assert assessment.complete is False
    assert any(issue.field.endswith("from_id") for issue in assessment.issues)


def test_relationship_does_not_arise_from_proximity():
    payload = deck_model()
    payload["relationships"] = []
    assessment = assess_construction_model(payload)
    assert assessment.complete is True
    assert assessment.accepted["relationships"] == []


def test_contradictory_bearing_geometry_is_refused_without_moving_members():
    payload = deck_model()
    original = deepcopy(payload["members"])
    relationship = next(item for item in payload["relationships"] if item["id"] == "rel-bear-post-1-beam-front")
    relationship["bearing_surface"]["coordinates"][0]["z"] = 100
    assessment = assess_construction_model(payload)
    assert assessment.complete is False
    assert assessment.generation_permitted is False
    assert any(issue.code == CODE_CONFLICTING_GEOMETRY for issue in assessment.issues)
    assert payload["members"] == original


def test_stringer_tread_detail_reads_the_relationship_bearing():
    accepted = _accepted()
    detail = next(item for item in _wave().details if item.view_id == "stringer-tread")
    assert detail.projected is True
    assert [element["id"] for element in detail.elements] == ["stringer-2", "tread-3"]
    relationship = next(item for item in accepted["relationships"] if item["id"] == "rel-bear-stringer-2-tread-3")
    seat = relationship["bearing_surface"]["coordinates"]
    u0 = min(point["y"] for point in seat)
    u1 = max(point["y"] for point in seat)
    v_seat = seat[0]["z"]
    stringer = detail.elements[0]
    interior = [
        point
        for point in stringer["profile_geometry"]["coordinates"]
        if u0 + 0.02 < point["u"] < u1 - 0.02
    ]
    assert interior
    assert max(point["v"] for point in interior) <= v_seat + 0.02
    assert stringer.get("bearing_lines")


def test_post_beam_detail_reads_the_relationship_and_does_not_invent_a_connector():
    detail = next(item for item in _wave().details if item.view_id == "post-beam")
    assert detail.projected is True
    assert [element["id"] for element in detail.elements] == ["post-1", "beam-front"]
    post = detail.elements[0]
    assert post.get("bearing_lines")
    assert len(post["bearing_lines"][0]) == 2
    connection = next(item for item in _accepted()["connections"] if item["id"] == "connection-post-beam")
    assert connection["connector"] == "fixture post cap"
    assert "geometry" not in connection
    assert "bolt_diameter" not in connection
    assert all(element["id"] in {"post-1", "beam-front"} for element in detail.elements)


def test_connection_geometry_stays_separate_from_metadata():
    payload = deck_model()
    payload["connections"][0]["geometry"] = {
        "kind": "segment",
        "coordinates": [
            {"x": 1, "y": 1, "z": 23 / 12},
            {"x": 1.25, "y": 1, "z": 23 / 12},
        ],
    }
    payload["connections"][0]["bolt_count"] = 2
    accepted = assess_construction_model(payload).accepted
    stored = accepted["connections"][0]
    assert stored["connector"] == "fixture post cap"
    assert stored["geometry"]["kind"] == "segment"
    assert stored["bolt_count"] == 2
    untouched = next(item for item in accepted["connections"] if item["id"] == "connection-stringer-tread")
    assert "geometry" not in untouched


def test_section_consumes_relationships_already_in_the_cut():
    accepted = _accepted()
    section = _wave().sections[0]
    identifiers = {element["id"] for element in section.elements}
    assert {"pier-1", "post-1", "beam-front", "joist-1", "deck-3"} <= identifiers
    assert "stringer-2" not in identifiers
    note = _relationship_note(accepted, section.elements)
    assert "pier supports post" in note
    assert "post bears on beam" in note
    assert "beam supports joist" in note
    assert "joist supports decking" in note
    assert "stringer" not in note


def test_schedule_consumes_relationships_without_becoming_a_takeoff():
    lines = "\n".join(text for _font, text in _schedule_lines(_wave().schedule))
    assert "RELATIONSHIP" in lines
    assert "bears_on" in lines
    assert "stringer" in lines and "tread" in lines
    assert "bearing supplied" in lines
    assert "bearing not supplied" in lines
    assert "metadata only" in lines
    assert "geometry supplied" not in lines
    assert "$" not in lines
    lowered = lines.lower()
    assert "price" not in lowered
    assert "estimate" not in lowered


def test_relationship_uncertainty_stays_uncertainty():
    payload = deck_model()
    relationship = next(item for item in payload["relationships"] if item["id"] == "rel-bear-stringer-2-tread-3")
    relationship["uncertainty"] = "Bearing depth is field-check only."
    accepted = assess_construction_model(payload)
    assert accepted.complete is True
    stored = next(item for item in accepted.accepted["relationships"] if item["id"] == "rel-bear-stringer-2-tread-3")
    assert stored["uncertainty"] == "Bearing depth is field-check only."
    detail = next(item for item in _wave(payload).details if item.view_id == "stringer-tread")
    assert any(note["note"] == "Bearing depth is field-check only." for note in detail.uncertainty)


def test_missing_bearing_names_the_fact_and_missing_geometry_adds_no_connector():
    payload = deck_model()
    for item in payload["relationships"]:
        if item["id"] == "rel-bear-post-1-beam-front":
            item.pop("bearing_surface")
            item.pop("bearing_location")
            item.pop("bearing_depth")
    wave = _wave(payload)
    detail = next(item for item in wave.details if item.view_id == "post-beam")
    assert detail.projected is False
    assert any("bearing surface" in issue.fact.lower() for issue in detail.issues)
    assert detail.elements == ()


def test_relationship_views_do_not_write_project_plan_or_estimate():
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        before = (Project.query.count(), PlanDocument.query.count(), Estimate.query.count())
        result = compose_construction_wave(
            deck_model(),
            sheet_definition(),
            sections=section_requests(),
            details=detail_requests(),
            sheet_program=sheet_program(),
        )
        text = "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(result.pdf_bytes)).pages)
        after = (Project.query.count(), PlanDocument.query.count(), Estimate.query.count())
        assert before == after == (0, 0, 0)
    assert result.composed is True
    assert "RELATIONSHIP" in text
    assert "fixture post cap" in text
    assert "BEARING" in text
