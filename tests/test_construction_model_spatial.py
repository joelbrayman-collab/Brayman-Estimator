"""Partial geometry, sheet sets, and dimension notation."""

from __future__ import annotations

from io import BytesIO

from pypdf import PdfReader

from app import create_app, db
from app.models import Estimate, Project
from app.plan_intelligence.models import PlanDocument
from app.services.construction_model import (
    assess_construction_model,
    compose_construction_wave,
    project_construction_wave,
)
from app.services.construction_model.model import format_measure
from app.services.construction_model.sheet import CODE_VIEW_CANNOT_BE_PLACED
from app.services.organizations import ensure_default_organization


def _provenance():
    return {"source": "project_input"}


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
                "id": "lower-walk",
                "name": "Finished lower deck",
                "elevation": 1,
                "provenance": _provenance(),
            }
        ],
        "members": [
            {
                "id": "joist-1",
                "role": "joist",
                "geometry": _point(4, 8),
                "provenance": _provenance(),
            },
            {
                "id": "beam-a",
                "role": "beam",
                "geometry": _segment((0, 1, 2), (6, 1, 2)),
                "provenance": _provenance(),
            },
        ],
        "supports": [
            {
                "id": "pier-a",
                "kind": "pier",
                "geometry": _point(0, 1, 0),
                "provenance": _provenance(),
            },
            {
                "id": "pier-b",
                "kind": "pier",
                "geometry": _point(0, 1, 0),
                "provenance": _provenance(),
            },
        ],
        "dimensions": [
            {"id": "beam-length", "value": 10, "unit": "ft", "subject_id": "beam-a", "start_id": "pier-a", "end_id": "beam-a"},
            {"id": "lower-height", "value": 12, "unit": "in", "subject_id": "lower-walk"},
        ],
    }
    payload.update(overrides)
    return payload


def _sheet(**overrides):
    payload = {
        "paper": "11x17",
        "scale": "1/4 in = 1 ft",
        "organization_name": "Brayman Construction",
        "project_name": "Partial deck",
        "address": "12 Example Road",
        "drawing_title": "Construction drawing",
        "sheet_number": "1",
        "revision": "A",
        "date": "2026-10-02",
    }
    payload.update(overrides)
    return payload


def _ids(view):
    return [element["id"] for element in view.elements]


def test_partial_plan_station_is_stored_without_an_elevation():
    accepted = assess_construction_model(_model()).accepted
    joist = next(item for item in accepted["members"] if item["id"] == "joist-1")
    assert joist["geometry"]["known"] == ["x", "y"]
    assert joist["geometry"]["unknown"] == ["z"]
    assert joist["geometry"]["coordinates"][0]["z"] is None
    assert joist["provenance"]["source"] == "project_input"


def test_plan_includes_the_station_and_elevations_omit_it():
    wave = project_construction_wave(_model())
    assert "joist-1" in _ids(wave.plan)
    assert "beam-a" in _ids(wave.plan)
    assert "joist-1" not in _ids(wave.front_elevation)
    assert "joist-1" not in _ids(wave.side_elevation)
    assert "beam-a" in _ids(wave.front_elevation)
    assert "beam-a" in _ids(wave.side_elevation)
    messages = [issue.message for issue in wave.front_elevation.issues]
    assert any(
        message == "You need to provide this information. The elevation of member joist-1 for the front elevation."
        for message in messages
    )
    assert all("beam-a" not in message for message in messages)


def test_section_refuses_only_the_member_that_lacks_elevation():
    wave = project_construction_wave(
        _model(),
        sections=[{"id": "cut-a", "section_direction": "y", "section_location": 1, "cut_depth": 0}],
    )
    section = wave.sections[0]
    assert section.projected is True
    assert "beam-a" in _ids(section)
    assert "joist-1" not in _ids(section)
    assert any(
        "The elevation of member joist-1 for section cut-a" in issue.message for issue in section.issues
    )


def test_schedule_names_the_member_and_does_not_invent_its_length():
    schedule = project_construction_wave(_model()).schedule
    rows = {row["id"]: row for row in schedule.members}
    assert rows["joist-1"]["role"] == "joist"
    assert rows["joist-1"]["lengths"] == ()
    assert rows["joist-1"]["length_displays"] == ()
    assert rows["beam-a"]["lengths"] == (10,)
    assert rows["beam-a"]["length_displays"] == ("10'-0\"",)
    assert any("The length of member joist-1" in issue.message for issue in schedule.issues)
    assert not any("The length of member beam-a" in issue.message for issue in schedule.issues)


def test_sheet_set_moves_an_oversized_elevation_and_keeps_the_scale():
    wide = _model()
    wide["members"][1]["geometry"] = _segment((0, 1, 2), (30, 1, 2))
    result = compose_construction_wave(wide, _sheet())
    assert result.composed is True
    kinds = [page["kind"] for page in result.manifest["pages"]]
    assert kinds[0] == "orthographic"
    assert "front_elevation" in kinds
    assert kinds[-1] == "index"
    assert "schedule" in kinds
    assert result.manifest["points_per_unit"] == 18
    assert result.manifest["sheet_count"] == len(result.manifest["pages"])
    assert result.manifest["sheet_count"] == len(PdfReader(BytesIO(result.pdf_bytes)).pages)
    numbers = [page["sheet_number"] for page in result.manifest["pages"]]
    assert numbers == [str(index) for index in range(1, len(numbers) + 1)]
    text = "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(result.pdf_bytes)).pages)
    assert f"Sheet 1 of {result.manifest['sheet_count']}" in text
    assert "10'-0\"" in text
    assert "1'-0\"" in text
    assert '12"' in text
    assert "2 PIERS" in text
    assert "pier-a" in text and "pier-b" in text


def test_metric_dimension_uses_metric_notation():
    assert format_measure(3, "metric") == "3 m"
    assert format_measure(12, "metric", "mm") == "12 mm"


def test_level_change_moves_elevations_and_leaves_the_plan_station():
    original = project_construction_wave(_model())
    revised = _model()
    revised["levels"][0]["elevation"] = 2
    revised["members"][0]["geometry"]["coordinates"][0]["x"] = 5
    updated = project_construction_wave(revised)
    assert _element_u(original.plan, "joist-1") == 4
    assert _element_u(updated.plan, "joist-1") == 5
    assert _element_u(original.front_elevation, "beam-a") == _element_u(updated.front_elevation, "beam-a")
    assert updated.schedule.levels[0]["display"] == "2'-0\""
    assert original.schedule.levels[0]["display"] == "1'-0\""
    assert "joist-1" not in _ids(updated.front_elevation)


def test_required_view_is_refused_when_it_cannot_be_placed():
    result = compose_construction_wave(_model(), _sheet(scale="4/1 in = 1 ft"))
    assert result.composed is False
    assert result.pdf_bytes is None
    assert result.manifest["points_per_unit"] == 288
    assert result.manifest["scale"] == "4/1 in = 1 ft"
    assert result.manifest["pages"] == []
    assert result.issues[0].code == CODE_VIEW_CANNOT_BE_PLACED
    assert result.issues[0].message == "You need to provide a different sheet arrangement or scale."
    assert any(issue.field == "plan" for issue in result.issues)


def test_spatial_sheet_does_not_write_project_plan_or_estimate():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-spatial",
            "WTF_CSRF_ENABLED": False,
        }
    )
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        projects_before = Project.query.count()
        plans_before = PlanDocument.query.count()
        estimates_before = Estimate.query.count()
        result = compose_construction_wave(_model(), _sheet())
        assert result.composed is True
        assert Project.query.count() == projects_before
        assert PlanDocument.query.count() == plans_before
        assert Estimate.query.count() == estimates_before


def _element_u(view, identifier):
    element = next(item for item in view.elements if item["id"] == identifier)
    return element["projected_geometry"]["coordinates"][0]["u"]
