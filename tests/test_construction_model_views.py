"""Slice 4: stair, section, detail, and schedule views from one model."""

from __future__ import annotations

import copy
from io import BytesIO

from pypdf import PdfReader

from app import create_app, db
from app.models import Estimate, Project
from app.plan_intelligence.models import PlanDocument
from app.services.construction_model import (
    DOCUMENT_STATUS_PRELIMINARY,
    compose_construction_wave,
    project_construction_wave,
)
from app.services.construction_model.sheet import CODE_GEOMETRY_DOES_NOT_FIT_SHEET
from app.services.organizations import ensure_default_organization


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


def _model(**overrides):
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
            {
                "id": "stringer-a",
                "role": "stringer",
                "geometry": _segment((4, 0, 0), (4, 3, 2)),
                "provenance": _provenance("governed_calculation_result"),
            },
            {
                "id": "rim-a",
                "role": "rim",
                "geometry": _segment((0, 20, 2), (4, 20, 2)),
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
        "dimensions": [
            {
                "id": "beam-length",
                "subject_id": "beam-a",
                "value": 8,
            }
        ],
        "stair_results": [
            {
                "id": "stair-a",
                "member_ids": ["stringer-a"],
                "provenance": _provenance("governed_calculation_result"),
                "rise": 6,
                "run": 10,
                "throat": 5,
                "nosing": 1,
                "stringer_count": 2,
                "tread_count": 3,
                "stair_width": 3,
            }
        ],
        "uncertainty": [
            {
                "code": "FIELD_VERIFICATION_REQUIRED",
                "subject_id": "stringer-a",
                "note": "Stringer bearing is not confirmed.",
            }
        ],
    }
    payload.update(overrides)
    return payload


def _section():
    return {
        "id": "section-a",
        "section_direction": "y",
        "section_location": 1,
        "cut_depth": 0,
    }


def _detail():
    return {"id": "detail-a", "element_ids": ["beam-a"], "view_type": "plan"}


def _sheet():
    return {
        "paper": "11x17",
        "scale": "1/4 in = 1 ft",
        "organization_name": "Brayman Construction",
        "project_name": "Sample deck",
        "address": "12 Example Road",
        "drawing_title": "Construction drawing",
        "sheet_number": "1",
        "revision": "A",
        "date": "2026-10-01",
    }


def _ids(view):
    return [element["id"] for element in view.elements]


def _element(view, identifier):
    return next(element for element in view.elements if element["id"] == identifier)


def test_stair_view_reads_supplied_facts_and_member_geometry():
    wave = project_construction_wave(_model(), sections=[_section()], details=[_detail()])
    stair = wave.stairs[0]
    assert stair.projected is True
    assert stair.facts == (
        ("rise", 6),
        ("run", 10),
        ("throat", 5),
        ("nosing", 1),
        ("stringer_count", 2),
        ("tread_count", 3),
        ("stair_width", 3),
    )
    assert _ids(stair) == ["stringer-a"]
    assert _element(stair, "stringer-a")["source_geometry"]["coordinates"][1]["y"] == 3


def test_section_includes_only_elements_the_cut_meets():
    wave = project_construction_wave(_model(), sections=[_section()], details=[_detail()])
    section = wave.sections[0]
    assert section.projected is True
    assert "beam-a" in _ids(section)
    assert "joist-a" in _ids(section)
    assert "rim-a" not in _ids(section)
    assert "invented-post" not in _ids(section)


def test_detail_reads_the_named_model_element():
    wave = project_construction_wave(_model(), sections=[_section()], details=[_detail()])
    detail = wave.details[0]
    assert detail.projected is True
    assert _ids(detail) == ["beam-a"]
    assert _element(detail, "beam-a")["projected_geometry"]["coordinates"][1]["u"] == 8


def test_schedule_reads_model_rows_and_refuses_missing_lengths():
    wave = project_construction_wave(_model(), sections=[_section()], details=[_detail()])
    rows = {row["id"]: row for row in wave.schedule.members}
    assert rows["beam-a"]["role"] == "beam"
    assert rows["beam-a"]["lengths"] == (8,)
    assert rows["joist-a"]["lengths"] == ()
    assert wave.schedule.supports[0]["id"] == "support-a"
    assert wave.schedule.supports[0]["kind"] == "pier"
    messages = [issue.message for issue in wave.schedule.issues]
    assert any(message.startswith("You need to provide this information. The length of member joist-a") for message in messages)
    assert all("8" != row["lengths"] for row in wave.schedule.members if row["id"] == "joist-a")


def test_missing_stair_fact_refuses_only_the_stair_view():
    model = _model()
    del model["stair_results"][0]["rise"]
    wave = project_construction_wave(model, sections=[_section()], details=[_detail()])
    assert wave.projected is True
    assert wave.plan.projected is True
    assert wave.stairs[0].projected is False
    assert wave.stairs[0].elements == ()
    assert wave.sections[0].projected is True
    assert wave.details[0].projected is True
    assert any(
        issue.message.startswith("You need to provide this information. The stair rise")
        for issue in wave.stairs[0].issues
    )


def test_one_model_drives_every_view():
    model = _model()
    wave = project_construction_wave(model, sections=[_section()], details=[_detail()])
    model_ids = {item["id"] for item in model["members"]} | {item["id"] for item in model["supports"]}
    for view in (wave.plan, wave.front_elevation, wave.side_elevation, wave.stairs[0], wave.sections[0], wave.details[0]):
        assert set(_ids(view)) <= model_ids
    assert _element(wave.plan, "beam-a")["source_geometry"]["coordinates"] == model["members"][0]["geometry"]["coordinates"]
    assert {row["id"] for row in wave.schedule.members} <= model_ids


def test_revision_reaches_affected_views_and_leaves_the_others():
    original = _model()
    before = project_construction_wave(original, sections=[_section()], details=[_detail()])
    changed = copy.deepcopy(original)
    changed["members"][0]["geometry"]["coordinates"][1]["x"] = 9
    after = project_construction_wave(changed, sections=[_section()], details=[_detail()])
    assert _element(before.plan, "beam-a")["projected_geometry"]["coordinates"][1]["u"] == 8
    assert _element(after.plan, "beam-a")["projected_geometry"]["coordinates"][1]["u"] == 9
    assert _element(after.sections[0], "beam-a")["projected_geometry"]["coordinates"][1]["u"] == 9
    assert _element(after.details[0], "beam-a")["projected_geometry"]["coordinates"][1]["u"] == 9
    assert _element(before.side_elevation, "joist-a")["projected_geometry"] == (
        _element(after.side_elevation, "joist-a")["projected_geometry"]
    )
    assert _element(before.stairs[0], "stringer-a")["projected_geometry"] == (
        _element(after.stairs[0], "stringer-a")["projected_geometry"]
    )
    assert before.schedule.supports == after.schedule.supports
    assert original["members"][0]["geometry"]["coordinates"][1]["x"] == 8


def test_view_definition_cannot_carry_geometry():
    definition = _section()
    definition["members"] = [{"id": "extra"}]
    wave = project_construction_wave(_model(), sections=[definition], details=[_detail()])
    assert wave.sections[0].projected is False
    assert wave.sections[0].elements == ()
    assert "without its own geometry" in wave.sections[0].issues[0].fact


def test_missing_detail_fact_is_named_and_not_invented():
    definition = _detail()
    definition["requires"] = ["fastener"]
    wave = project_construction_wave(_model(), sections=[_section()], details=[definition])
    assert wave.details[0].projected is False
    assert wave.details[0].elements == ()
    assert wave.details[0].issues[0].message.startswith("You need to provide this information. The fastener")


def test_uncertainty_reaches_the_stair_section_and_schedule():
    wave = project_construction_wave(_model(), sections=[_section()], details=[_detail()])
    note = {"code": "FIELD_VERIFICATION_REQUIRED", "subject_id": "stringer-a", "note": "Stringer bearing is not confirmed."}
    assert wave.stairs[0].uncertainty == (note,)
    assert _element(wave.stairs[0], "stringer-a")["uncertainty"] == [note]
    assert note in wave.sections[0].uncertainty
    stringer = next(row for row in wave.schedule.members if row["id"] == "stringer-a")
    assert stringer["uncertainty"] == [note]
    assert stringer["lengths"] == ()


def test_wave_composes_separate_11x17_sheets_at_the_stated_scale():
    result = compose_construction_wave(_model(), _sheet(), sections=[_section()], details=[_detail()])
    assert result.composed is True
    reader = PdfReader(BytesIO(result.pdf_bytes))
    assert len(reader.pages) >= 4
    box = reader.pages[0].mediabox
    assert abs(float(box.width) - 1224) < 0.1
    assert abs(float(box.height) - 792) < 0.1
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    assert "PLAN" in text
    assert "STAIR stair-a" in text
    assert "rise 6" in text
    assert "SECTION section-a" in text
    assert "DETAIL detail-a" in text
    assert "SCHEDULE" in text
    assert "beam-a" in text
    assert "PRELIMINARY CONSTRUCTION DRAWING" in text
    assert "Scale 1/4 in = 1 ft" in text
    assert "Stringer bearing is not confirmed." in text
    assert "The length of member joist-a" in text
    assert "Not a permit" not in text
    assert "Not a seal" not in text
    assert result.manifest["pages"][0]["kind"] == "orthographic"
    assert result.manifest["pages"][-1]["kind"] == "schedule"


def test_wave_does_not_scale_to_fit():
    result = compose_construction_wave(
        _model(),
        {**_sheet(), "scale": "4/1 in = 1 ft"},
        sections=[_section()],
        details=[_detail()],
    )
    assert result.composed is True
    assert result.manifest["points_per_unit"] == 288
    assert result.manifest["scale"] == "4/1 in = 1 ft"
    assert "orthographic" not in [page["kind"] for page in result.manifest["pages"]]
    assert result.manifest["pages"][-1]["kind"] == "schedule"
    assert any(issue.code == CODE_GEOMETRY_DOES_NOT_FIT_SHEET for issue in result.view_issues)


def test_incomplete_model_produces_no_wave_sheet():
    payload = _model()
    payload["supports"] = []
    result = compose_construction_wave(payload, _sheet(), sections=[_section()], details=[_detail()])
    assert result.composed is False
    assert result.pdf_bytes is None
    assert result.issues[0].message.startswith("You need to provide this information.")


def test_wave_does_not_write_project_plan_or_estimate():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-construction-wave",
            "WTF_CSRF_ENABLED": False,
        }
    )
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        projects_before = Project.query.count()
        plans_before = PlanDocument.query.count()
        estimates_before = Estimate.query.count()
        project_construction_wave(_model(), sections=[_section()], details=[_detail()])
        compose_construction_wave(_model(), _sheet(), sections=[_section()], details=[_detail()])
        assert Project.query.count() == projects_before
        assert PlanDocument.query.count() == plans_before
        assert Estimate.query.count() == estimates_before
        db.session.remove()
        db.drop_all()
