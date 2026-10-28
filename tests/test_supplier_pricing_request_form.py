"""The approved Supplier Pricing Request form as the repository template (Joel, 28 Oct 2026). Synthetic data only.

The filled form must be the approved form: the same fields (names, positions, sizes, which are read-only), the same
calculation (quantity x unit cost, subtotal, 13 % HST, the two-page summary and its groups), the same text in the
same places. Joel's additions: the supplier's contact under the supplier's name, and the blank master. Real job
data and the approved PDF itself stay outside Git; the geometry below was read from the approved PDF.
"""

from __future__ import annotations

import re
from io import BytesIO
from types import SimpleNamespace

import pytest
from pypdf import PdfReader

from app.services.supplier_pricing_request_form import (
    SupplierPricingFormError,
    calculation_script,
    render_blank_supplier_pricing_request_form,
    render_supplier_pricing_request_form,
    request_for_supplier_account,
)

KEYS = ["hardie", "soffit", "fascia", "corner", "wtrim", "dtrim", "drip", "freeze", "hardieacc", "alumacc"]
SIDING = {"hardie", "hardieacc"}


def _request(**over):
    rows = [(k, f"Synthetic item {n}", f"Synthetic spec {n}", (n + 1) * 25, "LF" if n else "SF")
            for n, k in enumerate(KEYS)]
    data = dict(project="Synthetic Job (synthetic)", supplier="Synthetic Supply - Somewhere",
                supplier_tag="SYNTHETIC SUPPLY / SOMEWHERE", requested="October 28, 2026",
                plans="Synthetic Plans - Aug. 20, 2026", scope="Siding / aluminum package",
                items=[dict(key=k, item=i, spec=s, qty=q, unit=u, group="siding" if k in SIDING else "alum")
                       for k, i, s, q, u in rows],
                groups=[dict(key="siding", label="Siding package"),
                        dict(key="alum", label="Soffit, fascia & aluminum")])
    data.update(over)
    return data


def _widgets(pdf):
    reader = PdfReader(BytesIO(pdf))
    out = {}
    for number, page in enumerate(reader.pages):
        for annot in page.get("/Annots", []):
            w = annot.get_object()
            out[str(w["/T"])] = {"page": number, "rect": [round(float(v)) for v in w["/Rect"]],
                                 "read_only": bool(int(w.get("/Ff", 0)) & 1), "da": str(w.get("/DA")),
                                 "value": str(w.get("/V") or ""), "aa": "/AA" in w}
    return reader, out


# The approved form's fields, read from the approved PDF: name -> (page, rect, read-only, font size).
def _approved_fields():
    fields = {}
    for n, key in enumerate(KEYS):
        b = 545 - 39 * (n + 1)
        fields[f"qty_{key}"] = (0, [347, b + 8, 386, b + 30], False, 8)
        fields[f"cost_{key}"] = (0, [443, b + 8, 509, b + 30], False, 8)
        fields[f"ext_{key}"] = (0, [518, b + 8, 588, b + 30], True, 8)
    fields.update({
        "subtotal": (0, [487, 119, 582, 138], True, 8), "hst": (0, [487, 99, 582, 118], True, 8),
        "total_hst": (0, [487, 80, 582, 99], True, 9), "quote_no": (0, [34, 41, 154, 63], False, 8),
        "prepared_by": (0, [170, 41, 290, 63], False, 8), "valid_until": (0, [306, 41, 406, 63], False, 8),
        "supplier_notes": (0, [422, 23, 592, 63], False, 7),
        "summary_total": (1, [390, 613, 575, 640], True, 13), "summary_hst": (1, [390, 562, 575, 582], True, 9),
        "summary_total_hst": (1, [390, 541, 575, 561], True, 10), "sum_siding": (1, [425, 480, 575, 501], True, 9),
        "sum_alum": (1, [425, 432, 575, 453], True, 9), "adj_1": (1, [34, 339, 578, 361], False, 7),
        "adj_2": (1, [34, 308, 578, 330], False, 7), "adj_3": (1, [34, 277, 578, 299], False, 7),
        "adj_4": (1, [34, 246, 578, 268], False, 7), "summary_prepared": (1, [34, 34, 184, 56], False, 8),
        "summary_date": (1, [204, 34, 324, 56], False, 8), "summary_quote": (1, [344, 34, 464, 56], False, 8),
    })
    return fields


def test_the_filled_form_has_exactly_the_approved_fields_in_the_approved_places():
    _reader, widgets = _widgets(render_supplier_pricing_request_form(_request()))
    approved = _approved_fields()
    assert set(widgets) == set(approved)  # 49 fields, the approved names
    assert len(widgets) == 49
    for name, (page, rect, read_only, size) in approved.items():
        w = widgets[name]
        assert (w["page"], w["rect"], w["read_only"]) == (page, rect, read_only), name
        assert w["da"] == f"/Helv {size} Tf 0 0 0 rg", name
    # Supplier Qty is pre-filled with the takeoff quantity (a plain number the calculation reads).
    assert widgets["qty_hardie"]["value"] == "25" and widgets["qty_alumacc"]["value"] == "250"
    # The calculation runs when a quantity, a unit cost, the quote # or Prepared by changes.
    assert {n for n, w in widgets.items() if w["aa"]} == (
        {f"qty_{k}" for k in KEYS} | {f"cost_{k}" for k in KEYS} | {"quote_no", "prepared_by"})


def test_the_text_is_the_approved_text_in_the_approved_places():
    reader, _ = _widgets(render_supplier_pricing_request_form(_request(items=[
        dict(_request()["items"][0], qty=1750)] + _request()["items"][1:])))
    page1, page2 = (p.extract_text() for p in reader.pages)
    for text in ("SUPPLIER PRICING REQUEST", "SYNTHETIC SUPPLY / SOMEWHERE  |  Page 1 of 2", "PROJECT",
                 "Synthetic Job (synthetic)", "CONTRACTOR", "Brayman Construction Co. Inc.", "SUPPLIER",
                 "Synthetic Supply - Somewhere", "REQUESTED", "October 28, 2026", "PLANS",
                 "Synthetic Plans - Aug. 20, 2026", "SCOPE", "HOW TO PRICE", "Enter Ben Unit Cost",
                 "ITEM / SPECIFICATION", "CALIBRAYT", "BEN UNIT", "1,750", "MATERIAL SUBTOTAL - PRE-HST",
                 "HST (13%)", "TOTAL INCLUDING HST", "SUPPLIER QUOTE #", "PREPARED BY", "VALID UNTIL",
                 "SUPPLIER NOTES", "Prepared with CalibraytAI"):
        assert text in page1, text
    for text in ("PRICING SUMMARY", "Page 2 of 2", "FINAL MATERIAL QUOTE - PRE-HST", "Siding package",
                 "Soffit, fascia & aluminum", "SUPPLIER ADJUSTMENTS", "SUPPLIER CONFIRMATION",
                 "Supplier Pricing Summary"):
        assert text in page2, text
    # No supplier was named that was not given; no contact line when there is no contact.
    assert "BMR" not in page1 + page2 and "Darcy" not in page1 + page2 and "·" not in page1


def test_the_calculation_is_the_approved_calculation_for_these_items_and_groups():
    data = _request()
    members = {i["key"]: i["group"] for i in data["items"]}
    script = calculation_script(KEYS, data["groups"], members, blank=False)
    assert "function n(v){ var x=parseFloat(v); return isNaN(x)?0:x; }" in script
    assert "function m(v){ return '$' + v.toFixed(2).replace(/\\B(?=(\\d{3})+(?!\\d))/g, ','); }" in script
    assert "var e=q*c;" in script and "this.getField('ext_'+k).value = c?m(e):''; total+=e;" in script
    assert "var tax=total*0.13; var grand=total+tax;" in script
    assert "this.getField('sum_siding').value=m(sums['siding']||0);" in script
    assert "this.getField('sum_alum').value=m(sums['alum']||0);" in script
    assert '"hardie": "siding"' in script and '"soffit": "alum"' in script and '"hardieacc": "siding"' in script
    assert "this.getField('summary_prepared').value=this.getField('prepared_by').value;" in script
    reader = PdfReader(BytesIO(render_supplier_pricing_request_form(data)))
    names = reader.trailer["/Root"]["/Names"]["/JavaScript"]["/Names"]
    assert names[1].get_object()["/JS"] == script


def test_the_supplier_contact_goes_under_the_supplier_on_both_pages():
    contact = dict(name="Pat Example (synthetic)", phone="613-555-0123", email="pat.example@example.invalid")
    reader, _ = _widgets(render_supplier_pricing_request_form(_request(contact=contact)))
    page1, page2 = (p.extract_text() for p in reader.pages)
    assert "Pat Example (synthetic) · 613-555-0123" in page1 and "pat.example@example.invalid" in page1
    assert "Pat Example (synthetic) · 613-555-0123 · pat.example@example.invalid" in page2


def test_the_blank_master_has_every_important_value_as_a_box_and_the_same_calculation():
    reader, widgets = _widgets(render_blank_supplier_pricing_request_form())
    for name in ("project", "supplier", "supplier_contact", "supplier_email", "requested", "plans", "scope",
                 "summary_project", "summary_supplier", "label_group1", "label_group2"):
        assert name in widgets and widgets[name]["value"] == "", name
    for n in range(1, 11):
        key = f"row{n:02d}"
        for prefix in ("item", "spec", "cqty", "unit", "qty", "cost", "ext"):
            assert f"{prefix}_{key}" in widgets
        assert widgets[f"qty_{key}"]["value"] == ""
    assert not widgets["sum_group1"]["read_only"]  # groups are typed by hand on the blank master
    page1 = reader.pages[0].extract_text()
    assert "SUPPLIER PRICING REQUEST" in page1 and "Page 1 of 2" in page1 and "HOW TO PRICE" in page1
    script = reader.trailer["/Root"]["/Names"]["/JavaScript"]["/Names"][1].get_object()["/JS"]
    assert "var tax=total*0.13;" in script and '"row01"' in script


def test_more_than_ten_items_continue_and_the_totals_follow_the_last_item():
    items = [dict(key=f"i{n:02d}", item=f"Synthetic item {n}", spec="", qty=n, unit="EA",
                  group="siding" if n % 2 else "alum") for n in range(1, 14)]
    reader, widgets = _widgets(render_supplier_pricing_request_form(_request(items=items)))
    assert len(reader.pages) == 3
    assert widgets["qty_i10"]["page"] == 0 and widgets["qty_i11"]["page"] == 1
    assert widgets["subtotal"]["page"] == 1 and widgets["summary_total"]["page"] == 2
    assert "Page 3 of 3" in reader.pages[2].extract_text()


def test_the_form_refuses_what_it_cannot_show():
    with pytest.raises(SupplierPricingFormError, match="supplier"):
        render_supplier_pricing_request_form(_request(supplier=""))
    with pytest.raises(SupplierPricingFormError, match="no group"):
        render_supplier_pricing_request_form(_request(items=[dict(_request()["items"][0], group="nope")]))
    with pytest.raises(SupplierPricingFormError, match="groups"):
        render_supplier_pricing_request_form(_request(groups=[]))
    with pytest.raises(SupplierPricingFormError, match="own simple key"):
        render_supplier_pricing_request_form(_request(items=[dict(_request()["items"][0], key="a b")]))


def test_choosing_a_supplier_fills_the_supplier_branch_and_contact():
    account = SimpleNamespace(supplier=SimpleNamespace(legal_name="Synthetic Supply", id=0),
                              supplier_location=SimpleNamespace(display_name="Somewhere"))
    project = SimpleNamespace(name="Synthetic Job (synthetic)")
    data = request_for_supplier_account(account, project=project, items=_request()["items"],
                                        groups=_request()["groups"], requested="October 28, 2026",
                                        contact={"name": "Pat Example (synthetic)", "email": "pat@example.invalid"})
    assert (data["supplier"], data["supplier_tag"]) == ("Synthetic Supply - Somewhere", "SYNTHETIC SUPPLY / SOMEWHERE")
    text = PdfReader(BytesIO(render_supplier_pricing_request_form(data))).pages[0].extract_text()
    assert "Synthetic Supply - Somewhere" in text and "Pat Example (synthetic)" in text
    assert re.search(r"SYNTHETIC SUPPLY / SOMEWHERE\s+\|\s+Page 1 of 2", text)


def test_the_approved_logos_are_the_dark_repository_logos():
    from app.services import supplier_pricing_request_form as form

    assert form.BRAYMAN_LOGO_DARK.name == "brayman-construction-logo-dark.png" and form.BRAYMAN_LOGO_DARK.is_file()
    assert form.CALIBRAYTAI_LOGO_DARK.name == "calibraytai-logo-v1-dark.png" and form.CALIBRAYTAI_LOGO_DARK.is_file()
