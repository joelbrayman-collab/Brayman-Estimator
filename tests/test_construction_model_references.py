"""Slice 13: callouts, sheet references, schedules, and issue status."""

from __future__ import annotations

import copy
from io import BytesIO

from pypdf import PdfReader

from app import create_app, db
from app.models import Estimate, Project
from app.plan_intelligence.models import PlanDocument
from app.services.construction_model.annotations import build_attribute_callouts
from app.services.construction_model.sheet import (
    _schedule_lines,
    _schedule_pages,
    build_sheet_references,
    compose_construction_wave,
)
from app.services.construction_model.views import (
    group_member_rows,
    group_relationship_rows,
    project_construction_wave,
)
from app.services.organizations import ensure_default_organization
from tests.fixtures.construction_model.complete_deck_fixture import (
    deck_model,
    detail_requests,
    section_requests,
    sheet_definition,
    sheet_program,
)


def _set(number="1"):
    definition = sheet_definition()
    definition["sheet_number"] = number
    return compose_construction_wave(
        deck_model(),
        definition,
        sections=section_requests(),
        details=detail_requests(),
        sheet_program=sheet_program(),
    )


def _text(result) -> str:
    return "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(result.pdf_bytes)).pages)


def _wave():
    return project_construction_wave(
        deck_model(), sections=section_requests(), details=detail_requests()
    )


def test_member_callouts_reference_model_ids():
    wave = _wave()
    plan = wave.plan
    known = {element["id"] for element in plan.elements}
    callouts = build_attribute_callouts(plan.elements, 0, 0, 36, 40, 160, deck_model())
    assert callouts
    for callout in callouts:
        assert callout["element_ids"]
        assert set(callout["element_ids"]) <= known
        assert callout["leader"] is True


def test_grouped_callouts_stay_traceable():
    wave = _wave()
    plan = wave.plan
    callouts = build_attribute_callouts(plan.elements, 0, 0, 36, 40, 160, deck_model())
    grouped = [item for item in callouts if len(item["element_ids"]) > 1]
    assert grouped
    covered = [identifier for item in callouts for identifier in item["element_ids"]]
    assert len(covered) == len(set(covered))


def test_section_marker_names_the_real_section_sheet():
    result = _set()
    assert result.composed is True, [issue.message for issue in result.issues]
    section = next(page for page in result.manifest["pages"] if page["kind"] == "section")
    text = _text(result)
    assert f"SEE SHEET {section['sheet_number']}" in text
    assert "Section A" in text or "SECTION A" in text


def test_detail_marker_names_the_real_detail_sheet():
    result = _set()
    detail = next(
        page
        for page in result.manifest["pages"]
        if page["kind"] == "detail" and "post-1" in page["element_ids"]
    )
    text = _text(result)
    assert "Post and beam" in text
    assert f"SHEET {detail['sheet_number']}" in text


def test_sheet_number_changes_update_references():
    first = _set("1")
    moved = _set("9")
    first_section = next(page for page in first.manifest["pages"] if page["kind"] == "section")
    moved_section = next(page for page in moved.manifest["pages"] if page["kind"] == "section")
    assert first_section["sheet_number"] != moved_section["sheet_number"]
    assert f"SEE SHEET {first_section['sheet_number']}" in _text(first)
    assert f"SEE SHEET {moved_section['sheet_number']}" in _text(moved)
    assert f"SEE SHEET {first_section['sheet_number']}" not in _text(moved)


def test_schedule_columns_are_deterministic():
    schedule = _wave().schedule
    assert _schedule_lines(schedule) == _schedule_lines(schedule)
    joined = "\n".join(line[1] for line in _schedule_lines(schedule))
    assert "Item    Role    Size    Material    Quantity    Length    Status    Reference" in joined
    assert "Connection    Members    Relationship    Connector    Fastener    Quantity    Geometry    Reference" in joined
    assert "Item    Description    Material    Quantity    Unit    Status    Reference" in joined


def test_schedule_headings_repeat_when_a_section_continues():
    from types import SimpleNamespace

    schedule = SimpleNamespace(
        materials=(),
        measurement_system="imperial",
        members=(),
        connections=(),
        supports=(),
        relationships=(),
        levels=(),
        dimensions=[{"id": f"d-{index}", "display": "1'-0\"", "value": 1} for index in range(40)],
        dimension_chains=(),
        issues=(),
    )
    pages = _schedule_pages(schedule)
    assert len(pages) > 1
    continued = [
        page
        for page in pages
        if any(line[1].startswith("d-") for line in page["lines"])
    ]
    assert len(continued) > 1
    for page in continued:
        assert any(line[1] == "Dimension" and line[0] == "Helvetica-Bold" for line in page["lines"])


def test_equivalent_members_group_and_different_lengths_stay_separate():
    rows = group_member_rows(
        (
            {"id": "j-a", "role": "joist", "member_size": "2x8", "material_id": "m", "lengths": (10,)},
            {"id": "j-b", "role": "joist", "member_size": "2x8", "material_id": "m", "lengths": (10,)},
            {"id": "j-c", "role": "joist", "member_size": "2x8", "material_id": "m", "lengths": (12,)},
        )
    )
    assert len(rows) == 2
    ten = next(row for row in rows if row["quantity"] == 2)
    twelve = next(row for row in rows if row["quantity"] == 1)
    assert set(ten["member_ids"]) == {"j-a", "j-b"}
    assert twelve["member_ids"] == ("j-c",)
    assert ten["length_display"] != twelve["length_display"]


def test_relationship_schedule_has_one_state_per_pair():
    model = deck_model()
    members = {item["id"]: item for item in model["members"]}
    members.update({item["id"]: item for item in model["supports"]})
    rows = group_relationship_rows(model["relationships"], members, model["connections"])
    seen = {}
    for row in rows:
        for source, target in zip(row["from_ids"], row["to_ids"]):
            pair = (source, target)
            assert pair not in seen
            seen[pair] = row
    post = seen[("post-1", "beam-front")]
    assert post["bearing"] == "supplied"
    assert post["missing"] == ""
    assert "0'-3\"" in post["contact"]
    missing = [row for row in rows if row["bearing"] == "not supplied"]
    assert missing
    assert all(row["missing"] == "bearing not supplied" for row in missing)
    assert any(row["bearing"] == "supplied" for row in rows)


def test_unresolved_required_content_is_marked_not_issued():
    result = _set()
    text = _text(result)
    assert "NOT ISSUED" in text
    assert "You need to provide this information." in text
    assert "GENERATED" in text


def test_sheet_index_matches_generated_sheets():
    result = _set()
    pages = result.manifest["pages"]
    text = _text(result)
    assert "DRAWING INDEX" in text
    assert pages[-1]["kind"] == "index"
    for page in pages:
        assert page["sheet_number"] in text
    assert len(pages) == result.manifest["sheet_count"]


def test_references_follow_the_sheet_set_and_are_not_stored():
    import app.services.construction_model.annotations as annotations
    import app.services.construction_model.sheet as sheet_mod
    import app.services.construction_model.views as views

    before = {
        name: (id(value), len(value))
        for module in (annotations, sheet_mod, views)
        for name, value in vars(module).items()
        if isinstance(value, (list, dict, set))
    }
    view = type(
        "View",
        (),
        {
            "view_id": "A",
            "label": "Section A",
            "elements": [{"id": "post-1"}],
            "facts": (("section_direction", "y"), ("section_location", 1.0)),
        },
    )()
    pages = [{"kind": "section", "title": "Section A", "view": view}]
    low = build_sheet_references(pages, ["4"])
    high = build_sheet_references(pages, ["12"])
    assert low[0]["target_id"] == "A"
    assert low[0]["sheet_number"] == "4"
    assert high[0]["sheet_number"] == "12"
    assert low[0]["section_direction"] == "y"
    _set()
    after = {
        name: (id(value), len(value))
        for module in (annotations, sheet_mod, views)
        for name, value in vars(module).items()
        if isinstance(value, (list, dict, set))
    }
    assert before == after


def test_composition_does_not_invent_fixture_facts_or_write_records():
    model = deck_model()
    snapshot = copy.deepcopy(model)
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        before = (Project.query.count(), PlanDocument.query.count(), Estimate.query.count())
        result = compose_construction_wave(
            model,
            sheet_definition(),
            sections=section_requests(),
            details=detail_requests(),
            sheet_program=sheet_program(),
        )
        after = (Project.query.count(), PlanDocument.query.count(), Estimate.query.count())
    assert model == snapshot
    assert before == after == (0, 0, 0)
    assert result.composed is True
