"""Deck component vocabulary, partial members, and explicit relationships."""

from __future__ import annotations

from app import create_app, db
from app.models import Estimate, Project
from app.plan_intelligence.models import PlanDocument
from app.services.construction_model import assess_construction_model, project_construction_wave
from app.services.construction_model.completeness import CODE_CONFLICTING_GEOMETRY
from app.services.construction_model.views import VIEW_REQUIREMENTS
from app.services.organizations import ensure_default_organization


def _provenance():
    return {"source": "project_input", "reference": "component test"}


def _point(x, y, z=None):
    coordinate = {"x": x, "y": y}
    if z is not None:
        coordinate["z"] = z
    return {"kind": "point", "coordinates": [coordinate]}


def _segment(start, end):
    return {
        "kind": "segment",
        "coordinates": [
            {"x": start[0], "y": start[1], "z": start[2]},
            {"x": end[0], "y": end[1], "z": end[2]},
        ],
    }


def _model(**overrides):
    payload = {
        "structure_class": "deck",
        "project_document_status": "preliminary_construction_drawing",
        "measurement_system": "imperial",
        "levels": [
            {
                "id": "walk",
                "name": "Finished walking surface",
                "elevation": 1,
                "provenance": _provenance(),
            }
        ],
        "members": [
            {
                "id": "joist-1",
                "role": "joist",
                "member_size": "2x8",
                "material_id": "joist-stock",
                "geometry": _point(4, 8),
                "provenance": _provenance(),
            },
            {
                "id": "beam-a",
                "role": "beam",
                "member_size": "2x10",
                "geometry": _segment((0, 1, 2), (10, 1, 2)),
                "provenance": _provenance(),
            },
            {
                "id": "post-a",
                "role": "post",
                "member_size": "6x6",
                "construction_status": "field_verification_required",
                "provenance": _provenance(),
            },
            {
                "id": "guard-a",
                "role": "guard",
                "provenance": _provenance(),
            },
            {
                "id": "gate-a",
                "role": "gate",
                "provenance": _provenance(),
            },
            {
                "id": "stringer-a",
                "role": "stringer",
                "geometry": _segment((0, 0, 0), (0, 3, 2)),
                "provenance": _provenance(),
            },
            {
                "id": "deck-a",
                "role": "decking",
                "member_size": "5/4x6",
                "provenance": _provenance(),
            },
        ],
        "supports": [
            {
                "id": "pier-a",
                "kind": "pier",
                "geometry": _point(0, 1, 0),
                "provenance": _provenance(),
            }
        ],
        "materials": [{"id": "joist-stock", "name": "2x8 lumber"}],
        "relationships": [
            {
                "id": "pier-post",
                "kind": "supports",
                "from_id": "pier-a",
                "to_id": "post-a",
            },
            {
                "id": "guard-edge",
                "kind": "protects",
                "from_id": "guard-a",
                "to_id": "deck-a",
            },
        ],
        "connections": [
            {
                "id": "post-beam",
                "participant_ids": ["post-a", "beam-a"],
                "connection_type": "bearing",
                "connector": "test-connector",
                "fastener": "test-fastener",
                "quantity": 4,
                "provenance": _provenance(),
            }
        ],
        "stair_results": [
            {
                "id": "stair-a",
                "throat": 5,
                "member_ids": ["stringer-a"],
                "provenance": _provenance(),
            }
        ],
    }
    payload.update(overrides)
    return payload


def test_generic_deck_components_can_be_represented():
    accepted = assess_construction_model(_model()).accepted
    roles = {item["role"] for item in accepted["members"]}
    assert {"joist", "beam", "post", "guard", "gate", "stringer", "decking"}.issubset(roles)
    assert accepted["supports"][0]["kind"] == "pier"
    assert accepted["levels"][0]["measurement_system"] == "imperial"
    assert accepted["levels"][0]["display"] == "1'-0\""


def test_partial_member_keeps_plan_geometry_and_refuses_elevation():
    accepted = assess_construction_model(_model()).accepted
    joist = next(item for item in accepted["members"] if item["id"] == "joist-1")
    assert joist["geometry"]["known"] == ["x", "y"]
    assert joist["geometry"]["unknown"] == ["z"]
    assert "length" not in joist
    wave = project_construction_wave(_model())
    assert "joist-1" in [item["id"] for item in wave.plan.elements]
    assert "joist-1" not in [item["id"] for item in wave.front_elevation.elements]
    assert any("post-a" in issue.message for issue in wave.plan.issues)
    assert any("elevation of member joist-1" in issue.message for issue in wave.front_elevation.issues)
    assert not any("elevation of member beam-a" in issue.message for issue in wave.front_elevation.issues)
    row = next(item for item in wave.schedule.members if item["id"] == "joist-1")
    assert row["lengths"] == ()


def test_length_is_derived_from_endpoints_and_a_conflict_is_refused():
    accepted = assess_construction_model(_model()).accepted
    beam = next(item for item in accepted["members"] if item["id"] == "beam-a")
    assert beam["length"]["derived"] is True
    assert beam["length"]["display"] == "10'-0\""
    assert beam["length"]["provenance"]["reference"] == "Derived from the member endpoints"
    assert len(beam["geometry"]["coordinates"]) == 2
    conflict = _model()
    conflict["members"][1]["length"] = 8
    result = assess_construction_model(conflict)
    assert result.complete is False
    assert result.issues[0].code == CODE_CONFLICTING_GEOMETRY
    supplied = _model()
    supplied["members"][0]["length"] = 12
    stored = assess_construction_model(supplied).accepted
    joist = next(item for item in stored["members"] if item["id"] == "joist-1")
    assert joist["length"]["value"] == 12
    assert joist["length"]["derived"] is False
    assert len(joist["geometry"]["coordinates"]) == 1


def test_relationships_are_not_inferred_and_connections_keep_supplied_parts():
    near = _model()
    near["relationships"] = []
    near["connections"] = []
    accepted = assess_construction_model(near).accepted
    assert accepted["relationships"] == []
    assert accepted["connections"] == []
    full = assess_construction_model(_model()).accepted
    assert [item["kind"] for item in full["relationships"]] == ["supports", "protects"]
    connection = full["connections"][0]
    assert connection["connector"] == "test-connector"
    assert connection["fastener"] == "test-fastener"
    assert connection["quantity"] == 4
    assert "invented" not in connection


def test_material_size_and_pier_without_shaft_data():
    accepted = assess_construction_model(_model()).accepted
    joist = next(item for item in accepted["members"] if item["id"] == "joist-1")
    post = next(item for item in accepted["members"] if item["id"] == "post-a")
    assert joist["member_size"] == "2x8"
    assert joist["material_id"] == "joist-stock"
    assert post["member_size"] == "6x6"
    pier = accepted["supports"][0]
    assert pier["kind"] == "pier"
    assert "shaft_length" not in pier
    assert "depth" not in pier
    assert "capacity" not in pier
    wave = project_construction_wave(_model())
    assert "pier-a" in [item["id"] for item in wave.plan.elements]


def test_stair_result_is_not_recalculated():
    wave = project_construction_wave(_model())
    result = wave.schedule
    assert result.produced is True
    stair = assess_construction_model(_model()).accepted["stair_results"][0]
    assert stair["throat"] == 5
    assert "rise" not in stair
    assert "run" not in stair
    assert wave.stairs[0].projected is False
    assert any("rise" in issue.message for issue in wave.stairs[0].issues)


def test_view_requirements_stay_specific():
    by_view = {item["view"]: item for item in VIEW_REQUIREMENTS}
    assert by_view["plan"]["axes"] == ("x", "y")
    assert "z" in by_view["plan"]["does_not_require"]
    assert "z" in by_view["front_elevation"]["axes"]
    assert by_view["schedule"]["does_not_require"] == ("an invented length",)


def test_component_model_does_not_write_project_plan_or_estimate():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test",
        }
    )
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        before = (Project.query.count(), PlanDocument.query.count(), Estimate.query.count())
        assess_construction_model(_model())
        project_construction_wave(_model())
        after = (Project.query.count(), PlanDocument.query.count(), Estimate.query.count())
        assert before == (0, 0, 0)
        assert after == before
