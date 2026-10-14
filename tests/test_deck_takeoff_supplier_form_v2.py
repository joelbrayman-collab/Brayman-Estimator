"""Supplier request form 2: SKU, unit cost, discount %; totals calculated by CalibraytAI.

Joel's decisions, 14 Oct 2026. The supplier types three boxes per material in any
PDF viewer. The PDF carries no JavaScript and no total fields: the Total column is
printed "Calculated by Brayman". On import the server calculates the net unit cost
(rounded to the cent), each line total (quantity x net) and the grand total, and
is the sole authority. A blank discount is not zero. Requests issued on the
historical eight-box form keep their stored PDF and their field mapping.
"""

from __future__ import annotations

import re
import shutil
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from io import BytesIO

import pytest
from pypdf import PdfReader
from pypdf.generic import ArrayObject, DictionaryObject, IndirectObject, NameObject

import app.services.brayman_supplier_estimate as supplier_estimate

from app.services.brayman_supplier_estimate import CALCULATED_BY_BRAYMAN, render_supplier_response_request
from app.services.deck_takeoff import storage
from app.services.deck_takeoff.intake import (
    EXCLUDE_DISCOUNT,
    EXCLUDE_IDENTITY,
    EXCLUDE_NOT_FINAL,
    EXCLUDE_QTY,
    EXCLUDE_SUBSTITUTION,
    INCOMPLETE,
    INVALID,
    NO_PRICES_WARNING,
    NOT_QUOTED,
    QUOTED,
    READY_TO_RECORD,
    SUBSTITUTION_REVIEW,
    SupplierResponseError,
    answers_from_values,
    net_unit_cost,
    read_response_pdf,
    reconcile,
)
from app.services.deck_takeoff.project import project_takeoff
from app.services.deck_takeoff.supplier_request import build_request
from app.services.organizations import DEFAULT_ORGANIZATION_ID
from tests.test_deck_takeoff_supplier_documents import _built, _fill, _row
from tests.test_deck_takeoff_workflow import VALID_UNTIL, _facts_form, _issue, _setup, app, client  # noqa: F401

V2 = ("sku", "unit_cost", "discount")
LEGACY_ONLY = ("product_confirmed", "unit_price", "net_price", "availability", "lead_time", "substitution", "line_total")
CENT = Decimal("0.01")


def _v2(project_id=7, **kw):
    return _built(project_id=project_id, response_form=2, **kw)


def _pdf(built):
    return render_supplier_response_request(**built["document"])


SCRIPT_KEYS = ("/JS", "/AA", "/OpenAction")
SCRIPT_TOKEN = re.compile(rb"/(JS|JavaScript|AA|OpenAction)(?=[\s/\[\]<>()]|$)")


def _javascript_found(payload: bytes) -> list:
    """Every place in the PDF that could carry a script, or [] when there is none.

    Scripts can only live in PDF dictionaries (/JS, /S /JavaScript, /AA, /OpenAction,
    the /Names /JavaScript tree). So every object number in the cross-reference table
    is walked, and the file's syntax is also searched with stream data removed.

    The whole file is not byte-searched: ReportLab ASCII85-encodes compressed page
    content as printable text, and those bytes change with the folder the app runs
    from (the logo's XObject name is an MD5 of its path). Under some folder names the
    text happens to contain "/JS" without the PDF carrying any script.
    """
    found = []
    syntax = re.sub(rb"stream\r?\n.*?endstream", b"stream endstream", payload, flags=re.S)
    found += [f"syntax {m.group(0).decode()}" for m in SCRIPT_TOKEN.finditer(syntax)]
    reader = PdfReader(BytesIO(payload), strict=True)
    seen = set()

    def walk(obj, where):
        if isinstance(obj, IndirectObject):
            if obj.idnum in seen:
                return
            seen.add(obj.idnum)
            where, obj = f"object {obj.idnum}", obj.get_object()
        if isinstance(obj, DictionaryObject):
            for key, value in obj.items():
                if key in SCRIPT_KEYS or (key == "/S" and value == "/JavaScript"):
                    found.append(f"{where} {key}")
                walk(value, where)
        elif isinstance(obj, ArrayObject):
            for value in obj:
                walk(value, where)
        elif isinstance(obj, NameObject) and obj == "/JavaScript":
            found.append(f"{where} /JavaScript")

    walk(reader.trailer, "trailer")
    for number in range(1, int(reader.trailer["/Size"])):
        walk(IndirectObject(number, 0, reader), f"object {number}")
    return found


def _expected(unit, discount, qty):
    net = (Decimal(unit) * (100 - Decimal(discount)) / 100).quantize(CENT, rounding=ROUND_HALF_UP)
    return net, (net * Decimal(str(qty))).quantize(CENT, rounding=ROUND_HALF_UP)


def _answers(built, lines, **closing):
    by_number = {}
    for number, values in lines.items():
        row = next(r for r in built["manifest"]["lines"] if r["number"] == number)
        by_number[number] = {"line_key": row["key"], "line_sig": row["signature"], **values}
    return {"request_id": built["manifest"]["request_id"], "valid_until": closing.pop("valid_until", "2026-11-30"), "lines": by_number, **closing}


def _reconcile(built, answers, project_id=7):
    return reconcile(built["manifest"], answers, project_id=project_id, organization_id="ORG-001", catalogue_codes=frozenset({"TEST-PT-2X12-8"}))


def _priced(built):
    return [r for r in built["manifest"]["lines"] if r["purchasing_quantity"] is not None]


def _final(built):
    """Lines marked FINAL QUANTITY: the only lines that can enter the Recordable Quoted Total."""
    return [r for r in built["manifest"]["lines"] if r["complete"] and r["purchasing_quantity"] is not None]


# --- The PDF -----------------------------------------------------------------


def test_each_material_has_three_supplier_boxes_and_a_printed_total():
    built = _v2()
    payload = _pdf(built)
    reader = PdfReader(BytesIO(payload), strict=True)
    fields = reader.get_fields()
    assert fields["response_form"]["/V"] == "2" and built["manifest"]["response_form"] == 2
    for row in built["manifest"]["lines"]:
        n = f"{row['number']:02d}"
        boxes = sorted(name[: -len(n) - 1] for name in fields if name.endswith(f"_{n}") and not name.startswith(("line_key", "line_sig")))
        assert boxes == sorted(V2)
        for typed in V2:
            assert not int(fields[f"{typed}_{n}"].get("/Ff", 0)) & 1  # editable
        for legacy in LEGACY_ONLY:
            assert f"{legacy}_{n}" not in fields  # no total box the supplier could type in
        assert f"qty_{n}" not in fields
        assert fields[f"line_key_{n}"]["/V"] == row["key"] and fields[f"line_sig_{n}"]["/V"] == row["signature"]
    assert "grand_total" not in fields
    for name in ("bmr_contact", "response_date", "valid_until", "general_notes"):
        assert name in fields
    text = " ".join(" ".join(p.extract_text() or "" for p in reader.pages).split())
    assert text.count(CALCULATED_BY_BRAYMAN) >= len(_priced(built)) + 1
    for words in ("SKU", "Unit cost", "Discount %", "Total", "a blank discount is not zero", "Any PDF viewer that saves form fields",
                  "Substitutions: write the original line number and your replacement SKU"):
        assert words in text
    assert len(reader.pages) == 3


def test_the_pdf_carries_no_javascript():
    payload = _pdf(_v2())
    reader = PdfReader(BytesIO(payload))
    assert _javascript_found(payload) == []
    assert b"/JavaScript" not in payload  # cannot occur in ASCII85 text, so this byte check stays exact
    assert "/CO" not in reader.trailer["/Root"]["/AcroForm"]
    for page in reader.pages:
        for ref in page.get("/Annots") or []:
            assert "/AA" not in ref.get_object()
    assert b"/NeedAppearances true" in payload  # viewers draw the typed values


def test_the_javascript_check_finds_the_scripts_on_the_historical_form():
    """The check is not weaker than a byte search: the eight-box form's calculation scripts are found."""
    found = _javascript_found(_pdf(_built()))
    assert any(f.endswith(" /AA") for f in found) and any(f.endswith(" /JS") for f in found)
    assert any(f == "syntax /JS" for f in found)


def test_the_pdf_carries_no_javascript_wherever_the_app_is_installed(tmp_path, monkeypatch):
    """Form 2 has no script from any install folder (the PDF bytes vary with the folder)."""
    logo = supplier_estimate._logo()
    names = set()
    for i in range(24):
        copy = tmp_path / f"Brayman-Estimator-drawings-20261014-{150000 + i}" / "app/static/branding" / logo.name
        copy.parent.mkdir(parents=True)
        shutil.copy(logo, copy)
        monkeypatch.setattr(supplier_estimate, "_logo", lambda copy=copy: copy)
        payload = _pdf(_v2())
        names.update(re.findall(rb"/FormXob\.[0-9a-f]+", payload))
        assert _javascript_found(payload) == [], copy.parent.parent.parent.parent
    assert len(names) == 24  # each folder really produced different PDF bytes


def test_a_quantity_tbd_line_prints_qty_tbd():
    built = _v2(facts={"cutting": {"kerf_in": 0.125}})
    text = " ".join(p.extract_text() or "" for p in PdfReader(BytesIO(_pdf(built))).pages)
    assert "Qty TBD" in text


def test_a_form_2_request_has_its_own_identity():
    assert _v2()["manifest"]["request_id"] != _built()["manifest"]["request_id"]


# --- Server calculation ------------------------------------------------------


@pytest.mark.parametrize("unit, discount", [("1.15", "10"), ("2.675", "0"), ("19.99", "12.5"), ("0.07", "33"), ("1234.56", "7"), ("0.125", "50"), ("38.50", "10")])
def test_net_unit_cost_rounds_to_the_cent_half_up(unit, discount):
    exact = Decimal(unit) * (100 - Decimal(discount)) / 100
    assert net_unit_cost(Decimal(unit), Decimal(discount)) == exact.quantize(CENT, rounding=ROUND_HALF_UP)


def test_line_total_is_quantity_times_the_rounded_net_and_the_recordable_total_adds_eligible_lines():
    built = _v2()
    rows = _final(built)[:4]
    cases = [("38.50", "10"), ("51.25", "10"), ("0.125", "50"), ("19.99", "12.5")]
    answers = _answers(built, {r["number"]: {"sku": f"S{i}", "unit_cost": u, "discount": d} for i, (r, (u, d)) in enumerate(zip(rows, cases))})
    # One more final line priced without a discount: incomplete, not in the total.
    extra = _final(built)[4]
    answers["lines"][extra["number"]] = {"line_key": extra["key"], "line_sig": extra["signature"], "sku": "S9", "unit_cost": "99", "discount": ""}
    result = _reconcile(built, answers)
    by = {r["number"]: r for r in result["rows"]}
    total = Decimal("0")
    for r, (u, d) in zip(rows, cases):
        net, line = _expected(u, d, r["purchasing_quantity"])
        assert by[r["number"]]["net_price"] == str(net) and by[r["number"]]["line_value"] == str(line)
        total += line
    assert by[extra["number"]]["status"] == INCOMPLETE and by[extra["number"]]["line_value"] is None
    assert by[extra["number"]]["total_exclusions"] == [EXCLUDE_DISCOUNT] and by[extra["number"]]["partial_quote"]
    assert result["recordable_quoted_total"] == str(total) and result["recordable_lines"] == 4
    assert result["excluded_lines"] == 1 and result["provisional_value"] is None  # no arithmetic without a discount
    # 51.25 less 10% is 46.125: the net is rounded to 46.13 before multiplying.
    assert by[rows[1]["number"]]["net_price"] == "46.13"




@pytest.mark.parametrize(
    "values, status",
    [
        ({"sku": "X", "unit_cost": "abc", "discount": "0"}, INVALID),
        ({"sku": "X", "unit_cost": "NaN", "discount": "0"}, INVALID),
        ({"sku": "X", "unit_cost": "-4", "discount": "0"}, INVALID),
        ({"sku": "X", "unit_cost": "10", "discount": "150"}, INVALID),
        ({"sku": "X", "unit_cost": "10", "discount": "-5"}, INVALID),
        ({"sku": "X", "unit_cost": "10", "discount": "Infinity"}, INVALID),
        ({"sku": "X", "unit_cost": "1E+400", "discount": "0"}, INVALID),
        ({"unit_cost": "10", "discount": "0"}, INCOMPLETE),
        ({"sku": "X", "discount": "5"}, INCOMPLETE),
        ({"sku": "X", "unit_cost": "10", "discount": ""}, INCOMPLETE),
    ],
)
def test_bad_or_missing_answers_are_never_recordable(values, status):
    built = _v2()
    row = _row(built, "lumber.2x12")
    result = _reconcile(built, _answers(built, {row["number"]: values}))
    line = next(r for r in result["rows"] if r["number"] == row["number"])
    assert line["status"] == status and line["recording"] != READY_TO_RECORD
    if values.get("sku") or status == INVALID:
        assert line["line_value"] is None  # no total without a valid unit cost and discount


def test_a_blank_discount_is_incomplete_and_never_assumed():
    built = _v2()
    row = _row(built, "lumber.2x12")
    result = _reconcile(built, _answers(built, {row["number"]: {"sku": "X", "unit_cost": "30", "discount": ""}}))
    line = next(r for r in result["rows"] if r["number"] == row["number"])
    assert line["status"] == INCOMPLETE and line["net_price"] is None and line["line_value"] is None
    assert any("blank discount is not zero" in p for p in line["problems"])
    assert result["recordable_quoted_total"] is None and EXCLUDE_DISCOUNT in line["total_exclusions"]


def test_zero_discount_is_a_real_discount_and_enters_the_total():
    built = _v2()
    row = _final(built)[0]
    result = _reconcile(built, _answers(built, {row["number"]: {"sku": "X", "unit_cost": "30", "discount": "0"}}))
    line = next(r for r in result["rows"] if r["number"] == row["number"])
    assert line["in_recordable_total"] and line["net_price"] == "30.00"
    assert result["recordable_quoted_total"] == str((Decimal("30") * row["purchasing_quantity"]).quantize(CENT))


@pytest.mark.parametrize(
    "case, values, reason",
    [
        ("missing SKU", {"unit_cost": "10", "discount": "0"}, "Missing SKU"),
        ("blank discount", {"sku": "X", "unit_cost": "10", "discount": ""}, "Blank discount"),
        ("missing unit cost", {"sku": "X", "discount": "5"}, "Missing unit cost"),
        ("invalid pricing", {"sku": "X", "unit_cost": "abc", "discount": "0"}, "Invalid pricing"),
    ],
)
def test_each_exclusion_reason_is_named(case, values, reason):
    built = _v2()
    row = _final(built)[0]
    result = _reconcile(built, _answers(built, {row["number"]: values}))
    line = next(r for r in result["rows"] if r["number"] == row["number"])
    assert not line["in_recordable_total"] and line["partial_quote"]
    assert any(x.startswith(reason) for x in line["total_exclusions"]), case
    assert result["recordable_quoted_total"] is None


def test_a_quantity_not_marked_final_is_provisional_only():
    built = _v2()
    row = _row(built, "lumber.2x12")  # ENGINEERING-DEPENDENT: a quantity, but not FINAL QUANTITY
    assert not row["complete"]
    result = _reconcile(built, _answers(built, {row["number"]: {"sku": "X", "unit_cost": "10", "discount": "0"}}))
    line = next(r for r in result["rows"] if r["number"] == row["number"])
    assert line["status"] == QUOTED and line["line_value"] == "100.00"
    assert line["total_exclusions"] == [EXCLUDE_NOT_FINAL]
    assert result["recordable_quoted_total"] is None and result["provisional_value"] == "100.00"


def test_a_tbd_quantity_is_excluded():
    built = _v2(facts={"cutting": {"kerf_in": 0.125}})
    row = next(r for r in built["manifest"]["lines"] if r["purchasing_quantity"] is None)
    result = _reconcile(built, _answers(built, {row["number"]: {"sku": "X", "unit_cost": "10", "discount": "0"}}))
    line = next(r for r in result["rows"] if r["number"] == row["number"])
    assert line["total_exclusions"] == [EXCLUDE_QTY] and line["line_value"] is None


def test_an_identity_mismatch_is_excluded_and_named():
    built = _v2()
    row = _final(built)[0]
    answers = _answers(built, {row["number"]: {"sku": "X", "unit_cost": "10", "discount": "0"}})
    answers["lines"][row["number"]]["line_sig"] = "0" * 24
    result = _reconcile(built, answers)
    line = next(r for r in result["rows"] if r["number"] == row["number"])
    assert line["total_exclusions"] == [EXCLUDE_IDENTITY] and result["recordable_quoted_total"] is None


def test_an_unresolved_substitution_never_enters_the_recordable_total():
    built = _v2()
    a, b = _final(built)[0], _final(built)[1]
    answers = _answers(built, {a["number"]: {"sku": "ALT-1", "unit_cost": "10", "discount": "0"},
                               b["number"]: {"sku": "BMR-2", "unit_cost": "20", "discount": "0"}},
                       general_notes=f"Line {a['number']} - replacement SKU ALT-1")
    result = _reconcile(built, answers)
    by = {r["number"]: r for r in result["rows"]}
    assert by[a["number"]]["status"] == SUBSTITUTION_REVIEW and EXCLUDE_SUBSTITUTION in by[a["number"]]["total_exclusions"]
    assert result["recordable_quoted_total"] == str((Decimal("20") * b["purchasing_quantity"]).quantize(CENT))
    assert result["provisional_value"] == str((Decimal("10") * a["purchasing_quantity"]).quantize(CENT))


def test_a_historical_request_gets_no_form_2_totals():
    built = _built()
    row = _row(built, "lumber.2x12")
    result = _reconcile(built, _answers(built, {row["number"]: {"sku": "X", "product_confirmed": "Yes", "unit_price": "10", "discount": "0"}}))
    assert "recordable_quoted_total" not in result and "provisional_value" not in result


def test_a_total_typed_into_a_tampered_pdf_is_ignored():
    built = _v2()
    row = _row(built, "lumber.2x12")
    answers = _answers(built, {row["number"]: {"sku": "X", "unit_cost": "10", "discount": "0", "line_total": "1.00"}}, grand_total="1.00")
    result = _reconcile(built, answers)
    line = next(r for r in result["rows"] if r["number"] == row["number"])
    assert line["line_value"] == str((Decimal("10") * Decimal(str(row["purchasing_quantity"]))).quantize(CENT))
    assert "grand_total" not in result
    assert result["provisional_value"] == line["line_value"]  # the server's figure, never the PDF's


def test_an_empty_response_is_flagged():
    built = _v2()
    result = _reconcile(built, _answers(built, {}))
    assert result["no_prices_found"] and result["issues"][0] == NO_PRICES_WARNING
    assert all(r["status"] == NOT_QUOTED for r in result["rows"])


def test_old_form_boxes_injected_into_a_form_2_response_are_ignored():
    built = _v2()
    row = _row(built, "lumber.2x12")
    answers = _answers(built, {row["number"]: {"sku": "X", "unit_cost": "10", "discount": "10", "net_price": "1.00", "substitution": "Brand Y", "product_confirmed": "no"}})
    line = next(r for r in _reconcile(built, answers)["rows"] if r["number"] == row["number"])
    assert line["status"] == QUOTED and line["net_price"] == "9.00"
    assert set(line["answers"]) == set(V2)


def test_notes_line_numbers_are_read_in_the_usual_forms():
    from app.services.deck_takeoff.intake import notes_line_numbers

    assert notes_line_numbers("Line 9 - replacement SKU GATE-48-BLK") == {9}
    assert notes_line_numbers("line 3: ALT-3\nItem #12 replaced by X; No. 4 sub") == {3, 12, 4}
    assert notes_line_numbers("Prices valid with yard pickup.") == set()


def test_a_substitution_in_general_notes_holds_that_line_for_brayman_review():
    built = _v2()
    stringer = _row(built, "lumber.2x12")
    other = next(r for r in _priced(built) if r["key"] != stringer["key"])
    notes = f"Line {stringer['number']} - replacement SKU ALT-2X12-8"
    result = _reconcile(built, _answers(built, {
        stringer["number"]: {"sku": "ALT-2X12-8", "unit_cost": "28", "discount": "0"},
        other["number"]: {"sku": "BMR-1", "unit_cost": "10", "discount": "0"},
    }, general_notes=notes))
    by = {r["number"]: r for r in result["rows"]}
    assert by[stringer["number"]]["status"] == SUBSTITUTION_REVIEW and by[stringer["number"]]["recording"] != READY_TO_RECORD
    assert by[other["number"]]["status"] == QUOTED
    assert result["notes_review_required"] and result["notes_line_numbers"] == [stringer["number"]]
    assert any("must read them and confirm" in i for i in result["issues"])


def test_a_historical_request_ignores_the_form_2_notes_rule():
    built = _built()  # form 1
    row = _row(built, "lumber.2x12")
    answers = _answers(built, {row["number"]: {"sku": "X", "product_confirmed": "Yes", "unit_price": "10", "discount": "0"}}, general_notes=f"Line {row['number']} something")
    result = _reconcile(built, answers)
    line = next(r for r in result["rows"] if r["number"] == row["number"])
    assert line["status"] == QUOTED and not result["notes_review_required"]


def test_identity_and_isolation_hold_for_form_2():
    built = _v2()
    row = _row(built, "lumber.2x12")
    tampered = _answers(built, {row["number"]: {"sku": "X", "unit_cost": "10", "discount": "0"}})
    tampered["lines"][row["number"]]["line_sig"] = "0" * 24
    line = next(r for r in _reconcile(built, tampered)["rows"] if r["number"] == row["number"])
    assert line["status"] == INVALID
    with pytest.raises(SupplierResponseError, match="not on this project"):
        _reconcile(built, _answers(built, {}), project_id=8)
    other = _answers(built, {})
    other["request_project"] = "8"
    with pytest.raises(SupplierResponseError, match="different project"):
        _reconcile(built, other)


# --- Historical requests are preserved --------------------------------------


def test_a_historical_eight_box_request_keeps_its_pdf_and_mapping(app, client):
    project, other, account = _setup()
    client.post(f"/projects/{project.id}/deck-takeoff/product-facts", data=_facts_form())
    state = project_takeoff(organization_id=DEFAULT_ORGANIZATION_ID, project_id=project.id)
    old = build_request(
        takeoff=state["takeoff"], project_id=project.id, organization_id=DEFAULT_ORGANIZATION_ID, project_name=project.name,
        project_address="", supplier_name=account.supplier.legal_name, contractor_supplier_account_id=account.id,
        supplier_id=account.supplier_id, supplier_location_id=account.supplier_location_id, issued_by="Office (13 Oct)",
        issued_at=datetime(2026, 10, 13, 15, 0), response_form=1,
    )
    manifest = dict(old["manifest"])
    manifest.pop("response_form")  # manifests stored before form 2 carry no marker
    old_pdf = render_supplier_response_request(**old["document"])
    storage.save_request(DEFAULT_ORGANIZATION_ID, project.id, manifest, old_pdf)
    rid = manifest["request_id"]

    # Issuing now makes a new form-2 request; the historical one is untouched.
    new_pdf, new_fields, _keys = _issue(client, project, account)
    assert new_fields["request_id"]["/V"] != rid and new_fields["response_form"]["/V"] == "2"
    assert client.get(f"/projects/{project.id}/deck-takeoff/requests/{rid}.pdf").data == old_pdf

    # The historical hand-entry page and import still use the eight boxes.
    entry = client.get(f"/projects/{project.id}/deck-takeoff/requests/{rid}/enter")
    assert b'name="product_confirmed_' in entry.data and b'name="unit_cost_' not in entry.data
    row = next(r for r in manifest["lines"] if r["key"].startswith("lumber.2x12"))
    n = f"{row['number']:02d}"
    form = {
        "request_id": rid, "request_project": str(project.id), f"line_key_{n}": row["key"], f"line_sig_{n}": row["signature"],
        f"sku_{n}": "OLD-1", f"product_confirmed_{n}": "Substitute", f"unit_price_{n}": "40", f"discount_{n}": "10",
        f"substitution_{n}": "Brand Y", "valid_until": VALID_UNTIL, "actor_display_name": "Test office",
    }
    result = client.post(f"/projects/{project.id}/deck-takeoff/responses", data=form)
    view = client.get(result.headers["Location"])
    assert b"Substitution: Brand Y" in view.data and b"Substitution review" in view.data and b"36.00" in view.data
    stored = storage.load_request(DEFAULT_ORGANIZATION_ID, project.id, rid)
    assert "response_form" not in stored

    # The new request's hand-entry page shows the four boxes.
    new_entry = client.get(f"/projects/{project.id}/deck-takeoff/requests/{new_fields['request_id']['/V']}/enter")
    assert b'name="unit_cost_' in new_entry.data and b'name="product_confirmed_' not in new_entry.data
    assert b'data-form-version="2"' in new_entry.data


# --- Round trips -------------------------------------------------------------


def test_a_filled_pdf_round_trips_without_any_viewer_calculation():
    built = _v2()
    payload = _pdf(built)
    stringer = _row(built, "lumber.2x12")
    others = [r for r in _priced(built) if r["key"] != stringer["key"]][:2]
    typed = {"bmr_contact": "Darcy (synthetic)", "response_date": "2026-10-15", "valid_until": "2026-11-30"}
    for i, (row, unit, discount) in enumerate([(stringer, "30.00", "10"), (others[0], "2.50", "0"), (others[1], "7.95", "15")]):
        n = f"{row['number']:02d}"
        typed.update({f"sku_{n}": f"BMR-{i}", f"unit_cost_{n}": unit, f"discount_{n}": discount})
    values = read_response_pdf(_fill(payload, typed))
    result = _reconcile(built, answers_from_values(values))
    by = {r["key"]: r for r in result["rows"]}
    s = by[stringer["key"]]
    assert s["status"] == QUOTED and s["recording"] == READY_TO_RECORD and s["net_price"] == "27.00"
    assert Decimal(s["line_value"]) == Decimal("27.00") * Decimal(str(stringer["purchasing_quantity"]))
    assert by[others[0]["key"]]["net_price"] == "2.50"  # explicit 0% is a real discount of zero
    priced = [(stringer, "30.00", "10"), (others[0], "2.50", "0"), (others[1], "7.95", "15")]
    recordable = sum(_expected(u, d, r["purchasing_quantity"])[1] for r, u, d in priced if r["complete"])
    provisional = sum(_expected(u, d, r["purchasing_quantity"])[1] for r, u, d in priced if not r["complete"])
    assert result["recordable_quoted_total"] == str(recordable) and result["provisional_value"] == str(provisional)
    assert not result["no_prices_found"]


def test_form_2_response_page_shows_server_totals(app, client):
    project, _other, account = _setup()
    pdf, fields, keys = _issue(client, project, account)
    n = keys["lumber.2x12.brown-pressure-treated.8ft"]  # quantity 10, not FINAL QUANTITY
    b = next(v for k, v in keys.items() if k.startswith("decking.boards."))  # FINAL QUANTITY
    returned = _fill(pdf, {f"sku_{n}": "BMR-2128-PT", f"unit_cost_{n}": "40", f"discount_{n}": "10",
                           f"sku_{b}": "BMR-DECK", f"unit_cost_{b}": "10", f"discount_{b}": "0",
                           "valid_until": VALID_UNTIL, "response_date": "2026-10-15"})
    imported = client.post(f"/projects/{project.id}/deck-takeoff/responses", data={"response_pdf": (BytesIO(returned), "r.pdf")}, content_type="multipart/form-data")
    view = client.get(imported.headers["Location"])
    record = storage.load_response(DEFAULT_ORGANIZATION_ID, project.id, imported.headers["Location"].rstrip("/").split("/")[-1])
    board = next(r for r in record["rows"] if r["number"] == int(b))
    assert record["recordable_quoted_total"] == board["line_value"] and record["provisional_value"] == "360.00"
    assert b"Recordable Quoted Total" in view.data and b"data-grand-total" in view.data and b"360.00" in view.data and b"36.00" in view.data
    assert b"Quantity not verified" in view.data and b"not</strong> in the Recordable Quoted Total" in view.data
    assert b"not an approved cost" in view.data and b"Approved Cost Total" not in view.data
    assert b"Availability" not in view.data and b"Confirmed</th>" not in view.data


def test_a_pdf_whose_viewer_dropped_the_values_warns_and_keeps_manual_entry(app, client):
    project, _other, account = _setup()
    pdf, fields, _keys = _issue(client, project, account)
    request_id = fields["request_id"]["/V"]
    unchanged = _fill(pdf, {"bmr_contact": "Darcy (synthetic)"})  # typed prices were not saved
    response = client.post(f"/projects/{project.id}/deck-takeoff/responses", data={"response_pdf": (BytesIO(unchanged), "r.pdf")},
                           content_type="multipart/form-data")
    assert response.status_code == 302 and response.headers["Location"].endswith(f"/requests/{request_id}/enter")
    page = client.get(response.headers["Location"])
    assert b"may not have saved them" in page.data and b'name="unit_cost_' in page.data
    assert storage.list_responses(DEFAULT_ORGANIZATION_ID, project.id) == []


def test_supplier_notes_must_be_reviewed_before_any_price_is_recorded(app, client):
    from app.models.supplier_catalogue import SupplierProductPriceEvidence

    project, _other, account = _setup()
    pdf, fields, keys = _issue(client, project, account)
    stringer = keys["lumber.2x12.brown-pressure-treated.8ft"]
    gate = keys["gate"]
    typed = {
        f"sku_{stringer}": "BMR-2128-PT", f"unit_cost_{stringer}": "40", f"discount_{stringer}": "10",
        f"sku_{gate}": "GATE-48-BLK", f"unit_cost_{gate}": "300", f"discount_{gate}": "0",
        "general_notes": f"Line {int(gate)} - replacement SKU GATE-48-BLK", "valid_until": VALID_UNTIL, "response_date": "2026-10-15",
    }
    imported = client.post(f"/projects/{project.id}/deck-takeoff/responses", data={"response_pdf": (BytesIO(_fill(pdf, typed)), "r.pdf")}, content_type="multipart/form-data")
    response_url = imported.headers["Location"]
    response_id = response_url.rstrip("/").split("/")[-1]
    view = client.get(response_url)
    assert b"BRAYMAN REVIEW REQUIRED" in view.data and b"GATE-48-BLK" in view.data and b'name="notes_reviewed"' in view.data
    refused = client.post(f"/projects/{project.id}/deck-takeoff/responses/{response_id}/record", data={"actor_display_name": "Joel (test)"}, follow_redirects=True)
    assert b"general notes" in refused.data and SupplierProductPriceEvidence.query.count() == 0
    done = client.post(f"/projects/{project.id}/deck-takeoff/responses/{response_id}/record",
                       data={"actor_display_name": "Joel (test)", "notes_reviewed": "yes"}, follow_redirects=True)
    assert b"1 supplier prices recorded" in done.data  # the stringer only; the substituted gate is held
    assert b"Supplier notes reviewed by Joel (test)" in done.data
    assert SupplierProductPriceEvidence.query.count() == 1


# --- Real viewers ------------------------------------------------------------
# Synthetic request typed into and saved by Apple Preview (macOS 26.5.2, 14 Oct 2026)
# and by pdf.js 4.10.38 (the engine behind Firefox's PDF viewer). Neither runs any
# calculation; the server does all of it.

FIXTURES = __import__("pathlib").Path(__file__).parent / "fixtures" / "supplier_forms"


@pytest.mark.parametrize("name, sku", [("form2-saved-by-apple-preview.pdf", "PREVIEW"), ("form2-saved-by-pdfjs.pdf", "PDFJS")])
def test_a_pdf_saved_by_a_real_viewer_keeps_its_values_and_identity(name, sku):
    built = _v2()
    values = read_response_pdf((FIXTURES / name).read_bytes())
    assert values["request_id"] == built["manifest"]["request_id"] and values["response_form"] == "2"
    for row in built["manifest"]["lines"]:
        n = f"{row['number']:02d}"
        assert values[f"line_key_{n}"] == row["key"] and values[f"line_sig_{n}"] == row["signature"]
    assert values["sku_01"] == f"{sku}-SKU-1" and values["unit_cost_01"] == "38.50" and values["discount_01"] == "10"
    result = _reconcile(built, answers_from_values(values))
    by = {r["number"]: r for r in result["rows"]}
    assert by[1]["status"] == QUOTED and by[1]["net_price"] == "34.65" and by[1]["line_value"] == "623.70"
    assert by[4]["status"] == INCOMPLETE and by[4]["line_value"] is None  # blank discount
    assert by[5]["status"] == QUOTED and by[5]["net_price"] == "189.00" and by[5]["line_value"] == "1890.00"  # explicit 0%
    assert result["recordable_quoted_total"] == "623.70"  # line 1 only: line 4 has no discount, line 5 is not FINAL QUANTITY
    assert by[4]["total_exclusions"] == [EXCLUDE_DISCOUNT] and by[5]["total_exclusions"] == [EXCLUDE_NOT_FINAL]
    assert result["provisional_value"] == "1890.00"


def test_manual_entry_uses_the_same_recordable_rule_as_pdf_import(app, client):
    project, _other, account = _setup()
    pdf, fields, keys = _issue(client, project, account)
    request_id = fields["request_id"]["/V"]
    page = client.get(f"/projects/{project.id}/deck-takeoff/requests/{request_id}/enter")
    assert b"Recordable Quoted Total (preview; the server recalculates)" in page.data and b'data-final="1"' in page.data
    board = next(v for k, v in keys.items() if k.startswith("decking.boards."))
    stringer = keys["lumber.2x12.brown-pressure-treated.8ft"]
    typed = {f"sku_{board}": "BMR-DECK", f"unit_cost_{board}": "10", f"discount_{board}": "0",
             f"sku_{stringer}": "BMR-2128-PT", f"unit_cost_{stringer}": "40", f"discount_{stringer}": "10",
             "valid_until": VALID_UNTIL, "response_date": "2026-10-15"}
    via_pdf = client.post(f"/projects/{project.id}/deck-takeoff/responses", data={"response_pdf": (BytesIO(_fill(pdf, typed)), "r.pdf")},
                          content_type="multipart/form-data")
    form = {"request_id": request_id, "request_project": str(project.id), "actor_display_name": "Test office", **typed}
    for n in (board, stringer):
        form[f"line_key_{n}"] = fields[f"line_key_{n}"]["/V"]
        form[f"line_sig_{n}"] = fields[f"line_sig_{n}"]["/V"]
    by_hand = client.post(f"/projects/{project.id}/deck-takeoff/responses", data=form)
    a = storage.load_response(DEFAULT_ORGANIZATION_ID, project.id, via_pdf.headers["Location"].rstrip("/").split("/")[-1])
    b = storage.load_response(DEFAULT_ORGANIZATION_ID, project.id, by_hand.headers["Location"].rstrip("/").split("/")[-1])
    for key in ("recordable_quoted_total", "recordable_lines", "excluded_lines", "provisional_value", "provisional_lines"):
        assert a[key] == b[key], key
    assert a["provisional_value"] == "360.00"
