"""Physical profiles, buildable details, and grouped construction schedules."""

from __future__ import annotations

import copy

from app import create_app, db
from app.models import Estimate, Project
from app.plan_intelligence.models import PlanDocument
from app.services.construction_model.model import view_profile
from app.services.construction_model.sheet import _schedule_lines
from app.services.construction_model.views import group_member_rows
from app.services.organizations import ensure_default_organization
from tests.fixtures.construction_model.complete_deck_fixture import (
    deck_model,
    section_requests,
    sheet_program,
)
from tests.test_construction_model_deck_fixture import _set, _wave


def _span(element, key):
    values = [point[key] for point in element["profile_geometry"]["coordinates"]]
    return max(values) - min(values)


def test_physical_member_profile_can_be_represented():
    item = {
        "profile_type": "rectangular",
        "section_width": 0.5,
        "section_depth": 0.5,
        "geometry": {
            "kind": "segment",
            "coordinates": [
                {"x": 1, "y": 1, "z": 0},
                {"x": 1, "y": 1, "z": 2},
            ],
        },
    }
    profile = view_profile(item, "x", "z")
    assert profile is not None
    assert len({(round(point["u"], 4), round(point["v"], 4)) for point in profile["coordinates"]}) >= 4
    bare = {"geometry": item["geometry"]}
    assert view_profile(bare, "x", "z") is None


def test_sloped_member_profile_projects_as_a_board():
    item = {
        "profile_type": "rectangular",
        "orientation": "top_edge",
        "section_width": 2 / 12,
        "section_depth": 1,
        "geometry": {
            "kind": "segment",
            "coordinates": [
                {"x": 0, "y": 0, "z": 1},
                {"x": 0, "y": 1, "z": 0},
            ],
        },
    }
    profile = view_profile(item, "y", "z")
    assert profile is not None
    unique = {(round(point["u"], 4), round(point["v"], 4)) for point in profile["coordinates"]}
    assert len(unique) >= 4
    heights = [point["v"] for point in profile["coordinates"]]
    assert max(heights) - min(heights) > 1.2
    plan = view_profile(item, "x", "y")
    widths = [point["u"] for point in plan["coordinates"]]
    assert abs((max(widths) - min(widths)) - (2 / 12)) < 0.02
    without_size = dict(item)
    without_size.pop("section_width")
    without_size.pop("section_depth")
    assert view_profile(without_size, "y", "z") is None


def test_stair_detail_uses_the_physical_member_and_the_supplied_result():
    wave = _wave()
    stair = next(element for element in wave.stairs[0].elements if element["id"] == "stringer-1")
    center = [point["v"] for point in stair["projected_geometry"]["coordinates"]]
    assert stair["profile_geometry"] is not None
    assert _span(stair, "v") > (max(center) - min(center)) + 0.4
    detail = next(item for item in wave.details if item.view_id == "stringer-tread")
    assert detail.projected is True
    assert {element["id"] for element in detail.elements} == {"stringer-2", "tread-3"}
    assert all(element.get("profile_geometry") for element in detail.elements)
    assert ("stringer_count", 3) in detail.facts
    assert ("stair_width", 36) in detail.facts
    assert ("rise", 7) in detail.facts
    assert ("run", 11) in detail.facts


def test_post_beam_detail_reads_the_model_connection():
    wave = _wave()
    detail = next(item for item in wave.details if item.view_id == "post-beam")
    assert [element["id"] for element in detail.elements] == ["post-1", "beam-front"]
    assert all(element.get("profile_geometry") for element in detail.elements)
    us = []
    vs = []
    for element in detail.elements:
        for point in element["projected_geometry"]["coordinates"]:
            us.append(point["u"])
            vs.append(point["v"])
    assert max(us) - min(us) <= 2.01
    assert max(vs) - min(vs) <= 2.01
    connection = next(item for item in wave.schedule.connections if item["id"] == "connection-post-beam")
    assert set(connection["participant_ids"]) == {"post-1", "beam-front"}
    assert connection["connector"] == "fixture post cap"
    assert connection["quantity"] == 2


def test_section_reads_physical_profiles_and_names_a_missing_one():
    section = _wave().sections[0]
    beam = next(element for element in section.elements if element["id"] == "beam-front")
    post = next(element for element in section.elements if element["id"] == "post-1")
    joist = next(element for element in section.elements if element["role"] == "joist")
    deck = next(element for element in section.elements if element["role"] == "decking")
    assert beam["profile_geometry"] is not None
    assert _span(beam, "v") > 0.7
    assert post["profile_geometry"] is not None
    assert joist["profile_geometry"] is not None
    assert deck["profile_geometry"] is not None
    model = copy.deepcopy(deck_model())
    joist = next(member for member in model["members"] if member["id"] == "joist-1")
    joist.pop("section_width")
    joist.pop("section_depth")
    from app.services.construction_model import project_construction_wave

    refused = project_construction_wave(model, sections=section_requests(), details=())
    messages = " ".join(issue.message for issue in refused.sections[0].issues)
    assert "section width and section depth of member joist-1" in messages
    drawn = next(element for element in refused.sections[0].elements if element["id"] == "joist-1")
    assert drawn.get("profile_geometry") is None


def test_equivalent_members_group_and_different_lengths_stay_separate():
    rows = group_member_rows(_wave().schedule.members, "imperial")
    joists = [row for row in rows if row["role"] == "joist"]
    assert len(joists) == 1
    assert joists[0]["quantity"] == 8
    assert joists[0]["member_size"] == "2x8"
    assert joists[0]["length_display"] == "10'-0\""
    assert "joist-1" not in joists[0]["length_display"]
    rims = [row for row in rows if row["role"] == "rim"]
    lengths = {row["length_display"] for row in rims}
    assert len(lengths) > 1
    assert "10'-0\"" in lengths
    assert "4'-6\"" in lengths
    values = []
    for row in rims:
        feet, inches = row["length_display"].replace('"', "").split("'-")
        values.append(int(feet) + int(inches) / 12)
    assert round(sum(values) / len(values), 2) not in {round(value, 2) for value in values}


def test_schedule_changes_when_the_model_changes_and_has_no_price():
    original = group_member_rows(_wave().schedule.members, "imperial")
    original_joists = next(row for row in original if row["role"] == "joist")
    changed = copy.deepcopy(deck_model())
    changed["members"] = [member for member in changed["members"] if member["id"] != "joist-8"]
    changed["relationships"] = [
        item
        for item in changed["relationships"]
        if item.get("from_id") != "joist-8" and item.get("to_id") != "joist-8"
    ]
    for chain in changed["dimension_chains"]:
        chain["references"] = [item for item in chain["references"] if item != "joist-8"]
    from app.services.construction_model import project_construction_wave

    updated = project_construction_wave(changed, sections=(), details=())
    joists = next(row for row in group_member_rows(updated.schedule.members, "imperial") if row["role"] == "joist")
    assert joists["quantity"] == original_joists["quantity"] - 1
    assert "joist-8" not in joists["member_ids"]
    lines = _schedule_lines(updated.schedule)
    text = "\n".join(line for _font, line in lines).lower()
    assert "connection / hardware schedule" in text
    assert "fixture post cap" in text
    assert "fixture bolt" in text
    assert "material / component schedule" in text
    assert "each" in text
    for banned in ("$", "price", "cost", "estimate", "total"):
        assert banned not in text
    assert not hasattr(updated.schedule, "store")


def test_guard_detail_projects_the_supplied_members():
    detail = next(item for item in _wave().details if item.view_id == "guard-gate")
    assert detail.projected is True
    identifiers = {element["id"] for element in detail.elements}
    assert {"guard-left-a", "gate-1", "guard-left-b"} <= identifiers
    assert all(element.get("profile_geometry") for element in detail.elements if element["id"] in identifiers)


def test_buildable_set_does_not_write_project_plan_or_estimate():
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        before = (Project.query.count(), PlanDocument.query.count(), Estimate.query.count())
        composed = _set()
        after = (Project.query.count(), PlanDocument.query.count(), Estimate.query.count())
        assert before == after == (0, 0, 0)
    assert composed.composed is True, [issue.message for issue in composed.issues]
    assert "3 in = 1 ft" in {page.get("scale") for page in sheet_program()}
    schedule_text = "\n".join(line for _font, line in _schedule_lines(_wave().schedule))
    assert "MEMBER SCHEDULE" in schedule_text
    assert "CONNECTION / HARDWARE SCHEDULE" in schedule_text
    assert "joist-1    joist" not in schedule_text
    assert "8    10'-0\"" in schedule_text
