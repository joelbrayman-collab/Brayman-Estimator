"""Paper-space callouts, dimension chains, and required-view placement."""

from __future__ import annotations

from app.services.construction_model import assess_construction_model, compose_construction_wave
from app.services.construction_model.annotations import (
    build_refusal_callouts,
    build_station_callouts,
    place_callouts,
    rectangles_overlap,
)
from app.services.construction_model.dimensions import resolve_dimension_chains
from app.services.construction_model.model import format_measure
from app.services.construction_model.sheet import CODE_VIEW_CANNOT_BE_PLACED


def _provenance():
    return {"source": "project_input", "reference": "annotation test"}


def _point(x, y, z=None):
    coordinate = {"x": x, "y": y}
    if z is not None:
        coordinate["z"] = z
    return {"kind": "point", "coordinates": [coordinate]}


def _element(identifier, role, x, y, z=None):
    record = {
        "id": identifier,
        "projected_geometry": {"coordinates": [{"u": x, "v": y}]},
        "provenance": _provenance(),
        "uncertainty": (),
    }
    if role == "pier":
        record["kind"] = role
    else:
        record["role"] = role
    return record


def _model():
    return {
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
                "geometry": _point(0, 1),
                "provenance": _provenance(),
            },
            {
                "id": "joist-2",
                "role": "joist",
                "geometry": _point(4, 1),
                "provenance": _provenance(),
            },
            {
                "id": "beam-a",
                "role": "beam",
                "geometry": {
                    "kind": "segment",
                    "coordinates": [
                        {"x": 0, "y": 1, "z": 2},
                        {"x": 10, "y": 1, "z": 2},
                    ],
                },
                "provenance": _provenance(),
            },
        ],
        "supports": [
            {
                "id": "pier-a",
                "kind": "pier",
                "geometry": _point(0, 1, 0),
                "provenance": _provenance(),
                "uncertainty": (),
            }
        ],
        "dimension_chains": [
            {
                "id": "joist-stations",
                "axis": "x",
                "kind": "station",
                "references": ["joist-1", "joist-2"],
                "provenance": _provenance(),
            },
            {
                "id": "beam-length",
                "axis": "x",
                "kind": "member_length",
                "references": ["beam-a"],
                "provenance": _provenance(),
            },
            {
                "id": "walk-level",
                "axis": "z",
                "kind": "level",
                "references": ["walk"],
                "provenance": _provenance(),
            },
            {
                "id": "missing-joist-elevation",
                "axis": "z",
                "kind": "point_to_point",
                "references": ["joist-1", "joist-2"],
                "provenance": _provenance(),
            },
        ],
    }


def _sheet():
    return {
        "paper": "11x17",
        "scale": "1/4 in = 1 ft",
        "organization_name": "Brayman Construction",
        "project_name": "Annotation deck",
        "address": "12 Example Road",
        "drawing_title": "Construction drawing",
        "sheet_number": "1",
        "revision": "A",
        "date": "2026-10-02",
    }


def test_callout_names_the_model_elements():
    elements = [_element("joist-1", "joist", 0, 0), _element("joist-2", "joist", 0, 0)]
    callouts = build_station_callouts(elements, 0, 0, 18, 100, 100)
    assert callouts[0]["element_ids"] == ("joist-1", "joist-2")
    assert "joist-1 to joist-2" in callouts[0]["text"]


def test_paper_callout_can_move_without_moving_model_geometry():
    element = _element("joist-1", "joist", 4, 8)
    other = _element("joist-2", "joist", 4, 8)
    before = (
        element["projected_geometry"]["coordinates"][0]["u"],
        element["projected_geometry"]["coordinates"][0]["v"],
    )
    callouts = build_station_callouts([element, other], 0, 0, 18, 40, 40)
    placed, refused = place_callouts(callouts, [], (0, 0, 400, 400))
    assert refused == []
    placed[0]["paper_x"] += 80
    assert element["projected_geometry"]["coordinates"][0]["u"] == before[0]
    assert element["projected_geometry"]["coordinates"][0]["v"] == before[1]
    assert placed[0]["geometry_reference"] == {"u": 4, "v": 8}


def test_nearby_elements_share_one_readable_callout():
    elements = [
        _element("joist-1", "joist", 0, 0),
        _element("joist-2", "joist", 1, 0),
        _element("joist-3", "joist", 2, 0),
        _element("joist-4", "joist", 3, 0),
        _element("joist-5", "joist", 4, 0),
    ]
    callouts = build_station_callouts(elements, 0, 0, 18, 0, 0)
    assert len(callouts) == 1
    assert callouts[0]["text"].split("\n")[0] == "5 JOISTS"
    assert "joist-1 to joist-5" in callouts[0]["text"]


def test_callouts_do_not_overlap_when_a_clear_place_exists():
    callouts = [
        {"id": "group-1", "text": "2 PIERS\npier-a, pier-b", "anchor_x": 10, "anchor_y": 10, "justification": "left"},
        {"id": "group-2", "text": "2 JOISTS\njoist-1 to joist-2", "anchor_x": 12, "anchor_y": 12, "justification": "left"},
    ]
    placed, refused = place_callouts(callouts, [], (0, 0, 500, 500))
    assert refused == []
    assert not rectangles_overlap(
        (placed[0]["paper_x"], placed[0]["paper_y"], placed[0]["paper_x"] + placed[0]["width"], placed[0]["paper_y"] + placed[0]["height"]),
        (placed[1]["paper_x"], placed[1]["paper_y"], placed[1]["paper_x"] + placed[1]["width"], placed[1]["paper_y"] + placed[1]["height"]),
    )


def test_callout_is_refused_when_it_cannot_avoid_a_collision():
    obstacle = (0, 0, 80, 40)
    callouts = [{"id": "group-1", "text": "2 PIERS\npier-a, pier-b", "justification": "left"}]
    placed, refused = place_callouts(callouts, [obstacle], (0, 0, 80, 40))
    assert placed == []
    assert refused[0]["id"] == "group-1"


def test_missing_elevation_notes_stay_readable_and_keep_ids():
    class Issue:
        def __init__(self, message):
            self.message = message

    issues = [
        Issue("You need to provide this information. The elevation of member joist-1 for the front elevation."),
        Issue("You need to provide this information. The elevation of member joist-2 for the front elevation."),
        Issue("You need to provide this information. The elevation of member joist-3 for the front elevation."),
    ]
    callouts = build_refusal_callouts(issues)
    assert len(callouts) == 1
    assert callouts[0]["element_ids"] == ("joist-1", "joist-2", "joist-3")
    assert callouts[0]["text"].startswith("You need to provide this information.")
    assert "joist-1 to joist-3" in callouts[0]["text"]
    section = build_refusal_callouts(
        [
            Issue("You need to provide this information. The elevation of member joist-1 for section cut-a."),
            Issue("You need to provide this information. The elevation of member joist-2 for section cut-a."),
        ]
    )
    assert len(section) == 1
    assert "joist-1 to joist-2" in section[0]["text"]


def test_dimension_chain_reads_the_model_and_refuses_a_missing_station():
    accepted = assess_construction_model(_model()).accepted
    resolved = {item["id"]: item for item in resolve_dimension_chains(accepted)}
    stations = resolved["joist-stations"]
    assert stations["segments"][0]["start_id"] == "joist-1"
    assert stations["segments"][0]["end_id"] == "joist-2"
    assert stations["segments"][0]["display"] == "4'-0\""
    assert stations["overall"]["display"] == "4'-0\""
    assert resolved["beam-length"]["segments"][0]["display"] == "10'-0\""
    missing = resolved["missing-joist-elevation"]["segments"][0]
    assert missing["refused"] is True
    assert missing["display"] is None
    assert missing["message"] == (
        "You need to provide this information. "
        "The elevation of member joist-1 and member joist-2 for dimension chain missing-joist-elevation."
    )


def test_level_dimension_updates_when_the_model_level_changes():
    model = _model()
    first = resolve_dimension_chains(assess_construction_model(model).accepted)
    level = next(item for item in first if item["id"] == "walk-level")
    assert level["overall"]["display"] == "1'-0\""
    assert level["overall"]["value"] == 1
    model["levels"][0]["elevation"] = 2
    second = resolve_dimension_chains(assess_construction_model(model).accepted)
    updated = next(item for item in second if item["id"] == "walk-level")
    assert updated["overall"]["display"] == "2'-0\""
    assert updated["overall"]["source_id"] == "walk"


def test_chain_value_updates_when_the_model_point_moves():
    model = _model()
    model["members"][1]["geometry"]["coordinates"][0]["x"] = 5
    resolved = resolve_dimension_chains(assess_construction_model(model).accepted)
    stations = next(item for item in resolved if item["id"] == "joist-stations")
    assert stations["segments"][0]["display"] == "5'-0\""


def test_uncertain_dimension_keeps_the_uncertainty():
    model = _model()
    model["uncertainty"] = [{"code": "field", "note": "FIELD VERIFICATION REQUIRED", "subject_id": "joist-1"}]
    segment = resolve_dimension_chains(assess_construction_model(model).accepted)[0]["segments"][0]
    assert segment["display"] == "4'-0\""
    assert segment["uncertainty"][0]["note"] == "FIELD VERIFICATION REQUIRED"


def test_required_view_moves_to_another_sheet_without_changing_scale():
    model = _model()
    model["members"][2]["geometry"]["coordinates"][1]["x"] = 30
    result = compose_construction_wave(model, _sheet())
    assert result.composed is True
    kinds = [page["kind"] for page in result.manifest["pages"]]
    assert "front_elevation" in kinds
    assert result.manifest["points_per_unit"] == 18
    assert result.manifest["scale"] == "1/4 in = 1 ft"
    numbers = [page["sheet_number"] for page in result.manifest["pages"]]
    assert numbers == [str(index) for index in range(1, len(numbers) + 1)]


def test_required_view_never_disappears_and_scale_is_not_changed():
    sheet = _sheet()
    sheet["scale"] = "4/1 in = 1 ft"
    result = compose_construction_wave(assess_construction_model(_model()).accepted, sheet)
    assert result.composed is False
    assert result.pdf_bytes is None
    assert result.manifest["points_per_unit"] == 288
    assert result.issues[0].code == CODE_VIEW_CANNOT_BE_PLACED
    assert any(issue.field == "plan" for issue in result.issues)


def test_construction_notation_is_not_a_bare_decimal():
    assert format_measure(10, "imperial") == "10'-0\""
    assert format_measure(3.5, "imperial") == "3'-6\""
    assert format_measure(12, "imperial", "in") == '12"'
    assert format_measure(3, "metric") == "3 m"
    assert format_measure(12, "metric", "mm") == "12 mm"
