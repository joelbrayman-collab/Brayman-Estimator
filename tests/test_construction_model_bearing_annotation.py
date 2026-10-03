"""Slice 18: bearing words move in paper space. The contact stays."""

from __future__ import annotations

import copy
from io import BytesIO

from pypdf import PdfReader

from app.services.construction_model.annotations import (
    _segment_hits_rect,
    bearing_annotation,
    group_bearing_annotations,
    place_margin_callouts,
    rectangles_overlap,
    route_leader,
)
from app.services.construction_model.sheet import compose_construction_wave
from tests.fixtures.construction_model.complete_deck_fixture import (
    deck_model,
    detail_requests,
    section_requests,
    sheet_definition,
    sheet_program,
)


def _set(model=None):
    return compose_construction_wave(
        deck_model() if model is None else model,
        sheet_definition(),
        sections=section_requests(),
        details=detail_requests(),
        sheet_program=sheet_program(),
    )


def _text(result) -> str:
    reader = PdfReader(BytesIO(result.pdf_bytes))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _note():
    return bearing_annotation(
        {
            "relationship_id": "rel-bear-post-1-beam-front",
            "kind": "bears_on",
            "from_id": "post-1",
            "to_id": "beam-front",
            "label": "0'-3\"",
        },
        ((510, 475), (545, 475)),
    )


def test_bearing_words_move_and_the_model_stays():
    model = deck_model()
    before = copy.deepcopy(model)
    result = _set(model)
    assert result.composed is True
    assert model["members"] == before["members"]
    assert model["relationships"] == before["relationships"]
    text = _text(result)
    assert 'BEARING 0\'-3"' in text
    assert "post-1 bears on beam-front" in text
    assert "rel-bear-post-1-beam-front" in text


def test_bearing_note_stays_linked_and_off_the_joint():
    note = _note()
    assert note["element_ids"] == ("post-1", "beam-front")
    assert "rel-bear-post-1-beam-front" in note["text"]
    assert note["member_points"] == ((510, 475), (545, 475))
    post = (500, 300, 560, 480)
    beam = (500, 470, 760, 560)
    frame = (40, 160, 1184, 748)
    placed, refused = place_margin_callouts([note], [post, beam], frame, (500, 300, 760, 560))
    assert refused == []
    item = placed[0]
    rect = (item["paper_x"], item["paper_y"], item["paper_x"] + item["width"], item["paper_y"] + item["height"])
    assert not rectangles_overlap(rect, post)
    assert not rectangles_overlap(rect, beam)
    unrelated = (600, 400, 700, 520)
    route = route_leader(
        (item["paper_x"], item["paper_y"] + item["height"] / 2),
        (527, 475),
        [unrelated],
        [],
        frame,
        [post, beam],
    )
    if route:
        for start, end in zip(route, route[1:]):
            assert not _segment_hits_rect(start, end, unrelated)


def test_equivalent_bearings_group_and_different_pairs_do_not():
    seats = []
    for stringer in (1, 2):
        for tread in range(1, 4):
            seats.append(
                bearing_annotation(
                    {
                        "relationship_id": f"rel-bear-stringer-{stringer}-tread-{tread}",
                        "kind": "bears_on",
                        "from_id": f"stringer-{stringer}",
                        "to_id": f"tread-{tread}",
                        "label": "0'-11\"",
                    },
                    ((0, tread), (1, tread)),
                )
            )
    pier = bearing_annotation(
        {
            "relationship_id": "rel-bear-pier-1-post-1",
            "kind": "bears_on",
            "from_id": "pier-1",
            "to_id": "post-1",
            "label": "0'-3\"",
        },
        ((0, 0), (1, 0)),
    )
    grouped = group_bearing_annotations([*seats, _note(), pier])
    assert len(grouped) == 3
    stair = next(item for item in grouped if "0'-11\"" in item["text"])
    assert stair["leader"] is False
    assert "stringer-1" in stair["text"]
    assert "stringer-2" in stair["text"]
    assert "rel-bear-stringer-1-tread-1" in stair["text"]
    assert "rel-bear-stringer-2-tread-3" in stair["text"]
    post = next(item for item in grouped if item["id"] == "bearing-rel-bear-post-1-beam-front")
    assert post["leader"] is True
    assert "pier-1" not in post["text"]
    pair = group_bearing_annotations(
        [
            bearing_annotation(
                {
                    "relationship_id": "rel-bear-post-1-beam-front",
                    "kind": "bears_on",
                    "from_id": "post-1",
                    "to_id": "beam-front",
                    "label": "0'-3\"",
                },
                ((0, 0), (3, 0)),
            ),
            bearing_annotation(
                {
                    "relationship_id": "rel-bear-post-2-beam-front",
                    "kind": "bears_on",
                    "from_id": "post-2",
                    "to_id": "beam-front",
                    "label": "0'-3\"",
                },
                ((10, 0), (13, 0)),
            ),
        ]
    )
    assert len(pair) == 1
    assert "post-1 to post-2 bears on beam-front" in pair[0]["text"]
    assert "beam-front, beam-front" not in pair[0]["text"]
    assert "rel-bear-post-1-beam-front" in pair[0]["text"]
    assert "rel-bear-post-2-beam-front" in pair[0]["text"]


def test_bearing_sheet_adds_no_fixture_fact():
    model = deck_model()
    roles = {item["role"] for item in model["members"]}
    assert roles.isdisjoint({"ledger", "landing", "hinge", "bottom_rail", "guard_post"})
    by_id = {item["id"]: item for item in model["connections"]}
    for identifier in (
        "connection-stringer-tread",
        "connection-beam-joist",
        "connection-stair-header",
        "connection-guard-gate",
    ):
        assert "connector_geometry" not in by_id[identifier]
    text = _text(_set())
    assert "GEOMETRY NOT SUPPLIED" in text
    assert "ledger" not in text.lower()
