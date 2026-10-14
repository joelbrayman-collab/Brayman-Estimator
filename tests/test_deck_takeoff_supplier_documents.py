"""Supplier request PDF on the approved Brayman page, and the response intake.

These tests reproduce requests issued on the historical eight-box form (form 1).
Those requests, their stored PDFs and their field mappings are preserved. The
current four-box form (form 2) is tested in test_deck_takeoff_supplier_form_v2.py.
"""

from __future__ import annotations

import copy
from io import BytesIO

import pytest
from pypdf import PdfReader, PdfWriter

from app.models.canonical_material import CANONICAL_MATERIAL_SEED
from app.services.brayman_supplier_estimate import (
    COMPANY,
    LEGAL,
    OFFICE,
    TITLE,
    bushel_supplier_estimate_request,
    render_supplier_estimate_request,
    render_supplier_response_request,
)
from app.services.construction_model.material_readiness import best_available_material_requirements
from app.services.deck_takeoff import calculate_pool_deck_takeoff, read_basis
from app.services.deck_takeoff.intake import (
    INCOMPLETE,
    INVALID,
    KEPT_ON_RESPONSE,
    NOT_QUOTED,
    NOT_RECORDABLE,
    PRICE_CONFLICT,
    QUOTED,
    READY_TO_RECORD,
    SUBSTITUTION_REVIEW,
    SupplierResponseError,
    answers_from_values,
    read_response_pdf,
    reconcile,
)
from app.services.brayman_supplier_estimate import grand_total_script, line_total_script, net_price_script
from app.services.deck_takeoff.supplier_request import FINAL, build_request
from tests.fixtures.construction_model.bushel_proving_fixture import proving_model
from tests.fixtures.construction_model.linda_j1_takeoff_fixture import model, with_codes
from tests.test_deck_takeoff_linda_j1 import TEST_PRODUCT

SOURCE = {"project_id": 7, "construction_model_revision_number": 3, "construction_model_sha256": "a" * 64}
DARCY_FIELDS = ("sku", "product_confirmed", "unit_price", "discount", "net_price", "availability", "lead_time", "substitution")


def _built(project_id=7, facts=None, content=None, response_form=1):
    basis, _ = read_basis(content or with_codes(model(), {"stringer": "TEST-PT-2X12-8"}), SOURCE)
    takeoff = calculate_pool_deck_takeoff(basis, facts if facts is not None else TEST_PRODUCT)
    return build_request(
        takeoff=takeoff,
        project_id=project_id,
        organization_id="ORG-001",
        project_name="Linda Bushel (synthetic copy)",
        project_address="12 D'Arcy's Way, Kemptville, ON",
        supplier_name="BMR Winchester",
        contractor_supplier_account_id=3,
        supplier_id=2,
        supplier_location_id=4,
        issued_by="Test office",
        response_form=response_form,
    )


def _pdf(built):
    return render_supplier_response_request(**built["document"])


def _fill(pdf: bytes, values: dict) -> bytes:
    writer = PdfWriter(clone_from=PdfReader(BytesIO(pdf)))
    for page in writer.pages:
        writer.update_page_form_field_values(page, values, auto_regenerate=False)
    out = BytesIO()
    writer.write(out)
    return out.getvalue()


def _row(built, prefix):
    return next(r for r in built["manifest"]["lines"] if r["key"].startswith(prefix))


def test_request_pdf_keeps_the_approved_page_and_parses_strictly():
    built = _built()
    payload = _pdf(built)
    reader = PdfReader(BytesIO(payload), strict=True)
    text = " ".join(" ".join(page.extract_text() or "" for page in reader.pages).split())
    for words in (COMPANY, LEGAL, OFFICE, TITLE, "Please return this PDF to Brayman Construction", "Prices valid until"):
        assert words in text
    for internal in ("CalibraytAI", "CanonicalMaterial", "MaterialRequirement", "PRODUCT_DEPENDENT"):
        assert internal not in text
    assert b"/NeedAppearances true" in payload
    assert b"/NeedAppearances True" not in payload
    fields = reader.get_fields()
    rows = built["manifest"]["lines"]
    for row in rows:
        n = f"{row['number']:02d}"
        for name in DARCY_FIELDS:
            assert f"{name}_{n}" in fields
            assert fields[f"{name}_{n}"].get("/V") in (None, "")
        assert fields[f"line_key_{n}"]["/V"] == row["key"]
        assert fields[f"line_sig_{n}"]["/V"] == row["signature"]
        # Brayman's quantity is drawn text. It is not a field the supplier can change.
        assert f"qty_{n}" not in fields
    assert fields["request_id"]["/V"] == built["manifest"]["request_id"]
    for name in ("bmr_contact", "response_date", "valid_until", "general_notes"):
        assert name in fields


def test_quantities_units_stock_and_source_are_printed():
    built = _built()
    payload = _pdf(built)
    text = "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(payload)).pages)
    stringer = _row(built, "lumber.2x12")
    assert stringer["qty"] == "10"
    assert "8 ft stock" in text
    assert "Source: project revision 3" in text
    assert "PRODUCT FACT REQUIRED FIRST" not in stringer["item"]


def test_product_facts_are_requested_before_a_quantity_when_missing():
    built = _built(facts={"cutting": {"kerf_in": 0.125}})
    boards = _row(built, "decking.boards")
    assert boards["qty"] == "TBD"
    assert "PRODUCT FACT REQUIRED FIRST" in boards["item"]
    assert "Actual board width" in boards["item"]


def test_the_approved_legacy_page_now_parses_strictly():
    proving = proving_model()
    readiness = best_available_material_requirements(proving, tuple(CANONICAL_MATERIAL_SEED))
    payload = render_supplier_estimate_request(**bushel_supplier_estimate_request(readiness, proving))
    reader = PdfReader(BytesIO(payload), strict=True)
    assert "unit_price_01" in reader.get_fields()
    assert b"/NeedAppearances true" in payload


def test_a_filled_pdf_round_trips_and_reconciles():
    built = _built()
    rows = built["manifest"]["lines"]
    stringer = _row(built, "lumber.2x12")
    beam = _row(built, "lumber.2x10")
    bolts = _row(built, "fasteners.stitch-bolts")
    sub = _row(built, "gate")
    blank = _row(built, "piers.helical")
    s, b, t, g = (f"{r['number']:02d}" for r in (stringer, beam, bolts, sub))
    values = {
        f"sku_{s}": "BMR-212-8PT", f"product_confirmed_{s}": "Yes", f"unit_price_{s}": "$30.00", f"discount_{s}": "10%", f"net_price_{s}": "27.00", f"availability_{s}": "In stock", f"lead_time_{s}": "2 days",
        f"sku_{b}": "BMR-210-10PT", f"product_confirmed_{b}": "Yes", f"unit_price_{b}": "25.00", f"discount_{b}": "10", f"net_price_{b}": "24.00",
        f"sku_{t}": "BOLT-12", f"product_confirmed_{t}": "Yes", f"unit_price_{t}": "2.00", f"discount_{t}": "10",
        f"sku_{g}": "GATE-X", f"product_confirmed_{g}": "Substitute", f"unit_price_{g}": "300", f"discount_{g}": "0", f"net_price_{g}": "300", f"substitution_{g}": "48 in gate instead",
        "bmr_contact": "Darcy", "response_date": "2026-10-14", "valid_until": "2026-11-30", "general_notes": "Synthetic test response",
    }
    returned = _fill(_pdf(built), values)
    answers = answers_from_values(read_response_pdf(returned))
    result = reconcile(built["manifest"], answers, project_id=7, organization_id="ORG-001", catalogue_codes=frozenset({"TEST-PT-2X12-8"}))
    by = {r["key"]: r for r in result["rows"]}
    assert by[stringer["key"]]["status"] == QUOTED
    assert by[stringer["key"]]["recording"] == READY_TO_RECORD
    assert by[stringer["key"]]["net_price"] == "27.00"
    assert by[stringer["key"]]["line_value"] == "270.00"
    assert by[stringer["key"]]["availability_status"] == "IN_STOCK"
    assert by[beam["key"]]["status"] == PRICE_CONFLICT
    assert by[beam["key"]]["recording"] == NOT_RECORDABLE
    assert by[bolts["key"]]["status"] == QUOTED
    assert by[bolts["key"]]["net_price"] == "1.80"
    assert "calculated" in by[bolts["key"]]["net_source"]
    assert by[bolts["key"]]["recording"] == READY_TO_RECORD
    assert by[bolts["key"]]["canonical_identity"]["code"] == "CAL-FAST-BEAM-STITCH-BOLT"
    assert by[sub["key"]]["status"] == SUBSTITUTION_REVIEW
    assert by[blank["key"]]["status"] == NOT_QUOTED
    assert result["valid_until"] == "2026-11-30"
    assert result["contact"] == "Darcy"
    assert len(result["rows"]) == len(rows)


@pytest.mark.parametrize(
    "values, status",
    [
        ({"unit_price": "abc"}, INVALID),
        ({"discount": "140"}, INVALID),
        ({"sku": "X", "product_confirmed": "Yes", "unit_price": "10"}, INCOMPLETE),
        ({"product_confirmed": "Yes", "net_price": "10"}, INCOMPLETE),
        ({"sku": "X", "net_price": "10"}, INCOMPLETE),
        ({"sku": "X", "product_confirmed": "maybe", "net_price": "10"}, SUBSTITUTION_REVIEW),
        ({"sku": "X", "product_confirmed": "Yes", "net_price": "10", "substitution": "Brand Y 12 ft instead"}, SUBSTITUTION_REVIEW),
        ({"sku": "X", "product_confirmed": "Yes", "net_price": "NaN"}, INVALID),
        ({"sku": "X", "product_confirmed": "Yes", "net_price": "Infinity"}, INVALID),
        ({"sku": "X", "product_confirmed": "Yes", "net_price": "1E+400"}, INVALID),
        ({"sku": "X", "product_confirmed": "Yes", "unit_price": "sNaN", "net_price": "1"}, INVALID),
        ({"sku": "X", "product_confirmed": "Yes", "discount": "Infinity", "net_price": "1"}, INVALID),
        ({"sku": "X", "product_confirmed": "Yes", "unit_price": "10", "net_price": "12"}, PRICE_CONFLICT),
    ],
)
def test_bad_or_partial_answers_are_never_recordable(values, status):
    built = _built()
    row = _row(built, "lumber.2x12")
    n = row["number"]
    answers = {"request_id": built["manifest"]["request_id"], "request_project": "7", "valid_until": "2026-11-30", "lines": {n: {"line_key": row["key"], "line_sig": row["signature"], **values}}}
    result = reconcile(built["manifest"], answers, project_id=7, organization_id="ORG-001", catalogue_codes=frozenset({"TEST-PT-2X12-8"}))
    line = next(r for r in result["rows"] if r["number"] == n)
    assert line["status"] == status
    assert line["recording"] == NOT_RECORDABLE


def test_a_tampered_line_identity_is_refused():
    built = _built()
    row = _row(built, "lumber.2x12")
    answers = {"request_id": built["manifest"]["request_id"], "valid_until": "2026-11-30", "lines": {row["number"]: {"line_key": row["key"], "line_sig": "0" * 24, "sku": "X", "product_confirmed": "Yes", "net_price": "1"}}}
    result = reconcile(built["manifest"], answers, project_id=7, organization_id="ORG-001", catalogue_codes=frozenset({"TEST-PT-2X12-8"}))
    line = next(r for r in result["rows"] if r["number"] == row["number"])
    assert line["status"] == INVALID


def test_a_price_without_validity_is_not_recorded():
    built = _built()
    row = _row(built, "lumber.2x12")
    answers = {"request_id": built["manifest"]["request_id"], "lines": {row["number"]: {"line_key": row["key"], "line_sig": row["signature"], "sku": "X", "product_confirmed": "Yes", "net_price": "1"}}}
    result = reconcile(built["manifest"], answers, project_id=7, organization_id="ORG-001", catalogue_codes=frozenset({"TEST-PT-2X12-8"}))
    line = next(r for r in result["rows"] if r["number"] == row["number"])
    assert line["status"] == QUOTED and line["recording"] == NOT_RECORDABLE
    assert any("valid" in issue for issue in result["issues"])


def test_another_projects_response_is_refused():
    built = _built(project_id=7)
    other = _built(project_id=8)
    answers = answers_from_values(read_response_pdf(_pdf(other)))
    with pytest.raises(SupplierResponseError):
        reconcile(built["manifest"], answers, project_id=7, organization_id="ORG-001")
    with pytest.raises(SupplierResponseError):
        reconcile(other["manifest"], answers, project_id=7, organization_id="ORG-001")
    with pytest.raises(SupplierResponseError):
        reconcile(other["manifest"], answers, project_id=8, organization_id="ORG-002")


def test_a_pdf_that_is_not_a_response_is_refused():
    with pytest.raises(SupplierResponseError):
        read_response_pdf(b"not a pdf")
    proving = proving_model()
    readiness = best_available_material_requirements(proving, tuple(CANONICAL_MATERIAL_SEED))
    legacy = render_supplier_estimate_request(**bushel_supplier_estimate_request(readiness, proving))
    with pytest.raises(SupplierResponseError):
        read_response_pdf(legacy)


def test_a_returned_line_without_its_identity_is_not_matched():
    built = _built()
    row = _row(built, "lumber.2x12")
    answers = {"request_id": built["manifest"]["request_id"], "valid_until": "2026-11-30", "lines": {row["number"]: {"sku": "X", "product_confirmed": "Yes", "net_price": "1"}}}
    result = reconcile(built["manifest"], answers, project_id=7, organization_id="ORG-001", catalogue_codes=frozenset({"TEST-PT-2X12-8"}))
    line = next(r for r in result["rows"] if r["number"] == row["number"])
    assert line["status"] == INVALID and line["recording"] == NOT_RECORDABLE


def test_a_blank_discount_is_reported_not_assumed():
    built = _built()
    row = _row(built, "lumber.2x12")
    answers = {"request_id": built["manifest"]["request_id"], "valid_until": "2026-11-30", "lines": {row["number"]: {"line_key": row["key"], "line_sig": row["signature"], "sku": "X", "product_confirmed": "Yes", "unit_price": "10", "net_price": "9"}}}
    result = reconcile(built["manifest"], answers, project_id=7, organization_id="ORG-001", catalogue_codes=frozenset({"TEST-PT-2X12-8"}))
    line = next(r for r in result["rows"] if r["number"] == row["number"])
    assert line["discount_percent"] is None
    assert any("implies 10.00%" in p for p in line["problems"])


def test_a_line_without_a_product_type_has_no_identity_and_keeps_its_price():
    facts = copy.deepcopy(TEST_PRODUCT)
    facts["decking"].pop("product_type")
    built = _built(facts=facts)
    boards = _row(built, "decking.boards")
    assert boards["canonical_identity"] is None
    answers = {
        "request_id": built["manifest"]["request_id"],
        "valid_until": "2026-11-30",
        "lines": {boards["number"]: {"line_key": boards["key"], "line_sig": boards["signature"], "sku": "X", "product_confirmed": "Yes", "net_price": "1"}},
    }
    result = reconcile(built["manifest"], answers, project_id=7, organization_id="ORG-001")
    line = next(r for r in result["rows"] if r["number"] == boards["number"])
    assert line["status"] == QUOTED and line["recording"] == KEPT_ON_RESPONSE


def test_each_row_says_whether_it_is_ready_to_order():
    built = _built()
    labels = {r["key"]: r["status_label"] for r in built["manifest"]["lines"]}
    assert labels["lumber.2x10.brown-pressure-treated.10ft"] == FINAL
    assert labels["piers.helical"].startswith("ENGINEERING-DEPENDENT")
    assert labels["lumber.6x6.brown-pressure-treated.8ft"].startswith("CALCULATED — FIELD VERIFICATION")
    no_facts = _built(facts={"cutting": {"kerf_in": 0.125, "offcut_reuse": "within_use"}})
    no_labels = {r["key"]: r["status_label"] for r in no_facts["manifest"]["lines"]}
    assert no_labels["decking.boards"].startswith("PRODUCT-DEPENDENT")
    assert all("NOT READY TO ORDER" in label or label in (FINAL,) or "FIELD VERIFICATION" in label for label in no_labels.values())
    text = " ".join(" ".join(p.extract_text() or "" for p in PdfReader(BytesIO(_pdf(built))).pages).split())
    for words in ("FINAL QUANTITY", "ENGINEERING-DEPENDENT — NOT READY TO ORDER", "Only those lines are ready to order"):
        assert words in text


def test_the_pdf_carries_live_calculations_in_order():
    built = _built()
    payload = _pdf(built)
    reader = PdfReader(BytesIO(payload), strict=True)
    fields = reader.get_fields()
    numbers = [f"{r['number']:02d}" for r in built["manifest"]["lines"]]
    scripts = {}
    for page in reader.pages:
        for ref in page.get("/Annots") or []:
            annot = ref.get_object()
            if "/AA" in annot:
                scripts[annot["/T"]] = annot["/AA"]["/C"]["/JS"]
    for n in numbers:
        assert f"net_price_{n}" in scripts and f"line_total_{n}" in scripts
        assert int(fields[f"line_total_{n}"].get("/Ff", 0)) & 1  # read-only, calculated
        assert not int(fields[f"net_price_{n}"].get("/Ff", 0)) & 1  # can still be typed when there is no unit price
    assert "grand_total" in scripts and int(fields["grand_total"].get("/Ff", 0)) & 1
    order = [ref.get_object()["/T"] for ref in reader.trailer["/Root"]["/AcroForm"]["/CO"]]
    assert order == [f"net_price_{n}" for n in numbers] + [f"line_total_{n}" for n in numbers] + ["grand_total"]


NODE_RUNNER = r"""
// node -e puts the first extra argument at argv[1].
const fields = JSON.parse(process.argv[1]);
const scripts = JSON.parse(process.argv[2]);
const doc = {getField: (name) => ({valueAsString: fields[name] === undefined ? "" : String(fields[name])})};
const out = {};
for (const [name, js] of scripts) {
  const event = {value: fields[name] === undefined ? "" : fields[name]};
  new Function("event", js).call(doc, event);
  fields[name] = event.value;
  out[name] = event.value;
}
console.log(JSON.stringify(out));
"""


def _run_js(fields, scripts):
    import json
    import shutil
    import subprocess

    node = shutil.which("node")
    assert node, "node is required to run the PDF form calculations"
    result = subprocess.run([node, "-e", NODE_RUNNER, json.dumps(fields), json.dumps(scripts)], capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def test_form_calculations_give_net_line_and_grand_totals():
    scripts = [
        ("net_price_01", net_price_script("01")),
        ("net_price_02", net_price_script("02")),
        ("net_price_03", net_price_script("03")),
        ("line_total_01", line_total_script("01", 10.0)),
        ("line_total_02", line_total_script("02", 152.0)),
        ("line_total_03", line_total_script("03", None)),
        ("grand_total", grand_total_script(["01", "02", "03"])),
    ]
    out = _run_js(
        {"unit_price_01": "$40.00", "discount_01": "10%", "unit_price_02": "0.35", "discount_02": "0",
         "unit_price_03": "12", "discount_03": "5"},
        scripts,
    )
    assert out["net_price_01"] == "36.00" and out["line_total_01"] == "360.00"
    assert out["net_price_02"] == "0.35" and out["line_total_02"] == "53.20"
    assert out["net_price_03"] == "11.40" and out["line_total_03"] == ""  # quantity TBD
    assert out["grand_total"] == "413.20"


def test_form_leaves_a_typed_net_alone_without_both_inputs():
    scripts = [
        ("net_price_01", net_price_script("01")),
        ("line_total_01", line_total_script("01", 4.0)),
        ("grand_total", grand_total_script(["01"])),
    ]
    out = _run_js({"unit_price_01": "25", "discount_01": "", "net_price_01": "21.50"}, scripts)
    assert out["net_price_01"] == "21.50"  # a blank discount is not zero
    assert out["line_total_01"] == "86.00" and out["grand_total"] == "86.00"
    empty = _run_js({}, scripts)
    assert empty["net_price_01"] == "" and empty["line_total_01"] == "" and empty["grand_total"] == ""


def test_form_calculation_matches_the_server_check_to_the_cent():
    from decimal import ROUND_HALF_UP, Decimal

    cases = [("1.15", "10"), ("2.675", "0"), ("19.99", "12.5"), ("0.07", "33"), ("1234.56", "7")]
    scripts = [(f"net_price_{i:02d}", net_price_script(f"{i:02d}")) for i in range(len(cases))]
    fields = {}
    for i, (unit, discount) in enumerate(cases):
        fields[f"unit_price_{i:02d}"] = unit
        fields[f"discount_{i:02d}"] = discount
    out = _run_js(fields, scripts)
    for i, (unit, discount) in enumerate(cases):
        exact = (Decimal(unit) * (100 - Decimal(discount)) / 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        assert abs(Decimal(out[f"net_price_{i:02d}"]) - exact) <= Decimal("0.01")
