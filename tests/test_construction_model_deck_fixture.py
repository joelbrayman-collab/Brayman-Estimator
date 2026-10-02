"""Complete generic deck fixture and the drawing set it produces."""

from __future__ import annotations

from app import create_app, db
from app.models import Estimate, Project
from app.plan_intelligence.models import PlanDocument
from app.services.construction_model import (
    assess_construction_model,
    compose_construction_wave,
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


def _wave():
    return project_construction_wave(deck_model(), sections=section_requests(), details=detail_requests())


def _set():
    return compose_construction_wave(
        deck_model(),
        sheet_definition(),
        sections=section_requests(),
        details=detail_requests(),
        sheet_program=sheet_program(),
    )


def test_complete_fixture_loads_and_passes_completeness():
    assessment = assess_construction_model(deck_model())
    assert assessment.complete is True
    assert assessment.generation_permitted is True
    assert assessment.issues == ()
    assert "complete deck drawing engine fixture" in assessment.accepted["uncertainty"][0]["note"].lower()


def test_required_views_generate_from_the_model():
    wave = _wave()
    assert wave.projected is True
    assert wave.plan.projected is True
    assert wave.front_elevation.projected is True
    assert wave.side_elevation.projected is True
    assert wave.stairs[0].projected is True
    assert wave.sections[0].projected is True
    assert all(detail.projected for detail in wave.details)
    assert wave.schedule.produced is True
    assert wave.schedule.issues == ()


def test_views_use_model_geometry_and_do_not_own_a_store():
    model = deck_model()
    assessment = assess_construction_model(model)
    known = {item["id"] for item in assessment.accepted["members"]}
    known.update(item["id"] for item in assessment.accepted["supports"])
    known.update(item["id"] for item in assessment.accepted["openings"])
    wave = _wave()
    views = (
        wave.plan,
        wave.front_elevation,
        wave.side_elevation,
        wave.stairs[0],
        wave.sections[0],
        *wave.details,
    )
    for view in views:
        for element in view.elements:
            assert element["id"] in known
            assert "source_geometry" in element
    assert "members" not in sheet_program()[0]
    assert "geometry" not in section_requests()[0]


def test_dimensions_schedules_stair_and_details_read_the_model():
    wave = _wave()
    chains = {item["id"]: item for item in wave.schedule.dimension_chains}
    assert chains["width"]["overall"]["display"] == "12'-0\""
    assert chains["stair-rise"]["segments"][0]["display"] == "3'-6\""
    assert chains["stair-run"]["segments"][0]["display"] == "4'-7\""
    assert wave.stairs[0].facts[0] == ("rise", 7)
    assert ("stair_width", 36) in wave.stairs[0].facts
    assert wave.sections[0].view_id == "A"
    assert "post-1" in [element["id"] for element in wave.sections[0].elements]
    assert "beam-front" in [element["id"] for element in wave.sections[0].elements]
    post_detail = wave.details[0]
    assert [element["id"] for element in post_detail.elements] == ["post-1", "beam-front"]
    sizes = {row["id"]: row["member_size"] for row in wave.schedule.members}
    assert sizes["joist-1"] == "2x8"
    assert sizes["post-1"] == "6x6"
    assert any(row["role"] == "joist" for row in wave.schedule.members)


def test_sheet_program_is_deterministic_and_does_not_scale_to_fit():
    first = _set()
    second = _set()
    assert first.composed is True, [issue.message for issue in first.issues]
    assert first.view_issues == ()
    assert first.manifest["pdf_sha256"] == second.manifest["pdf_sha256"]
    titles = [page["kind"] for page in first.manifest["pages"]]
    assert titles[:9] == [
        "plan",
        "plan",
        "plan",
        "front_elevation",
        "side_elevation",
        "stair",
        "section",
        "detail",
        "detail",
    ]
    assert titles[-1] == "schedule"
    assert first.manifest["sheet_count"] == len(titles)
    scales = {page.get("scale") for page in sheet_program() if page.get("scale")}
    assert "1/2 in = 1 ft" in scales
    assert "1 in = 1 ft" in scales
    assert scales == {"1/2 in = 1 ft", "1 in = 1 ft"}


def test_filtered_sheets_share_ids_and_omit_no_requested_view():
    result = _set()
    model_ids = {item["id"] for item in assess_construction_model(deck_model()).accepted["members"]}
    model_ids.update(item["id"] for item in assess_construction_model(deck_model()).accepted["supports"])
    seen = set()
    for page in result.manifest["pages"]:
        for identifier in page["element_ids"]:
            assert identifier in model_ids or identifier == "opening-stair"
            seen.add(identifier)
    assert {"pier-1", "joist-1", "deck-1", "guard-front-a", "gate-1", "stringer-1", "post-1"} <= seen


def test_fixture_set_does_not_write_project_plan_or_estimate():
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        before = (Project.query.count(), PlanDocument.query.count(), Estimate.query.count())
        _set()
        after = (Project.query.count(), PlanDocument.query.count(), Estimate.query.count())
        assert before == after == (0, 0, 0)
