"""Slice 2: plan, front elevation, and side elevation from one model."""

from __future__ import annotations

import copy
from pathlib import Path

from app import create_app, db
from app.models import Estimate, Project
from app.plan_intelligence.models import PlanDocument
from app.services.construction_model import (
    DOCUMENT_STATUS_PRELIMINARY,
    project_construction_view,
    project_model_views,
)
from app.services.construction_model.completeness import CODE_MISSING_SUPPORT
from app.services.construction_model.projection import (
    VIEW_FRONT_ELEVATION,
    VIEW_PLAN,
    VIEW_SIDE_ELEVATION,
    describe_projection,
    governed_view_definition,
)
from app.services.organizations import ensure_default_organization

PACKAGE = Path(__file__).resolve().parents[1] / "app" / "services" / "construction_model"
FORBIDDEN_SOURCE = (
    "bushel",
    "Bushel",
    "linda",
    "Linda",
    "10.5",
    "reportlab",
    "freecad",
    "FreeCAD",
    "cadquery",
    "build123d",
)


def _provenance(source="project_input"):
    return {"source": source}


def _point(x, y, z):
    return {"kind": "point", "coordinates": [{"x": x, "y": y, "z": z}]}


def _segment(start, end):
    return {
        "kind": "segment",
        "coordinates": [
            {"x": start[0], "y": start[1], "z": start[2]},
            {"x": end[0], "y": end[1], "z": end[2]},
        ],
    }


def _fixture(**overrides):
    """Small deck-class fixture. Counts and coordinates are not a job default."""
    payload = {
        "structure_class": "deck",
        "project_document_status": DOCUMENT_STATUS_PRELIMINARY,
        "measurement_system": "imperial",
        "levels": [
            {
                "id": "walk",
                "name": "Walking surface",
                "elevation": 3,
                "provenance": _provenance(),
            }
        ],
        "members": [
            {
                "id": "beam-a",
                "role": "beam",
                "geometry": _segment((0, 1, 2), (8, 1, 2)),
                "provenance": _provenance("governed_calculation_result"),
            },
            {
                "id": "joist-a",
                "role": "joist",
                "geometry": _segment((1, 0, 3), (1, 5, 3)),
                "provenance": _provenance(),
            },
        ],
        "supports": [
            {
                "id": "support-a",
                "kind": "pier",
                "geometry": _point(0, 1, 0),
                "provenance": _provenance("source_document"),
            }
        ],
        "uncertainty": [
            {
                "code": "FIELD_VERIFICATION_REQUIRED",
                "subject_id": "support-a",
                "note": "Support length is not confirmed.",
            }
        ],
    }
    payload.update(overrides)
    return payload


def _ids(projection):
    return [element["id"] for element in projection.elements]


def _element(projection, identifier):
    return next(element for element in projection.elements if element["id"] == identifier)


def test_same_model_produces_plan_front_and_side():
    model = _fixture()
    views = project_model_views(model)
    assert views.projected is True
    assert views.drawing_artifact is None
    assert views.plan.view_type == VIEW_PLAN
    assert views.front_elevation.view_type == VIEW_FRONT_ELEVATION
    assert views.side_elevation.view_type == VIEW_SIDE_ELEVATION
    assert views.plan.horizontal_axis == "x"
    assert views.plan.vertical_axis == "y"
    assert views.front_elevation.horizontal_axis == "x"
    assert views.front_elevation.vertical_axis == "z"
    assert views.side_elevation.horizontal_axis == "y"
    assert views.side_elevation.vertical_axis == "z"
    for view in (views.plan, views.front_elevation, views.side_elevation):
        assert view.projected is True
        assert view.drawing_artifact is None
        assert "beam-a" in _ids(view)
        assert "support-a" in _ids(view)
        assert view.levels[0]["elevation"] == 3


def test_plan_uses_horizontal_coordinates():
    views = project_model_views(_fixture())
    beam = _element(views.plan, "beam-a")
    assert beam["projected_geometry"]["coordinates"][0]["u"] == 0
    assert beam["projected_geometry"]["coordinates"][0]["v"] == 1
    assert beam["projected_geometry"]["coordinates"][1]["u"] == 8
    assert beam["source_geometry"]["coordinates"][1]["z"] == 2
    assert "support-a" in describe_projection(views.plan)


def test_front_elevation_uses_height():
    views = project_model_views(_fixture())
    beam = _element(views.front_elevation, "beam-a")
    start = beam["projected_geometry"]["coordinates"][0]
    assert start["u"] == 0
    assert start["v"] == 2
    assert start["source"] == {"x": 0, "y": 1, "z": 2}


def test_side_elevation_uses_depth_and_height():
    views = project_model_views(_fixture())
    joist = _element(views.side_elevation, "joist-a")
    coords = joist["projected_geometry"]["coordinates"]
    assert coords[0]["u"] == 0
    assert coords[0]["v"] == 3
    assert coords[1]["u"] == 5
    assert coords[1]["v"] == 3


def test_member_is_consistent_and_cannot_be_invented():
    model = _fixture()
    views = project_model_views(model)
    model_ids = {item["id"] for item in model["members"]} | {item["id"] for item in model["supports"]}
    for view in (views.plan, views.front_elevation, views.side_elevation):
        assert set(_ids(view)) <= model_ids
        assert "invented-post" not in _ids(view)
        beam = _element(view, "beam-a")
        assert beam["source_geometry"] == model["members"][0]["geometry"]
        assert beam["provenance"] == model["members"][0]["provenance"]


def test_changing_a_coordinate_changes_affected_views_only_from_the_model():
    original = _fixture()
    before = project_model_views(original)
    changed = copy.deepcopy(original)
    changed["members"][0]["geometry"]["coordinates"][1]["x"] = 9
    after = project_model_views(changed)
    assert _element(before.plan, "beam-a")["projected_geometry"]["coordinates"][1]["u"] == 8
    assert _element(after.plan, "beam-a")["projected_geometry"]["coordinates"][1]["u"] == 9
    assert _element(after.front_elevation, "beam-a")["projected_geometry"]["coordinates"][1]["u"] == 9
    assert _element(before.side_elevation, "joist-a")["projected_geometry"] == (
        _element(after.side_elevation, "joist-a")["projected_geometry"]
    )
    assert original["members"][0]["geometry"]["coordinates"][1]["x"] == 8


def test_projection_does_not_mutate_the_model():
    model = _fixture()
    snapshot = copy.deepcopy(model)
    project_model_views(model)
    project_construction_view(model, governed_view_definition(VIEW_PLAN))
    assert model == snapshot


def test_removing_a_required_support_refuses_every_view():
    payload = _fixture()
    payload["supports"] = []
    views = project_model_views(payload)
    assert views.projected is False
    assert views.drawing_artifact is None
    assert views.issues[0].code == CODE_MISSING_SUPPORT
    assert views.issues[0].message.startswith("You need to provide this information.")
    for view in (views.plan, views.front_elevation, views.side_elevation):
        assert view.projected is False
        assert view.elements == ()
        assert view.levels == ()
        assert view.drawing_artifact is None


def test_view_definition_cannot_carry_members():
    definition = governed_view_definition(VIEW_PLAN)
    definition["members"] = [{"id": "extra", "role": "post"}]
    result = project_construction_view(_fixture(), definition)
    assert result.projected is False
    assert result.elements == ()
    assert result.issues[0].field == "view.members"
    assert "without its own geometry" in result.issues[0].fact


def test_uncertainty_survives_projection():
    views = project_model_views(_fixture())
    note = views.uncertainty[0]
    assert note["code"] == "FIELD_VERIFICATION_REQUIRED"
    for view in (views.plan, views.front_elevation, views.side_elevation):
        assert view.uncertainty == (note,)
        support = _element(view, "support-a")
        assert support["uncertainty"] == [note]
        assert _element(view, "beam-a")["uncertainty"] == []


def test_source_has_no_job_defaults_or_sheet_writer():
    for path in PACKAGE.glob("*.py"):
        source = path.read_text(encoding="utf-8")
        for token in FORBIDDEN_SOURCE:
            assert token not in source, path.name


def test_projection_does_not_write_project_plan_or_estimate():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-construction-view",
            "WTF_CSRF_ENABLED": False,
        }
    )
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        projects_before = Project.query.count()
        plans_before = PlanDocument.query.count()
        estimates_before = Estimate.query.count()
        project_model_views(_fixture())
        project_model_views({"structure_class": "deck"})
        assert Project.query.count() == projects_before
        assert PlanDocument.query.count() == plans_before
        assert Estimate.query.count() == estimates_before
        db.session.remove()
        db.drop_all()
