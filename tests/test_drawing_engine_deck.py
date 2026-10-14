"""The deck drawing set agrees with the governed J1 geometry and takeoff.

Synthetic J1 construction model and synthetic product facts. Nothing is
stored. Every assertion compares the drawing to the takeoff or the model,
not to numbers typed into the test.
"""

from __future__ import annotations

import io
import math

import ezdxf
import pytest
from ezdxf import recover
from pypdf import PdfReader

import app.models  # noqa: F401  (load models before services)
from app.services.deck_takeoff import calculate_pool_deck_takeoff, read_basis
from app.services.deck_takeoff.geometry import CurvedDeck, pool_wall_x, upper_courses
from app.services.drawings.core import L_DECK, L_FOUND, Dim, Poly, Table, ft_in
from app.services.drawings.deck import STATUS, DeckDrawingInput, DeckDrawingSet
from app.services.drawings.dxf import render_dxf
from app.services.drawings.pdf import render_pdf
from tests.fixtures.construction_model.linda_j1_takeoff_fixture import model
from tests.test_deck_takeoff_linda_j1 import TEST_PRODUCT

SOURCE = {"project_id": 1, "construction_model_revision_number": 1, "construction_model_sha256": "a" * 64}


def _build(facts=TEST_PRODUCT, content=None):
    content = content or model()
    basis, missing = read_basis(content, SOURCE)
    assert missing == []
    takeoff = calculate_pool_deck_takeoff(basis, facts)
    lower = next(level["elevation"] for level in content["levels"] if level["id"] == "lower-walk") * 12.0
    data = DeckDrawingInput(
        basis=basis, takeoff=takeoff, facts=facts, project_name="Linda Bushel (synthetic)", project_address="Synthetic copy",
        model_revision="R1", drawing_revision="D1", date="2026-10-14", fingerprint="TESTSET", lower_walk_in=lower,
    )
    data.stair_results = content.get("stair_results")
    ds = DeckDrawingSet(data)
    return ds, ds.sheets(), basis, takeoff


@pytest.fixture(scope="module")
def built():
    return _build()


@pytest.fixture(scope="module")
def pdf_bytes(built):
    return render_pdf(built[1], title="test")


@pytest.fixture(scope="module")
def dxf_doc(built):
    data = render_dxf(built[1], title="test")
    doc, auditor = recover.read(io.BytesIO(data))
    return doc, auditor, data


def _sheet(sheets, number):
    return next(s for s in sheets if s.number == number)


def test_the_set_is_seven_11x17_vector_sheets_with_title_blocks(built, pdf_bytes):
    _ds, sheets, _b, _t = built
    reader = PdfReader(io.BytesIO(pdf_bytes), strict=True)
    assert len(reader.pages) == len(sheets) == 7
    for page in reader.pages:
        assert abs(float(page.mediabox.width) - 1224) < 0.5 and abs(float(page.mediabox.height) - 792) < 0.5
        assert "/Image" not in str(page.get("/Resources", {}).get("/XObject", {}))  # no raster drawing (no logo in this test)
    text = "\n".join(p.extract_text() or "" for p in reader.pages)
    assert text.count(STATUS) >= 7
    for number, title in [("A-1", "GENERAL ARRANGEMENT"), ("A-2", "DECKING LAYOUT"), ("S-1", "HELICAL PIER"), ("S-2", "FRAMING PLAN"),
                          ("A-3", "STAIR"), ("A-4", "ELEVATIONS"), ("G-1", "SCHEDULES")]:
        assert number in text and title in text


def test_plan_dimensions_are_the_models(built, pdf_bytes):
    _ds, _s, basis, takeoff = built
    text = "\n".join(p.extract_text() or "" for p in PdfReader(io.BytesIO(pdf_bytes)).pages)
    deck = CurvedDeck(basis.pool_radius_ft, basis.upper_width_ft, basis.upper_clear_depth_ft)
    assert ft_in(basis.upper_width_ft * 12) in text  # 18'-0"
    assert ft_in(basis.pool_radius_ft * 24) in text  # 21'-0" pool
    assert ft_in(deck.side_length_ft * 12) in text  # side to the pool
    assert ft_in(basis.stair_width_ft * 12) in text
    assert ft_in(basis.lower_depth_ft * 12) in text
    assert f"{basis.riser_count} R @" in text and f"{basis.tread_count} T @" in text
    assert "3 1/2\" CLEAR" in text or "42\"" in text or "3'-6\"" in text
    assert f"{takeoff['geometry']['upper_area_sqft']:.1f}" in text


def test_every_pier_is_drawn_once_at_the_model_location(built):
    ds, sheets, basis, _t = built
    s1 = _sheet(sheets, "S-1")
    circles = [it for it in s1.views[0].items if getattr(it, "layer", None) == L_FOUND and it.__class__.__name__ == "Circle" and it.radius == 6.0]
    centres = sorted((round(c.center[0], 3), round(c.center[1], 3)) for c in circles)
    expected = sorted((round(x * 12, 3), round(-y * 12, 3)) for _n, x, y in basis.piers)
    assert centres == expected and len(centres) == 15


def test_joist_schedule_and_drawn_joists_are_the_takeoffs(built):
    ds, sheets, basis, takeoff = built
    s2 = _sheet(sheets, "S-2")
    table = next(it for it in s2.items if isinstance(it, Table) and it.title.startswith("UPPER JOIST"))
    joists = next(r for r in next(l for l in takeoff["lines"] if l["key"] == "structure.schedule")["cuts"] if r["family"] == "joist")["cuts"]
    assert [row[2] for row in table.rows] == [ft_in(c["length_ft"] * 12) for c in joists]
    # Drawn joist length = pool wall to the front edge at each station.
    drawn = [it for it in s2.views[0].items if isinstance(it, Poly) and it.layer == "S-FRAM" and it.fill == "#f4e9d8"]
    lengths = sorted(round(max(p[1] for p in d.points) - min(p[1] for p in d.points), 3) for d in drawn)
    assert sorted(round(c["length_ft"] * 12, 3) for c in joists) == pytest.approx(lengths[:len(joists)], abs=0.01) or all(
        any(abs(l - c["length_ft"] * 12) < 0.01 for l in lengths) for c in joists
    )


def test_board_courses_and_curved_cuts_match_the_takeoff(built):
    ds, sheets, basis, takeoff = built
    a2 = _sheet(sheets, "A-2")
    table = next(it for it in a2.items if isinstance(it, Table))
    cuts = next(l for l in takeoff["lines"] if l["key"] == "decking.upper")["cuts"]
    by_row = {r[0]: r for r in table.rows}
    for c in cuts:
        assert by_row[c["row"]][4] == c["length"]
    # The drawn long edge of each band B piece, plus overhang, is the takeoff's cut length.
    deck = CurvedDeck(basis.pool_radius_ft, basis.upper_width_ft, basis.upper_clear_depth_ft)
    layout = upper_courses(deck, TEST_PRODUCT["decking"]["actual_width_in"], TEST_PRODUCT["decking"]["gap_in"])
    oh = TEST_PRODUCT["decking"]["end_overhang_in"]
    boards = [it for it in a2.views[0].items if isinstance(it, Poly) and it.layer == L_DECK and it.fill]
    cut_len = {c["row"]: c["length_ft"] * 12 for c in cuts}
    checked = 0
    for course in layout.courses:
        if course.band != "B":
            continue
        y = -course.y_outer_ft * 12
        pieces = [b for b in boards if abs(b.points[0][1] - y) < 1e-6 and len(b.points) > 4]
        assert len(pieces) == 2
        for piece in pieces:
            long_edge = abs(piece.points[0][0] - piece.points[1][0])
            assert long_edge == pytest.approx(cut_len[f"B{course.index}"], abs=1 / 16)
            assert abs(piece.points[1][0]) == pytest.approx(pool_wall_x(basis.pool_radius_ft, course.y_outer_ft) * 12, abs=1e-6)
            checked += 1
    assert checked == 2 * layout.curve_rows


def test_stair_and_height_stack_come_from_the_model(built):
    ds, sheets, basis, takeoff = built
    st = ds.stack
    assert st.upper_walk == pytest.approx(st.lower_walk + basis.rise_in)
    assert st.rise / basis.riser_count == pytest.approx(takeoff["geometry"]["riser_height_in"], abs=0.01)
    # The stringer follows the model's rise and run.
    poly = ds.stringer_polygon(basis.front_y_ft * 12)
    seats = [p for p in poly if any(abs(p[0] - (basis.front_y_ft * 12 + k * basis.tread_depth_in)) < 1e-6 for k in range(1, basis.tread_count + 1))]
    assert len(seats) >= basis.tread_count


def test_nothing_is_invented_when_product_facts_are_missing():
    ds, sheets, basis, takeoff = _build(facts={})
    a2 = _sheet(sheets, "A-2")
    texts = [it.text for it in a2.views[0].items if hasattr(it, "text") and isinstance(getattr(it, "text"), str)]
    assert any("WAIT FOR THE BOARD WIDTH" in t for t in texts)
    assert not [it for it in a2.views[0].items if isinstance(it, Poly) and it.layer == L_DECK and it.fill == "#d9c29c" and len(it.points) > 4]
    a4 = _sheet(sheets, "A-4")
    notes = [n for n in a4.items if hasattr(n, "items") and getattr(n, "title", "").startswith("ELEVATION")][0]
    assert any("waits for the railing product" in i for i in notes.items)


def test_open_engineering_items_are_on_the_drawings(pdf_bytes):
    text = "\n".join(p.extract_text() or "" for p in PdfReader(io.BytesIO(pdf_bytes)).pages)
    for phrase in ("Helical pier shaft", "Structural member adequacy", "Guard post attachment", "pool-enclosure", "Manufacturer installation rules"):
        assert phrase in text
    assert "SEAL" not in text.upper().replace("NOT SEALED", "")


def test_dxf_is_real_cad_geometry(dxf_doc, built):
    doc, auditor, data = dxf_doc
    assert not auditor.has_errors
    assert doc.header["$INSUNITS"] == 1
    msp = doc.modelspace()
    kinds = {e.dxftype() for e in msp}
    assert {"LWPOLYLINE", "DIMENSION", "ARC", "HATCH", "TEXT"} <= kinds
    assert "IMAGE" not in kinds
    layers = {e.dxf.layer for e in msp}
    assert {"S-FRAM", "S-BEAM", "S-FNDN", "A-DECK", "A-GUARD", "A-ANNO-DIMS"} <= layers
    measures = [round(d.get_measurement(), 3) for d in msp.query("DIMENSION")]
    basis = built[2]
    assert round(basis.upper_width_ft * 12, 3) in measures  # 216 in
    assert round(basis.stair_width_ft * 12, 3) in measures
    # Pool wall arcs are the model's radius.
    radii = {round(a.dxf.radius, 3) for a in msp.query("ARC")}
    assert round(basis.pool_radius_ft * 12, 3) in radii


def test_the_set_is_deterministic(built):
    _ds, sheets, _b, _t = built
    a = render_pdf(sheets, title="x")
    b = render_pdf(sheets, title="x")
    assert a == b
    assert render_dxf(sheets, title="x") == render_dxf(sheets, title="x")


def test_treads_project_the_nosing_past_the_riser_and_show_the_back_gap(built):
    """Joel, 14 Oct 2026: treads extend past the riser by the nosing; the boards the takeoff
    counts are laid from the nose back, and what they do not cover is the gap at the riser above."""
    ds, sheets, basis, takeoff = built
    nose = TEST_PRODUCT["decking"]["tread_nosing_overhang_in"]
    w, gap = TEST_PRODUCT["decking"]["actual_width_in"], TEST_PRODUCT["decking"]["gap_in"]
    row = next(l for l in takeoff["lines"] if l["key"] == "decking.treads")["cuts"][0]
    run = basis.tread_depth_in
    for j in range(1, basis.tread_count + 1):
        t = ds.tread_layout(j)
        assert t["front"] - t["front_face"] == pytest.approx(nose)  # nose past the riser board face
        assert t["front_face"] - t["back_face"] == pytest.approx(run)  # riser face to riser face = run
        assert len(t["boards"]) == row["boards"]  # the takeoff's boards, nothing added
        coverage = row["boards"] * w + (row["boards"] - 1) * gap if not row.get("ripped_last_board_in") else run + nose
        assert t["back_gap"] == pytest.approx(run + nose - coverage, abs=1e-6)
        assert t["back_gap"] >= 0
        rx, _rz, rw, _rh = t["riser"]
        assert rx + rw == pytest.approx(t["front_face"])  # riser board on the stringer cut, under the nose
    # The same boards are what A-3 (section and detail) and A-4 (Section A) draw.
    first = ds.tread_layout(1)
    for number, view_ids in (("A-3", ("a3-section", "a3-detail")), ("A-4", None)):
        sheet = _sheet(sheets, number)
        views = [v for v in sheet.views if view_ids is None or v.ident in view_ids]
        found = [v for v in views if any(isinstance(it, Poly) and it.layer == "A-STAIR" and abs(it.points[0][0] - first["boards"][0][0]) < 1e-6 for it in v.items)]
        assert found, number
    text = "\n".join(p.extract_text() or "" for p in PdfReader(io.BytesIO(render_pdf([_sheet(sheets, "A-3")], title="t"))).pages)
    assert "NOSING" in text and "GAP" in text and "Back gap at riser above" in text


# --- The accepted drawing standard -------------------------------------------
# tests/fixtures/drawings/ holds the accepted record: the standard (layouts, title block,
# line weights, layers, dimension style, export rules, templates), the content signature
# of the accepted synthetic J1 set, and its sheet previews. A drawing change that is not
# a deliberate standard change fails here. To change the standard on purpose: bump
# STANDARD_VERSION, run tests/fixtures/drawings/regenerate_accepted_fixtures.py, review.

ACCEPTED = __import__("pathlib").Path(__file__).parent / "fixtures" / "drawings" / "pool-deck-synthetic-j1"


def test_the_drawing_standard_is_the_accepted_one():
    import json

    from app.services.drawings.standard import standard

    assert json.loads(json.dumps(standard(), sort_keys=True, ensure_ascii=False)) == json.loads((ACCEPTED / "standard.json").read_text())


def test_the_drawing_set_matches_the_accepted_signature(built):
    import json

    from app.services.drawings.standard import set_signature

    _ds, sheets, _b, _t = built
    current = json.loads(json.dumps(set_signature(sheets), sort_keys=True, ensure_ascii=False))
    accepted = json.loads((ACCEPTED / "signature.json").read_text())
    assert current == accepted
    for sheet in sheets:
        assert (ACCEPTED / f"{sheet.number}.png").stat().st_size > 10_000  # accepted preview kept in the repository
