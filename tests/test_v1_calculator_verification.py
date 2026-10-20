"""Independent verification of the V1 calculators (Joel, 20 Oct 2026).

"Independently verify mathematical results. Correct supported functionality that is
inaccurate or incomplete. Do not expose unsupported options as operational. Preserve
existing accepted calculation contracts and tests."

Every expected value below was worked by hand from the rule each calculator documents,
before the calculator was run; the arithmetic is in the comment beside it. Where the
documented rule itself departs from usual construction practice, the test says so in a
FLAG comment and pins the documented behaviour (it is not changed here).

Nothing in this file edits or loosens an existing calculator test or an accepted
contract. Conversions used in the hand work: 1 ft = 0.3048 m exactly, 1 in = 25.4 mm,
1 yd³ = 27 ft³ = 0.764554857984 m³, 1 ft² = 0.09290304 m².
"""

from __future__ import annotations

import json
import math
import shutil
import subprocess
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest

from app import create_app, db
from app.services import trade_area as ta
from app.services import wall_framing_purchasing as buy
from app.services.deck_takeoff import geometry as deck_geometry
from app.services.deck_takeoff import stock as deck_stock
from app.services.estimate_builder import (
    add_manual_line,
    calculate_extended_cost,
    calculate_sell_price,
    create_section,
    update_version_pricing,
)
from app.services.icf_quantity import IcfQuantityInputError, build_icf_standard_quantities
from app.services.labour_engine import (
    LabourEngineError,
    apply_explicit_adjustment,
    calculate_direct_labour_cost,
    calculate_man_hours,
    calculate_planning_man_hours,
)
from app.services.outbuilding import takeoff as outbuilding
from app.services.pricing_engine import (
    PricingEngineError,
    _allocate_line_sell_prices,
    apply_contingency,
    apply_tax_after_pre_tax,
    compute_named_method_pre_tax,
    cost_plus_markup_pre_tax,
    legacy_stack_pre_tax,
    true_gross_margin_pre_tax,
)
from app.services.purchasing_quantity import annotate_purchasing, coverage_purchasing, sheet_purchasing
from app.services.unit_conversion import convert
from app.services.wall_framing import WallFramingInputError, calculate_straight_wall

ROOT = Path(__file__).resolve().parents[1]
D = Decimal


# ---------------------------------------------------------------- fixtures

@pytest.fixture
def app():
    from app.services.material_catalogue import ensure_canonical_material_seed
    from app.services.labour_engine import ensure_org_001_direct_labour_cost_rate_standard
    from app.services.organizations import ensure_default_organization

    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
                              "SECRET_KEY": "test-secret-key"})
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        ensure_canonical_material_seed()
        ensure_org_001_direct_labour_cost_rate_standard()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()  # signed in by the conftest office-client fixture


def _estimate(number):
    from tests.test_approved_contractor_cost_snapshot import _estimate as make

    return make(number)


def _text(response):
    assert response.status_code == 200, response.status_code
    return response.get_data(as_text=True)


# ================================================================ unit conversions

def test_unit_conversions_are_the_exact_factors():
    # 1 yd³ = 0.9144³ m³ = 0.764554857984 m³ exactly.
    assert convert("1", "YD3", "M3")["quantity"] == D("0.764554857984")
    # 27 ft³ = 1 yd³; 13.5 ft³ = 0.5 yd³.
    assert convert("13.5", "cubic feet", "yd³")["quantity"] == D("0.5")
    # 1 ft³ = 0.3048³ m³ = 0.028316846592 m³.
    assert convert("1", "FT3", "M3")["quantity"] == D("0.028316846592")
    # 10 ft = 3.048 m; 3.048 m = 10 ft (round trip exact).
    assert convert("10", "FT", "M")["quantity"] == D("3.048")
    assert convert("3.048", "M", "FT")["quantity"] == D("10")
    # 1 m² = 1 / 0.09290304 ft² = 10.7639104... ft².
    assert convert("1", "M2", "FT2")["quantity"].quantize(D("0.0000001")) == D("10.7639104")
    # Edge: a pair with no governed rule returns None rather than a guess.
    assert convert("1", "M3", "YD3") is None
    assert convert("1", "FT", "FT2") is None


# ================================================================ concrete slab (preserved engine)

_SLAB_SCRIPT = """
import {calculateConcreteSlab} from %s;
const runs = JSON.parse(process.argv[1]);
const out = runs.map((run) => { try { return calculateConcreteSlab(run, {result_id: "v"}); }
                                 catch (e) { return {error: e.message}; } });
console.log(JSON.stringify(out));
"""


def _node():
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is not installed")
    return node


def _slab(runs):
    bundle = (ROOT / "app/static/js/concrete-slab-1.0.0.js").as_uri()
    script = _SLAB_SCRIPT % json.dumps(bundle)
    done = subprocess.run([_node(), "--input-type=module", "-e", script, json.dumps(runs)],
                          capture_output=True, text=True, check=True)
    return json.loads(done.stdout)


def _run(variant, system, inputs, waste):
    return {"variant": variant, "measurement_system": system,
            "inputs": [{"code": c, "value": v, "unit_code": u} for c, v, u in inputs],
            "assumptions": [{"code": "waste_percent", "value": waste, "unit_code": "percent"}]}


def _amounts(result):
    return {row["code"]: row["quantity"] for row in result["components"] + result["quantities"]}


def test_concrete_slab_office_bundle_matches_hand_worked_volumes():
    standard, edge_imp, edge_met, too_wide = _slab([
        # 20 × 10 ft × 4 in: 200 ft² × 4/12 ft = 66.667 ft³ ÷ 27 = 2.4691 yd³ → 2.469.
        # Waste 10 % = 0.24691 → 0.247. Total = 2.469 + 0.247 = 2.716.
        _run("standard", "imperial", [("length", "20", "ft"), ("width", "10", "ft"), ("slab_thickness", "4", "in")], "10"),
        # 30 × 20 ft × 4 in, edge 1 ft wide, 8 in below the slab, waste 5 %:
        # base 600 × 4/12 = 200 ft³ = 7.4074 → 7.407 yd³;
        # perimeter band = 2·w·(L+W) − 4·w² = 2·1·50 − 4 = 96 ft²; × 8/12 = 64 ft³ = 2.3704 → 2.370;
        # waste = 5 % of 264 ft³ = 13.2 ft³ = 0.4889 → 0.489; total 7.407 + 2.370 + 0.489 = 10.266.
        _run("thickened_edge", "imperial", [("length", "30", "ft"), ("width", "20", "ft"), ("slab_thickness", "4", "in"),
                                            ("edge_width", "1", "ft"), ("edge_depth_below_slab", "8", "in")], "5"),
        # 10 × 8 m × 100 mm = 8 m³; band 2·0.3·18 − 4·0.09 = 10.44 m² × 0.2 m = 2.088 m³; waste 0; total 10.088.
        _run("thickened_edge", "metric", [("length", "10", "m"), ("width", "8", "m"), ("slab_thickness", "100", "mm"),
                                          ("edge_width", "300", "mm"), ("edge_depth_below_slab", "200", "mm")], "0"),
        # Edge: 2 × 4 ft edge = 8 ft = the slab width, so the bands would overlap — refused.
        _run("thickened_edge", "imperial", [("length", "10", "ft"), ("width", "8", "ft"), ("slab_thickness", "4", "in"),
                                            ("edge_width", "4", "ft"), ("edge_depth_below_slab", "8", "in")], "0"),
    ])
    assert _amounts(standard) == {"base_slab_concrete": "2.469", "waste": "0.247", "total_concrete": "2.716"}
    assert _amounts(edge_imp) == {"base_slab_concrete": "7.407", "thickened_edge_concrete": "2.37",
                                  "waste": "0.489", "total_concrete": "10.266"}
    assert edge_imp["quantities"][0]["unit_code"] == "yd3"
    assert _amounts(edge_met) == {"base_slab_concrete": "8", "thickened_edge_concrete": "2.088",
                                  "waste": "0", "total_concrete": "10.088"}
    assert "overlap" in too_wide["error"]


def test_concrete_page_offers_only_the_two_engine_variants(client):
    page = _text(client.get("/calculators/concrete"))
    assert page.count("<option value=") == 4  # 2 slab types + 2 measurement systems
    assert '<option value="standard">' in page and '<option value="thickened_edge">' in page
    assert "Nothing is added to an estimate." in page


# ================================================================ stairs (preserved engine)

_STAIR_SCRIPT = """
import {selectRecommendedStair} from %s;
import {readFileSync} from "node:fs";
const profile = JSON.parse(readFileSync(%s, "utf8"));
const runs = JSON.parse(process.argv[1]);
console.log(JSON.stringify(runs.map((input) => selectRecommendedStair(input, profile))));
"""


def _stairs(inputs):
    base = ROOT / "calculation-engines/stair-ontario-residential-v1/website-source/lib/useful-tools"
    script = _STAIR_SCRIPT % (json.dumps((base / "stairs.mjs").as_uri()),
                              json.dumps(str(base / "profiles/ontario-residential-v1.json")))
    done = subprocess.run([_node(), "--input-type=module", "-e", script, json.dumps(inputs)],
                          capture_output=True, text=True, check=True)
    return json.loads(done.stdout)


def test_ontario_stair_recommendations_match_hand_worked_layouts():
    metric, imperial, impossible = _stairs([
        {"totalRise": {"value": 2600, "unit": "mm"}, "availableRun": {"value": 3300, "unit": "mm"}},
        {"totalRise": {"value": 108, "unit": "in"}, "availableRun": {"value": 140, "unit": "in"}},
        {"totalRise": {"value": 2600, "unit": "mm"}, "availableRun": {"value": 1000, "unit": "mm"}},
    ])
    # Profile: rise 125–200 mm, run 255–355 mm. Treads = risers − 1; run = available run ÷ treads.
    # 2600 mm rise: 12 risers → 216.7 mm (too high); 13 → 200.0 mm (at the limit, passes) with
    # 3300 ÷ 12 = 275 mm run (passes); 14 → 185.7 mm but 3300 ÷ 13 = 253.8 mm run (< 255, fails).
    # So 13 risers / 12 treads is the only all-pass layout. Edge: the riser sits exactly on 200 mm.
    assert (metric["riserCount"], metric["treadCount"]) == (13, 12)
    assert metric["riserHeightM"] * 1000 == pytest.approx(200.0)
    assert metric["treadRunM"] * 1000 == pytest.approx(275.0)
    assert metric["overallStatus"] == "pass"
    # Stringer = √(2.6² + 3.3²) = 4.2012 m.
    assert metric["stringerLengthM"] == pytest.approx(math.hypot(2.6, 3.3))
    # FLAG (preserved engine, not changed): the reported angle is atan(total rise ÷ total run)
    # = atan(2600/3300) = 38.2°. The pitch a carpenter lays out is atan(riser ÷ tread)
    # = atan(200/275) = 36.0°, because the run spans one fewer tread than there are risers.
    assert metric["angleDegrees"] == pytest.approx(math.degrees(math.atan2(2600, 3300)))
    assert metric["angleDegrees"] - math.degrees(math.atan2(200, 275)) == pytest.approx(2.2, abs=0.1)

    # 108 in rise, 140 in run: 14 risers → 7.714 in = 195.9 mm, 140 ÷ 13 = 10.769 in = 273.5 mm (pass);
    # 15 risers → run 140 ÷ 14 = 10 in = 254 mm (fails 255); 13 risers → 8.31 in = 211 mm (fails 200).
    assert (imperial["riserCount"], imperial["treadCount"]) == (14, 13)
    assert imperial["riserHeightM"] / 0.0254 == pytest.approx(108 / 14)
    assert imperial["treadRunM"] / 0.0254 == pytest.approx(140 / 13)
    assert imperial["overallStatus"] == "pass"

    # Edge: 2600 mm of rise in 1000 mm of run cannot meet the profile; the best candidate is still
    # shown, marked FAIL, never as a compliant stair.
    assert impossible["overallStatus"] == "fail"
    assert any(check["status"] == "fail" for check in impossible["checks"])


# ================================================================ ICF walls (8-inch only)

def _icf(manufacturer, area, c90, c45):
    return build_icf_standard_quantities(manufacturer_id=manufacturer, net_wall_area_ft2=area,
                                         corner_90_count=c90, corner_45_count=c45, result_id="verify")


def _icf_q(result):
    return {q["code"]: q["quantity"] for q in result["payload"]["quantities"]}


def test_icf_per_form_profile_matches_hand_count():
    # Fox Blocks: standard 5.33 ft², 0.132 yd³; 90° corner 7.56 ft², 0.145 yd³.
    # 1000 ft² with 4 × 90°: corners cover 4 × 7.56 = 30.24 ft²; standard = 969.76 ÷ 5.33 = 181.943715 forms;
    # concrete = 181.943715 × 0.132 + 4 × 0.145 = 24.016570 + 0.58 = 24.59657 yd³.
    assert _icf_q(_icf("fox_blocks", "1000", 4, 0)) == {
        "corner_90_8_forms": "4.0", "standard_forms": "181.943715", "concrete": "24.59657"}
    # Nudura: 12 ft² and 0.306 yd³ per form. 1000 ÷ 12 = 83.333333; × 0.306 = 25.5 yd³.
    assert _icf_q(_icf("nudura", "1000", 0, 0)) == {"standard_forms": "83.333333", "concrete": "25.5"}


def test_icf_cavity_width_profile_matches_hand_count():
    # Logix: concrete = net area × 0.667 ft cavity ÷ 27 = 1000 × 0.667 ÷ 27 = 24.703704 yd³ (corners included).
    # Forms: corners 4 × 5.36 + 2 × 3.89 = 29.22 ft²; (1000 − 29.22) ÷ 5.33 = 182.135084.
    assert _icf_q(_icf("logix", "1000", 4, 2)) == {
        "corner_90_8_forms": "4.0", "corner_45_8_forms": "2.0",
        "standard_forms": "182.135084", "concrete": "24.703704"}


def test_icf_edge_corners_larger_than_the_wall_are_refused():
    # 2 Nudura 90° corners cover 12 ft², more than a 10 ft² wall.
    with pytest.raises(IcfQuantityInputError, match="larger than the net wall area"):
        _icf("nudura", "10", 2, 0)


def test_icf_missing_corner_fact_withholds_quantities_defect_recorded():
    """DEFECT RECORDED FOR JOEL (not fixed: icf_quantity.py is SHA-pinned in
    tests/test_icf_wall_calculator_access.py::test_existing_icf_engine_and_wall_form_page_are_unchanged).

    BuildBlock has a verified per-form volume (0.131687 yd³) but no 45° corner. Requesting a
    45° corner correctly withholds standard forms and concrete, but the page also lists
    "Neither a per-form volume nor a cavity-width factor is in the profile", which is untrue for
    this profile: concrete is missing only because the standard form count waits on the corner.
    """
    result = _icf("styrorail_buildblock", "1000", 4, 1)
    fields = {item["field"]: item for item in result["inputs_required"]}
    assert "corner_45_8.wall_coverage_ft2" in fields
    assert set(_icf_q(result)) == {"corner_90_8_forms"}  # no standard forms, no concrete invented
    # Pins today's misleading wording so a later approved fix shows up here.
    assert fields["standard_8.concrete_volume_yd3"]["reason"].startswith("Neither a per-form volume")


def test_icf_page_shows_the_service_numbers_and_only_the_8_inch_core(client):
    page = _text(client.post("/calculators/wall-form", data={"manufacturer_id": "fox_blocks", "net_wall_area": "1000",
                                                              "corner_90": "4", "corner_45": "0"}))
    assert "181.943715" in page and "24.59657" in page
    assert "Core size: 8 inches." in page
    for other in ("6-inch", "10-inch", "12-inch", "core_size"):
        assert other not in page  # no other core is offered as working


# ================================================================ footings

def test_rectangular_footings_imperial_and_estimate_payload_agree():
    r = ta.footing(unit_system="imperial", waste_percent="5", footings=[
        {"length": "40", "width": "2", "thickness": "10", "count": "2"},
        {"length": "3", "width": "3", "thickness": "12", "count": "4"}])
    # 40 × 2 × 10/12 = 66.667 ft³ × 2 = 133.333; 3 × 3 × 1 = 9 × 4 = 36; total 169.333 ft³.
    # ÷ 27 = 6.2716 → 6.272 yd³; × 0.028316846592 = 4.795 m³.
    # +5 % = 177.8 ft³ ÷ 27 = 6.5852 → 6.585 yd³; 5.0347 → 5.035 m³.
    assert (r["ft3"], r["yd3"], r["m3"], r["order_yd3"], r["order_m3"]) == ("169.33", "6.272", "4.795", "6.585", "5.035")
    payload = ta.footing_contract_v1(r, "verify")
    parts = {c["code"]: c["quantity"] for c in payload["components"]}
    # Net 6.272 + waste 0.313 = the 6.585 yd³ the page shows; the review adds no further waste.
    assert parts == {"concrete_net": "6.272", "concrete_waste": "0.313"}
    assert payload["quantities"] == [{"code": "concrete", "quantity": "6.585", "unit_code": "yd3"}]


def test_rectangular_footing_metric_edge_is_exact():
    # 10 m × 0.6 m × 300 mm = 1.8 m³ exactly; +10 % = 1.98 m³.
    r = ta.footing(unit_system="metric", footings=[{"length": "10", "width": "0.6", "thickness": "300"}], waste_percent="10")
    assert (r["m3"], r["order_m3"]) == ("1.800", "1.980")
    payload = ta.footing_contract_v1(r, "verify")
    assert payload["quantities"] == [{"code": "concrete", "quantity": "1.98", "unit_code": "m3"}]


def test_footing_estimate_hand_off_carries_the_page_number(app, client):
    from app.models.calculation_estimate_mapping import CalculationResultIntake

    estimate = _estimate("EST-VERIFY-FTG")
    version = estimate.current_version
    url = f"/estimates/{estimate.id}/versions/{version.id}/footing-quantities"
    form = {"unit_system": "imperial", "footing_length": ["40", "3"], "footing_width": ["2", "3"],
            "footing_thickness": ["10", "12"], "footing_count": ["2", "4"], "waste_percent": "5"}
    page = _text(client.post(url, data=dict(form, action="calculate")))
    assert "6.585 yd³" in page
    assert client.post(url, data=dict(form, action="review")).status_code == 302
    frozen = CalculationResultIntake.query.one().frozen_result
    assert frozen["quantities"] == [{"code": "concrete", "quantity": "6.585", "unit_code": "yd3"}]


# ================================================================ roofing, siding, drywall, flooring

def test_roofing_two_planes_with_products():
    r = ta.roofing(unit_system="imperial", planes=[{"length": "40", "width": "15", "pitch": "4"}] * 2,
                   waste_percent="15", bundle_coverage="32.3", underlayment_coverage="400",
                   ridge_length="40", ridge_cap_coverage="33")
    # 4/12: √(1 + (4/12)²) = √(10/9) = 1.054093. Each plane 600 × 1.054093 = 632.456; two = 1264.91 ft² = 12.65 sq.
    # +15 % = 1454.648 → 1454.65 ft² = 14.55 sq. Bundles ⌈1454.648 ÷ 32.3⌉ = ⌈45.04⌉ = 46.
    # Rolls ⌈1454.648 ÷ 400⌉ = 4. Ridge cap ⌈40 ÷ 33⌉ = 2 (no waste on ridge).
    assert r["planes"][0]["slope_factor"] == "1.0541"
    assert (r["area"]["sqft"], r["squares"], r["order_area"]["sqft"], r["order_squares"]) == \
        ("1264.91", "12.65", "1454.65", "14.55")
    assert (r["bundles"], r["underlayment_rolls"], r["ridge_cap_bundles"]) == (46, 4, 2)


def test_roofing_metric_and_flat_edge():
    r = ta.roofing(unit_system="metric", planes=[{"length": "12", "width": "5", "pitch": "6"}], waste_percent="10",
                   bundle_coverage="3", ridge_length="12", ridge_cap_coverage="10")
    # 60 m² × √1.25 (1.118034) = 67.08 m²; +10 % = 73.79 m²; bundles ⌈73.79 ÷ 3⌉ = ⌈24.6⌉ = 25; ridge ⌈12 ÷ 10⌉ = 2.
    assert (r["area"]["m2"], r["order_area"]["m2"], r["bundles"], r["ridge_cap_bundles"]) == ("67.08", "73.79", 25, 2)
    # Edge: flat (0/12), no waste, coverage dividing exactly: 10 × 10 = 100 ft² ÷ 25 = exactly 4 bundles, not 5.
    flat = ta.roofing(unit_system="imperial", planes=[{"length": "10", "width": "10", "pitch": "0"}],
                      waste_percent="0", bundle_coverage="25")
    assert (flat["area"]["sqft"], flat["bundles"]) == ("100.00", 4)
    with pytest.raises(ta.TradeAreaInputError, match="ridge and hip length"):
        ta.roofing(unit_system="imperial", planes=[{"length": "10", "width": "10", "pitch": "4"}],
                   waste_percent="0", ridge_cap_coverage="20")


def test_siding_walls_gables_less_openings():
    r = ta.siding(unit_system="imperial", walls=[{"length": "40", "height": "10"}] * 2 + [{"length": "30", "height": "10"}] * 2,
                  gables=[{"base": "30", "height": "7.5"}] * 2,
                  openings=[{"width": "3", "height": "4", "count": "3"}, {"width": "16", "height": "7"}],
                  waste_percent="10", piece_coverage="200")
    # Walls 2·400 + 2·300 = 1400; gables 2 × (30 × 7.5 ÷ 2 = 112.5) = 225; gross 1625.
    # Openings 3 × 12 + 112 = 148; net 1477 = 14.77 sq; +10 % = 1624.7; ⌈1624.7 ÷ 200⌉ = 9 boxes.
    assert (r["gross_area"]["sqft"], r["opening_area"]["sqft"], r["net_area"]["sqft"],
            r["order_area"]["sqft"], r["squares"], r["pieces"]) == ("1625.00", "148.00", "1477.00", "1624.70", "14.77", 9)
    # Edge: openings as large as the wall are refused.
    with pytest.raises(ta.TradeAreaInputError, match="openings are larger"):
        ta.siding(unit_system="imperial", walls=[{"length": "10", "height": "8"}], gables=[],
                  openings=[{"width": "10", "height": "8"}], waste_percent="0")


def test_drywall_room_and_exact_sheet_edge():
    r = ta.drywall(unit_system="imperial", walls=[{"length": "12", "height": "8"}] * 2 + [{"length": "14", "height": "8"}] * 2,
                   ceilings=[{"length": "12", "width": "14"}],
                   openings=[{"width": "2.5", "height": "6.75"}, {"width": "4", "height": "3"}],
                   waste_percent="10", sheet_size="4x12")
    # Walls 2·96 + 2·112 = 416; ceiling 168; gross 584; openings 16.875 + 12 = 28.875; net 555.125;
    # +10 % = 610.6375; 4×12 sheet = 48 ft² → ⌈12.72⌉ = 13 sheets.
    assert (r["net_area"]["sqft"], r["order_area"]["sqft"], r["sheets"]) == ("555.13", "610.64", 13)
    # Edge: 8 × 8 ft wall, no waste = 64 ft² = exactly two 4×8 sheets.
    assert ta.drywall(unit_system="imperial", walls=[{"length": "8", "height": "8"}], ceilings=[], openings=[],
                      waste_percent="0", sheet_size="4x8")["sheets"] == 2
    # A sheet size the page does not offer is refused, not guessed.
    with pytest.raises(ta.TradeAreaInputError, match="sheet size"):
        ta.drywall(unit_system="imperial", walls=[{"length": "8", "height": "8"}], ceilings=[], openings=[],
                   waste_percent="0", sheet_size="54x12")


def test_flooring_rooms_perimeter_and_metric():
    r = ta.flooring(unit_system="imperial", rooms=[{"length": "12", "width": "14"}, {"length": "3", "width": "5"}],
                    waste_percent="7", box_coverage="20")
    # 168 + 15 = 183 ft²; perimeter 2·26 + 2·8 = 68 ft; +7 % = 195.81; ⌈195.81 ÷ 20⌉ = 10 boxes.
    assert (r["area"]["sqft"], r["perimeter"]["ft"], r["order_area"]["sqft"], r["boxes"]) == ("183.00", "68.00", "195.81", 10)
    m = ta.flooring(unit_system="metric", rooms=[{"length": "4", "width": "5"}], waste_percent="0")
    # 20 m² = 20 ÷ 0.09290304 = 215.28 ft²; perimeter 18 m = 59.06 ft; no coverage → no box count.
    assert (m["area"]["sqft"], m["perimeter"]["ft"], m["boxes"]) == ("215.28", "59.06", None)


def test_trade_pages_show_the_service_numbers(client):
    roof = _text(client.post("/calculators/roofing", data={
        "unit_system": "imperial", "plane_length": ["40", "40"], "plane_width": ["15", "15"], "plane_pitch": ["4", "4"],
        "waste_percent": "15", "bundle_coverage": "32.3", "underlayment_coverage": "400",
        "ridge_length": "40", "ridge_cap_coverage": "33"}))
    assert "1264.91" in roof and "1454.65" in roof and "46 shingle bundles" in roof and "2 ridge cap bundles" in roof
    wall = _text(client.post("/calculators/drywall", data={
        "unit_system": "imperial", "wall_length": ["12", "12", "14", "14"], "wall_height": ["8"] * 4,
        "ceiling_length": ["12"], "ceiling_width": ["14"], "opening_width": ["2.5", "4"], "opening_height": ["6.75", "3"],
        "waste_percent": "10", "sheet_size": "4x12"}))
    assert "555.13" in wall and "13 sheets" in wall
    sheet_choices = _text(client.get("/calculators/drywall"))
    assert '"4x8"' in sheet_choices and '"4x10"' in sheet_choices and '"4x12"' in sheet_choices
    floor = _text(client.post("/calculators/flooring", data={
        "unit_system": "imperial", "room_length": ["12", "3"], "room_width": ["14", "5"],
        "waste_percent": "7", "box_coverage": "20"}))
    assert "183.00" in floor and "10 boxes" in floor and "68.00 ft" in floor
    siding = _text(client.post("/calculators/siding", data={
        "unit_system": "imperial", "wall_length": ["40", "40", "30", "30"], "wall_height": ["10"] * 4,
        "gable_base": ["30", "30"], "gable_height": ["7.5", "7.5"], "opening_width": ["3", "16"],
        "opening_height": ["4", "7"], "opening_count": ["3", ""], "waste_percent": "10", "piece_coverage": "200"}))
    assert "1477.00" in siding and "9 pieces or boxes" in siding


# ================================================================ wall framing

def test_wall_framing_short_final_bay_and_exact_bay_edge():
    # 10 ft = 120 in at 16 in: studs at 0,16,…,112 (8) + 120 = 9; last bay 8 in (short).
    # Studs 9 × 8 = 72 lf; plates 2 × 10 + 1 × 10 = 30; total 102 lf.
    ten = calculate_straight_wall(length_ft="10", height_ft="8", spacing_in="16", stud_size="2x4",
                                  top_plate_count="2", bottom_plate_count="1")
    assert (ten["stud_count"], ten["short_final_spacing_in"], ten["total_lineal_ft"]) == (9, D("8"), D("102"))
    # Edge: 12 ft = 144 in = 9 × 16 exactly → studs 0…128 (9) + 144 = 10; last bay is a full 16 in, not short.
    twelve = calculate_straight_wall(length_ft="12", height_ft="8", spacing_in="16", stud_size="2x4",
                                     top_plate_count="2", bottom_plate_count="1")
    assert (twelve["stud_count"], twelve["short_final_spacing_in"]) == (10, None)
    with pytest.raises(WallFramingInputError):
        calculate_straight_wall(length_ft="12", height_ft="8", spacing_in="0", stud_size="2x4",
                                top_plate_count="2", bottom_plate_count="1")


_FRAMED = dict(length_ft="12", height_ft="8", spacing_in="16", stud_size="2x4", top_plate_count="2",
               bottom_plate_count="1",
               openings=[{"opening_type": "window", "width_in": "36", "height_ft": "4", "position_in": "30", "sill_ft": "3"}],
               corners=[{"end": "left", "count": "2", "stud_size": "2x4", "length_ft": "8"}],
               extra_members=[{"kind": "king", "count": "2", "length_ft": "8"},
                              {"kind": "header", "count": "1", "length_ft": "3.5"}])


def test_wall_framing_with_an_opening_and_purchase():
    w = calculate_straight_wall(**_FRAMED)
    # Window 30–66 in removes the layout studs strictly inside: 32, 48, 64 → 10 − 3 = 7 full-height studs.
    # Lineal: 7 × 8 = 56 + plates 24 + 12 + corners 2 × 8 = 16 + kings 16 + header 3.5 = 127.5 lf.
    assert w["intersecting_positions_in"] == (D("32"), D("48"), D("64"))
    assert (w["remaining_stud_count"], w["total_lineal_ft"]) == (7, D("127.5"))
    b = buy.purchase(w, waste_percent="10", plate_stock_length_ft="12")
    # Studs (7 + 2 corner) × 1.10 = 9.9 → 10. Plates 36 lf × 1.10 = 39.6 ÷ 12 = 3.3 → 4 pieces.
    # FLAG (documented rule, not changed): studs are bought at the full wall height (8 ft); in
    # practice a stud is the wall height less the plates (e.g. a 92-5/8 in precut for an 8 ft wall).
    assert (b["stud_pieces_net"], b["stud_pieces"], b["plate_order_lineal_ft"], b["plate_pieces"]) == (9, 10, D("39.6"), 4)
    q = {row["code"]: row["quantity"] for row in buy.contract_v1(w, b, "verify")["quantities"]}
    assert q == {"studs": "10", "plates": "4", "headers_3_5ft": "1", "king_studs_8ft": "2"}


def test_wall_framing_estimate_hand_off_carries_the_page_numbers(app, client):
    from app.models.calculation_estimate_mapping import CalculationResultIntake

    estimate = _estimate("EST-VERIFY-FRM")
    version = estimate.current_version
    url = f"/estimates/{estimate.id}/versions/{version.id}/framing-quantities"
    form = {"length_ft": "12", "height_ft": "8", "spacing_in": "16", "stud_size": "2x4", "top_plate_count": "2",
            "bottom_plate_count": "1", "opening_type": ["window"], "opening_width_in": ["36"], "opening_height_ft": ["4"],
            "opening_position_in": ["30"], "opening_sill_ft": ["3"], "corner_end": ["left"], "corner_count": ["2"],
            "corner_stud_size": ["2x4"], "corner_length_ft": ["8"], "member_kind": ["king", "header"],
            "member_name": ["", ""], "member_count": ["2", "1"], "member_length_ft": ["8", "3.5"],
            "waste_percent": "10", "plate_stock_length_ft": "12"}
    page = _text(client.post(url, data=dict(form, action="calculate")))
    assert "127.5 total lineal feet" in page and "7 full-height studs" in page
    assert client.post(url, data=dict(form, action="review")).status_code == 302
    frozen = CalculationResultIntake.query.one().frozen_result
    assert {q["code"]: q["quantity"] for q in frozen["quantities"]} == {
        "studs": "10", "plates": "4", "headers_3_5ft": "1", "king_studs_8ft": "2"}


# ================================================================ post-frame outbuilding takeoff

_BUILDING = dict(
    building_system="POST_FRAME_STEEL", width_ft="30", length_ft="40", wall_height_ft="12", roof_type="GABLE",
    roof_pitch="4", eave_overhang_in="12", gable_overhang_in="12", post_spacing_ft="8", endwall_post_spacing_ft="10",
    post_description="3-ply 2x6", truss_spacing_ft="4", purlin_spacing_in="24", purlin_lumber="2x4 SPF",
    girt_spacing_in="24", girt_lumber="2x4 SPF", skirt_lumber="2x8 PT", roof_panel_coverage_in="36",
    wall_panel_coverage_in="36", screws_per_sqft="0.8", foundation="SLAB", slab_thickness_in="4",
    concrete_waste_percent="5", openings=[])


def _lines(values):
    result = outbuilding.takeoff(values)
    return result, {line["code"].split("-2X")[0]: line for line in result["lines"]}


def test_outbuilding_takeoff_matches_hand_takeoff():
    result, by = _lines(_BUILDING)
    # W 360 in, L 480 in, H 144 in, 4/12 → run 180, rise 60, slope factor √(1 + 1/9) = 1.054093.
    # Slope (with 12 in eave) = 192 × 1.054093 = 202.386 in; roof length = 480 + 2 × 12 = 504 in.
    q = {code: line["qty"] for code, line in by.items()}
    assert q["CAL-OB-POST"] == "16"           # ⌈480/96⌉ = 5 bays → 2 × 6 = 12; ⌈360/120⌉ = 3 → 2 × 2 = 4
    assert q["CAL-OB-TRUSS-30FT-4-12"] == "11"  # ⌈480/48⌉ + 1
    assert q["CAL-OB-PURLIN"] == "756.00"     # rows ⌊202.386/24⌋ + 1 = 9; 2 × 9 × 504 in = 9072 in
    assert q["CAL-OB-GIRT"] == "888.00"       # 6 rows × 1680 in + gable rows at 24 and 48 in: 2 × (216 + 72)
    assert q["CAL-OB-SKIRT"] == "140.00"      # 1680 in perimeter
    assert q["CAL-OB-ROOF-PANEL"] == "473.67"  # ⌈504/36⌉ = 14 per side, ⌈202.386⌉ = 203 in: 2 × 14 × 203 = 5684 in
    assert by["CAL-OB-ROOF-PANEL"]["cut_list"] == [("16'-11\"", 28)]
    assert q["CAL-OB-RIDGE-CAP"] == "42.00"
    # Wall panels: sidewalls 2 × ⌈480/36⌉ = 28 × 144 in; each endwall 10 panels at 144 in + the gable
    # rise at the panel's high edge (12, 24, 36, 48, 60, 60, 48, 36, 24, 12) = 1800 in; total 7632 in.
    assert q["CAL-OB-WALL-PANEL"] == "636.00"
    assert q["CAL-OB-TRIM-EAVE"] == "84.00" and q["CAL-OB-TRIM-RAKE"] == "67.47"  # 4 × 202.386 = 809.54 in
    assert q["CAL-OB-TRIM-CORNER"] == "48.00" and q["CAL-OB-TRIM-BASE"] == "140.00"
    # Roof 2 × 504 × 202.386 ÷ 144 = 1416.70 ft²; walls 2·480·144 + 2·(360·144 + 360·60/2) = 263520 in² = 1830.0 ft².
    assert result["areas"] == {"roof_sqft": "1416.7", "wall_cladding_sqft": "1830.0", "floor_sqft": "1200.0"}
    assert q["CAL-OB-CLADDING-SCREW"] == "2598"  # ⌈3246.70 × 0.8⌉ = ⌈2597.36⌉
    # Slab 360 × 480 × 4 ÷ 1728 = 400 ft³ × 0.028316846592 = 11.3267 m³ × 1.05 = 11.893 → up to 11.90 m³.
    assert q["CAL-CONC"] == "11.90" and by["CAL-CONC"]["status"] == "REVIEW"
    assert by["CAL-OB-POST"]["status"] == "REVIEW" and by["CAL-OB-FRAME-CONNECTORS"]["qty"] is None


def test_outbuilding_overhead_door_takes_off_what_it_blocks():
    door = [{"kind": "OVERHEAD_DOOR", "wall": "FRONT", "width_in": "120", "height_in": "120", "offset_ft": "10"}]
    result, by = _lines(dict(_BUILDING, openings=door))
    q = {code: line["qty"] for code, line in by.items()}
    # 10 × 10 ft door at 120–240 in on the front: panels 144–180 and 180–216 lie wholly over it and
    # drop to 144 − 120 = 24 in → 7632 − 2 × 120 = 7392 in = 616.00 lf.
    assert q["CAL-OB-WALL-PANEL"] == "616.00"
    assert ("2'-0\"", 2) in by["CAL-OB-WALL-PANEL"]["cut_list"]
    assert q["CAL-OB-GIRT"] == "848.00"   # girt rows at 24, 48, 72, 96 in are cut by 120 in: 10656 − 480 = 10176 in
    assert q["CAL-OB-SKIRT"] == "130.00" and q["CAL-OB-TRIM-BASE"] == "130.00"  # 1680 − 120 in
    assert q["CAL-OB-TRIM-OPENING"] == "30.00"  # 2 jambs + head = 360 in
    assert result["areas"]["wall_cladding_sqft"] == "1730.0"  # 1830 − 100
    assert q["CAL-OB-CLADDING-SCREW"] == "2518"  # ⌈(1416.70 + 1730.0) × 0.8⌉ = ⌈2517.36⌉
    assert by["CAL-OB-DOOR-FRAMING"]["qty"] is None and by["CAL-OB-DOOR-FRAMING"]["status"] == "REVIEW"


def test_outbuilding_edge_missing_answers_are_not_invented():
    _result, by = _lines(dict(_BUILDING, truss_spacing_ft=None, screws_per_sqft=None, foundation="TO_CONFIRM"))
    for code in ("CAL-OB-TRUSS", "CAL-OB-CLADDING-SCREW", "CAL-CONC"):
        assert by[code]["qty"] is None and by[code]["status"] == "NEEDS_ANSWER"
    from app.services.outbuilding import spec

    # Only the validated system and roof are offered; the others are listed as not yet available.
    assert list(spec.BUILDING_SYSTEMS) == ["POST_FRAME_STEEL"] and list(spec.ROOF_TYPES) == ["GABLE"]
    values, errors = spec.read_answers({"building_system": "STEEL_FRAME", "roof_type": "HIP"})
    assert values["building_system"] is None and values["roof_type"] is None and len(errors) == 2


# ================================================================ deck takeoff

def test_curved_pool_deck_geometry_matches_hand_geometry():
    deck = deck_geometry.CurvedDeck(12.0, 16.0, 6.0)
    # Pool r = 12 ft, deck 16 ft wide, 6 ft clear: sides meet the wall at y = √(144 − 64) = 8.94427;
    # front at 18 → sides 9.05573 ft. Half angle asin(8/12) = 0.729728 rad; bite = r²θ − y·x = 105.0808 − 71.5542.
    assert deck.side_y_ft == pytest.approx(math.sqrt(80))
    assert deck.area_sqft == pytest.approx(16 * (18 - math.sqrt(80)) - (144 * math.asin(8 / 12) - math.sqrt(80) * 8))
    assert deck.area_sqft == pytest.approx(111.365, abs=0.001)
    assert deck.joist_length_ft(0.0) == pytest.approx(6.0) and deck.joist_length_ft(8.0) == pytest.approx(9.05573, abs=1e-5)
    # 4 header chords: Δ = 2θ/4; chord = 2r·sin(Δ/2) = 24 × sin(0.182432) = 4.3541 ft; sagitta r(1 − cos(Δ/2)) = 2.3896 in.
    assert deck.header_chords(4)[0] == pytest.approx(4.3541, abs=1e-4)
    assert deck.header_sagitta_in(4) == pytest.approx(2.3896, abs=1e-4)
    with pytest.raises(deck_geometry.GeometryRefusal):
        deck_geometry.CurvedDeck(8.0, 16.0, 6.0)  # edge: deck as wide as the pool cannot meet the wall


def test_deck_board_courses_and_stock_packing():
    # 66 in band, 5.5 in boards, 1/4 in gap (5.75 in pitch): ⌊66.25/5.75⌋ = 11 boards use
    # 11 × 5.5 + 10 × 0.25 = 63 in; 3 in left − 1 gap = a 2.75 in ripped board.
    assert deck_geometry.straight_band(66, 5.5, 0.25) == (11, 2.75, 0.0)
    # Edge: 63 in fills exactly with 11 boards — no ripped board.
    assert deck_geometry.straight_band(63, 5.5, 0.25) == (11, None, 0.0)
    # Ten 70 in cuts, 1/8 in kerf, stock 8/12/16 ft: two cuts need 70 + 0.125 + 70 = 140.125 in, so a
    # 12 ft (144 in) stick holds two and a 16 ft (192 in) stick still holds only two. Five 12 ft sticks
    # = 720 in bought, 20 in waste — less than ten 8 ft (960 in) or five 16 ft (960 in).
    allocation = deck_stock.allocate([(70, f"c{i}") for i in range(10)], [96, 144, 192], 0.125)
    assert allocation.count_by_stock() == {144.0: 5}
    assert (allocation.purchased_in, allocation.waste_in) == (720.0, 20.0)
    with pytest.raises(deck_stock.StockRefusal, match="splice"):
        deck_stock.allocate([(200, "long")], [96, 144, 192], 0.125)


# ================================================================ waste factors and purchasing units

def test_waste_and_purchase_units():
    # Line waste: 10 × $12.50 × 1.10 = $137.50; sell at 20 % markup = $165.00.
    assert calculate_extended_cost("10", "12.50", "10") == D("137.5")
    assert calculate_sell_price(D("137.5"), "20") == D("165")
    # Edge: 0 % waste leaves the cost unchanged.
    assert calculate_extended_cost("3", "200", "0") == D("600")
    # Sheets: 610.6375 ft² ÷ (48 × 96 / 144 = 32 ft²) = 19.08 sheets — an exact quotient, not rounded here.
    assert sheet_purchasing("610.6375", 48, 96)["purchasing_quantity"] == D("610.6375") / D("32")
    assert coverage_purchasing("100", "")["purchasing_status"] == "TBD"
    # Concrete purchased in m³: 6.585 yd³ × 0.764554857984 = 5.0346 m³.
    line = annotate_purchasing({"status": "KNOWN", "quantity": D("6.585"), "unit": "YD3",
                                "quantity_meaning": "concrete_volume"})
    assert line["purchasing_unit"] == "M3"
    assert line["purchasing_quantity"] == D("6.585") * D("0.764554857984")


# ================================================================ labour hours

def test_labour_arithmetic():
    # 240 ft² × 0.05 h/ft² = 12 h; 12 h × $65 = $780; 3 people × 8 h × 2.5 days = 60 h; +10 % with a reason = 66 h.
    assert calculate_man_hours("240", "0.05") == D("12")
    assert calculate_direct_labour_cost(D("12"), "65") == D("780")
    assert calculate_planning_man_hours(3, 8, "2.5") == D("60")
    assert apply_explicit_adjustment(D("60"), "10", "Winter conditions") == D("66")
    with pytest.raises(LabourEngineError, match="reason"):
        apply_explicit_adjustment(D("60"), "10", "")
    with pytest.raises(LabourEngineError):
        calculate_man_hours("-1", "0.05")


def test_entered_labour_hours_cost_hours_times_saved_rate(app):
    from app.models.labour_engine import DirectLabourCostRateStandard
    from app.services import estimate_labour_hours as labour
    from app.services.organizations import DEFAULT_ORGANIZATION_ID

    estimate = _estimate("EST-VERIFY-LAB")
    version = estimate.current_version
    item = add_manual_line(create_section(version, name="Work"), line_type="Custom", description="Footings",
                           quantity=3, unit="yd3", unit_cost=200)
    rate = D(str(DirectLabourCostRateStandard.query.filter_by(organization_id=DEFAULT_ORGANIZATION_ID,
                                                              approval_status="APPROVED").one().rate_per_man_hour))
    labour.save_hours(version, organization_id=DEFAULT_ORGANIZATION_ID, hours_by_item={item.id: "7.5"}, actor="Joel Brayman")
    from app.models import EstimateLineItem

    line = EstimateLineItem.query.filter_by(code=f"LAB-{item.id}").one()
    # 7.5 h × the saved company rate, to the cent; waste stays 0 on a labour line.
    assert line.extended_cost == (D("7.5") * rate).quantize(D("0.01"))
    assert D(str(line.waste_percent)) == 0


# ================================================================ assemblies and estimate totals

def test_assembly_cost_rolls_up_with_component_waste_and_markup(app):
    from app.models import Assembly, AssemblyItem, CostItem
    from app.services.estimate_builder import add_assembly_line

    plywood = CostItem(code="V-PLY", name="Plywood", category="Material", unit="each", unit_cost=D("50.00"),
                       default_markup_percent=D("0"), is_active=True)
    screws = CostItem(code="V-SCR", name="Screws", category="Material", unit="box", unit_cost=D("4.25"),
                      default_markup_percent=D("0"), is_active=True)
    db.session.add_all([plywood, screws]); db.session.flush()
    assembly = Assembly(code="V-ASM", name="Subfloor 4x8", category="Assembly", unit="each",
                        default_markup_percent=D("15"), is_active=True)
    db.session.add(assembly); db.session.flush()
    db.session.add_all([AssemblyItem(assembly_id=assembly.id, cost_item_id=plywood.id, quantity=D("2"), waste_percent=D("10")),
                        AssemblyItem(assembly_id=assembly.id, cost_item_id=screws.id, quantity=D("3"), waste_percent=D("0"))])
    db.session.commit()
    # 2 × 50 × 1.10 = 110.00 + 3 × 4.25 = 12.75 → 122.75 base; × 1.15 = 141.1625 sell per unit.
    assert assembly.base_unit_cost == D("122.75")
    assert assembly.sell_unit_price == D("141.1625")
    estimate = _estimate("EST-VERIFY-ASM")
    section = create_section(estimate.current_version, name="Floor")
    line = add_assembly_line(section, assembly_id=assembly.id, quantity=4, waste_percent=5)
    # 4 × 122.75 × 1.05 = 515.55 cost; × 1.15 markup = 592.8825 → 592.88.
    assert (line.extended_cost, line.sell_price) == (D("515.55"), D("592.88"))


def test_version_totals_stack_overhead_profit_then_tax(app):
    estimate = _estimate("EST-VERIFY-TOT")
    version = estimate.current_version
    section = create_section(version, name="Work")
    add_manual_line(section, line_type="Custom", description="A", quantity=10, unit="ea", unit_cost="12.50", waste_percent=10)
    add_manual_line(section, line_type="Custom", description="B", quantity=3, unit="ea", unit_cost=200)
    update_version_pricing(version, overhead_percent="10", profit_percent="8", tax_percent="13")
    # Subtotal 137.50 + 600 = 737.50; overhead 73.75; profit 8 % of 811.25 = 64.90; taxable 876.15;
    # HST 13 % = 113.8995 → 113.90; total 990.05.
    assert (version.subtotal, version.total) == (D("737.50"), D("990.05"))


# ================================================================ pricing and margin

def test_named_pricing_methods():
    # True gross margin: sell = cost ÷ (1 − GM) = 1000 ÷ 0.75 = 1333.33; check: (1333.33 − 1000)/1333.33 = 25.0 %.
    assert true_gross_margin_pre_tax("1000", "0.25") == D("1333.33")
    assert true_gross_margin_pre_tax("1000", "0") == D("1000.00")  # edge: no margin
    with pytest.raises(PricingEngineError):
        true_gross_margin_pre_tax("1000", "1")  # edge: 100 % margin is impossible
    # Markup: 1000 × 1.15 = 1150.00 (a 13.04 % margin, not 15 %).
    assert cost_plus_markup_pre_tax("1000", "0.15") == D("1150.00")
    # Legacy stack: 1000 + 10 % = 1100; profit 10 % of 1100 = 110; pre-tax 1210; tax 13 % = 157.30; 1367.30.
    assert legacy_stack_pre_tax("1000", "10", "10") == (D("1000.00"), D("100.00"), D("110.00"), D("1210.00"))
    assert apply_tax_after_pre_tax("1210", "13") == (D("157.30"), D("1367.30"))


def test_contingency_treatments():
    # 5 % of 1000 = 50. Included in the margin basis: (1000 + 50) ÷ 0.75 = 1400.00.
    assert compute_named_method_pre_tax(method="TRUE_GROSS_MARGIN", direct_cost="1000", target_gross_margin="0.25",
                                        contingency_visibility="CUSTOMER_PRICED",
                                        contingency_pricing_treatment="INCLUDED_IN_MARGIN_BASIS",
                                        contingency_rate="0.05") == (D("50.00"), D("1050.00"), D("1400.00"))
    # Added after base pricing: 1333.33 + 50 = 1383.33.
    assert compute_named_method_pre_tax(method="TRUE_GROSS_MARGIN", direct_cost="1000", target_gross_margin="0.25",
                                        contingency_visibility="CUSTOMER_PRICED",
                                        contingency_pricing_treatment="ADDED_AFTER_BASE_PRICING",
                                        contingency_rate="0.05")[2] == D("1383.33")
    # Internal reserve is tracked (50) and never reaches the customer price.
    assert compute_named_method_pre_tax(method="TRUE_GROSS_MARGIN", direct_cost="1000", target_gross_margin="0.25",
                                        contingency_visibility="INTERNAL_RESERVE", contingency_rate="0.05") == \
        (D("50.00"), D("1000.00"), D("1333.33"))
    assert apply_contingency("1000", "UNSPECIFIED", None, "0.05")[0] == D("0.00")
    with pytest.raises(PricingEngineError):
        compute_named_method_pre_tax(method="GUESS", direct_cost="1000")


def test_pre_tax_sell_is_spread_over_lines_without_losing_a_cent():
    items = [SimpleNamespace(extended_cost=D(v), sell_price=None) for v in ("333.33", "333.33", "333.34")]
    version = SimpleNamespace(sections=[SimpleNamespace(line_items=items, subtotal=None)])
    _allocate_line_sell_prices(version, D("1333.33"), D("1000.00"))
    # 1333.33 × 333.33/1000 = 444.4389 → 444.44 twice; the last line takes the remainder 444.45; sum 1333.33.
    assert [i.sell_price for i in items] == [D("444.44"), D("444.44"), D("444.45")]
    assert version.sections[0].subtotal == D("1333.33")
