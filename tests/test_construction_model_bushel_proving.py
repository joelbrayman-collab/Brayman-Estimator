"""Bushel proving fixture for the Construction Model.

The fixture is case data. The engine stays generic.
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

from pypdf import PdfReader

from app import create_app, db
from app.models import Estimate, Project
from app.plan_intelligence.models import PlanDocument
from app.services.construction_model import (
    assess_construction_model,
    compose_construction_wave,
    project_construction_wave,
)
from app.services.construction_model.sheet import CODE_GEOMETRY_DOES_NOT_FIT_SHEET
from app.services.organizations import ensure_default_organization
from tests.fixtures.construction_model.bushel_proving_fixture import (
    ADDRESS,
    FIXTURE_LABEL,
    GATE_CLEAR_IN,
    JOIST_STATION_IN,
    LOWER_WALKING_SURFACE_IN,
    PIER_COORDINATES,
    SCALE_THAT_DOES_NOT_FIT,
    STATED_SCALE,
    STRINGER_COUNT,
    STRINGER_STATION_IN,
    STRINGER_THROAT_IN,
    TREAD_BOARDS,
    VERANDA_KIT,
    WITHHELD,
    detail_requests,
    joist_stations_ft,
    proving_model,
    section_requests,
    sheet_definition,
    stringer_stations_ft,
)

PACKAGE = Path(__file__).resolve().parents[1] / "app" / "services" / "construction_model"
FORBIDDEN_IN_ENGINE = (
    "bushel",
    "Bushel",
    "linda",
    "Linda",
    "D'Arcy",
    "Kemptville",
    FIXTURE_LABEL,
)


def _wave(model=None, sheet=None):
    return project_construction_wave(
        proving_model() if model is None else model,
        sections=section_requests(),
        details=detail_requests(),
    )


def _composed(model=None, sheet=None):
    return compose_construction_wave(
        proving_model() if model is None else model,
        sheet_definition() if sheet is None else sheet,
        sections=section_requests(),
        details=detail_requests(),
    )


def _ids(view):
    return [element["id"] for element in view.elements]


def _messages(issues):
    return [issue.message for issue in issues]


def test_bushel_fixture_loads_as_proving_data():
    model = proving_model()
    assert model["fixture_label"] == FIXTURE_LABEL
    assert FIXTURE_LABEL == "BUSHEL PROVING FIXTURE"
    assessment = assess_construction_model(model)
    assert assessment.complete is True
    assert assessment.generation_permitted is True


def test_governed_decisions_are_represented():
    model = proving_model()
    assert len(PIER_COORDINATES) == 15
    assert len(model["supports"]) == 15
    assert [item["id"] for item in model["supports"]] == [item[0] for item in PIER_COORDINATES]
    assert len(JOIST_STATION_IN) == 16
    assert len(joist_stations_ft()) == 16
    assert len(STRINGER_STATION_IN) == STRINGER_COUNT
    assert len(stringer_stations_ft()) == 10
    assert STRINGER_THROAT_IN == 5.0
    assert LOWER_WALKING_SURFACE_IN == 12
    assert model["levels"][0]["elevation"] == 1
    assert ADDRESS == "12 D'Arcy's Way, Kemptville, ON K0G 1J0"
    assert TREAD_BOARDS == "Two 5/4 x 6 boards per tread"
    assert VERANDA_KIT == "37 in Veranda rail kit"
    assert GATE_CLEAR_IN == 42
    stair = model["stair_results"][0]
    assert stair["throat"] == 5.0
    assert stair["stringer_count"] == 10
    assert stair["stair_width"] == 10
    materials = {item["id"]: item["name"] for item in model["materials"]}
    assert materials["tread-boards"] == TREAD_BOARDS
    assert materials["veranda-kit"] == VERANDA_KIT
    dimensions = {item["id"]: item["value"] for item in model["dimensions"]}
    assert dimensions["gate-clear"] == 42
    assert dimensions["lower-walking-surface-height"] == 12


def test_generic_engine_contains_no_bushel_defaults():
    for path in PACKAGE.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in FORBIDDEN_IN_ENGINE:
            assert token not in text, f"{token} in {path.name}"


def test_pier_plan_reads_the_model():
    wave = _wave()
    assert _ids(wave.plan).count("P1") == 1
    pier_ids = [element["id"] for element in wave.plan.elements if element["element_class"] == "supports"]
    assert pier_ids == [item[0] for item in PIER_COORDINATES]
    assert len(pier_ids) == 15
    placed = next(element for element in wave.plan.elements if element["id"] == "P8")
    assert placed["projected_geometry"]["coordinates"][0]["u"] == -9.0
    assert placed["projected_geometry"]["coordinates"][0]["v"] == 8.5
    assert all(
        element["source_geometry"]["coordinates"][0]["z"] == 0
        for element in wave.plan.elements
        if element["element_class"] == "supports"
    )


def test_framing_plan_uses_known_stations_and_elevations_refuse_them():
    accepted = assess_construction_model(proving_model()).accepted
    joists = [item for item in accepted["members"] if item["role"] == "joist"]
    assert len(joists) == 16
    assert joists[0]["geometry"]["unknown"] == ["z"]
    assert joists[0]["geometry"]["known"] == ["x", "y"]
    wave = _wave()
    assert "joist-1" in _ids(wave.plan)
    assert "joist-1" not in _ids(wave.front_elevation)
    assert "joist-1" not in _ids(wave.side_elevation)
    framing = next(view for view in wave.details if view.view_id == "framing-plan")
    assert framing.projected is True
    assert _ids(framing) == ["joist-1"]
    assert any(
        "The elevation of member joist-1 for the front elevation" in message
        for message in _messages(wave.front_elevation.issues)
    )


def test_elevations_read_the_same_complete_geometry():
    wave = _wave()
    complete = {"lower-walking-surface", *(item[0] for item in PIER_COORDINATES)}
    assert complete <= set(_ids(wave.plan))
    assert set(_ids(wave.front_elevation)) == complete
    assert set(_ids(wave.side_elevation)) == complete
    surface = next(element for element in wave.front_elevation.elements if element["id"] == "lower-walking-surface")
    assert {point["v"] for point in surface["projected_geometry"]["coordinates"]} == {1}


def test_stair_view_refuses_missing_facts():
    stair = _wave().stairs[0]
    assert stair.projected is False
    assert stair.elements == ()
    text = " ".join(_messages(stair.issues))
    assert "You need to provide this information." in text
    for fact in (
        "The stair rise",
        "The stair run",
        "The stair nosing",
        "The tread count",
        "The elevation of member stringer-1 for the stair",
    ):
        assert fact in text
    assert "The stair throat" not in text
    assert "The stringer count" not in text
    assert "The stair width" not in text


def test_section_reads_only_modeled_members():
    section = _wave().sections[0]
    assert section.projected is True
    assert _ids(section) == ["lower-walking-surface"]
    assert "P1" not in _ids(section)
    assert "stringer-1" not in _ids(section)


def test_details_read_the_model_and_refuse_missing_facts():
    details = {view.view_id: view for view in _wave().details}
    assert details["pier-bracket"].projected is False
    assert any(
        "The bracket for this detail" in message for message in _messages(details["pier-bracket"].issues)
    )
    assert details["guard-balusters"].projected is False
    assert any(
        "The baluster_layout for this detail" in message
        for message in _messages(details["guard-balusters"].issues)
    )
    assert details["stringer-cut"].projected is False
    assert details["stringer-cut"].elements == ()


def test_schedule_reads_the_model():
    schedule = _wave().schedule
    assert schedule.produced is True
    rows = {row["id"]: row for row in schedule.members}
    assert rows["lower-walking-surface"]["role"] == "decking"
    assert rows["lower-walking-surface"]["lengths"] == (10, 3)
    assert rows["lower-walking-surface"]["length_displays"] == ("10'-0\"", "3'-0\"")
    assert rows["joist-1"]["lengths"] == ()
    assert rows["stringer-1"]["role"] == "stringer"
    assert [row["id"] for row in schedule.supports] == [item[0] for item in PIER_COORDINATES]
    assert all(row["kind"] == "pier" for row in schedule.supports)
    names = [item["name"] for item in schedule.materials]
    assert TREAD_BOARDS in names
    assert VERANDA_KIT in names
    values = {item["id"]: item for item in schedule.dimensions}
    assert values["gate-clear"]["value"] == 42
    assert values["gate-clear"]["display"] == '42"'
    assert values["lower-walking-surface-height"]["display"] == '12"'
    assert schedule.levels[0]["display"] == "1'-0\""


def test_missing_facts_do_not_become_geometry():
    model = proving_model()
    roles = {item["role"] for item in model["members"]}
    assert "post" not in roles
    assert "baluster" not in roles
    for support in model["supports"]:
        point = support["geometry"]["coordinates"][0]
        assert point["z"] == 0
        assert support["geometry"]["kind"] == "point"
    for member in model["members"]:
        if member["role"] in {"joist", "stringer"}:
            assert "z" not in member["geometry"]["coordinates"][0]
            continue
        for point in member["geometry"]["coordinates"]:
            assert point["z"] >= 0
    for fact in WITHHELD:
        assert fact
    wave = _wave()
    assert "joist-1" in _ids(wave.plan)
    assert "stringer-1" in _ids(wave.plan)
    assert "stringer-1" not in _ids(wave.front_elevation)
    assert "joist-1" not in _ids(wave.side_elevation)


def test_model_revision_propagates_to_every_view():
    original = _wave()
    revised = proving_model()
    revised["supports"][7]["geometry"]["coordinates"][0]["x"] = -8
    updated = _wave(revised)
    assert _element_u(original.plan, "P8") == -9
    assert _element_u(updated.plan, "P8") == -8
    assert _element_u(updated.front_elevation, "P8") == -8
    assert _ids(updated.front_elevation) == _ids(updated.side_elevation)
    assert "joist-1" in _ids(updated.plan)
    assert "joist-1" not in _ids(updated.front_elevation)


def test_multiple_sheets_are_deterministic_and_11x17():
    first = _composed()
    second = _composed()
    assert first.composed is True
    assert first.pdf_bytes == second.pdf_bytes
    assert first.manifest["pdf_sha256"] == second.manifest["pdf_sha256"]
    kinds = [page["kind"] for page in first.manifest["pages"]]
    assert kinds[0] == "orthographic"
    assert "section" in kinds
    assert kinds[-1] == "schedule"
    reader = PdfReader(BytesIO(first.pdf_bytes))
    assert first.manifest["sheet_count"] == len(reader.pages)
    assert all(page["sheet_count"] == first.manifest["sheet_count"] for page in first.manifest["pages"])
    for page in reader.pages:
        box = page.mediabox
        assert float(box.width) == 1224
        assert float(box.height) == 792
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    assert "Linda Bushel pool deck" in text
    assert ADDRESS in text
    assert STATED_SCALE in text
    assert "Revision P" in text
    assert "PRELIMINARY CONSTRUCTION DRAWING" in text
    moved = _composed(sheet=sheet_definition(scale=SCALE_THAT_DOES_NOT_FIT))
    assert moved.composed is True
    assert moved.pdf_bytes is not None
    assert moved.manifest["scale"] == SCALE_THAT_DOES_NOT_FIT
    assert moved.manifest["points_per_unit"] == 27
    assert "front_elevation" in [page["kind"] for page in moved.manifest["pages"]]
    assert "Sheet 1 of" in "\n".join(
        page.extract_text() or "" for page in PdfReader(BytesIO(moved.pdf_bytes)).pages
    )


def test_proving_set_does_not_write_project_plan_or_estimate():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-bushel-proving",
            "WTF_CSRF_ENABLED": False,
        }
    )
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        projects_before = Project.query.count()
        plans_before = PlanDocument.query.count()
        estimates_before = Estimate.query.count()
        result = _composed()
        assert result.composed is True
        assert Project.query.count() == projects_before
        assert PlanDocument.query.count() == plans_before
        assert Estimate.query.count() == estimates_before


def _element_u(view, identifier):
    element = next(item for item in view.elements if item["id"] == identifier)
    return element["projected_geometry"]["coordinates"][0]["u"]
