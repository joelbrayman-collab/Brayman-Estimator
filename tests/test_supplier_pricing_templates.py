"""The Supplier Pricing Request template library (Joel, 29 Oct 2026: "save this template for Hardie Board
estimates ... a library of these"). Synthetic job data; the measurements are the first Hardie job's, which the
template must reproduce exactly."""

from __future__ import annotations

import json
from io import BytesIO

import pytest
from pypdf import PdfReader

from app.services.supplier_pricing_request_form import render_supplier_pricing_request_form
from app.services.supplier_pricing_templates import (
    LIBRARY, SupplierPricingTemplateError, list_templates, load_template, quantities, request_from_template)

HARDIE = "hardie-vertical-aluminum-v1"
MEASURED = {"siding_sf": 1750, "batten_lf": 1313, "joint_lf": 200, "trim_joint_lf": 600, "soffit_sf": 400,
            "fascia_lf": 315, "corner_lf": 125, "window_trim_lf": 205, "door_trim_lf": 115, "drip_lf": 70,
            "freeze_lf": 125, "jchannel_lf": 315}
# The quantities and specifications sent for that job (BY THE PIECE form, 29 Oct 2026).
EXPECTED = [
    ("hpanel", 61, "PC", "Cedarmill, Arctic White - 4x8 sheet (1,750 SF + 10%)"),
    ("hbatten", 121, "PC", "Arctic White - 12 ft, 16 in. O/C (1,313 LF + 10%)"),
    ("hnails", 3, "BOX", "Ring shank, 5 lb box - ~4,500 nails (panels + battens)"),
    ("hflash", 22, "PC", "10 ft - ~200 LF of panel joints + 10%"),
    ("hcaulk", 24, "TUBE", "Arctic White - ~600 LF of trim joints, 25 LF/tube"),
    ("htouch", 1, "KIT", "Arctic White"),
    ("soffit", 28, "PC", "Gentek - Black - 16 in. x 12 ft (400 SF + 10%)"),
    ("fascia", 29, "PC", "Gentek - Black - 12 ft (315 LF + 10%)"),
    ("corner", 14, "PC", "Gentek - White - 10 ft (125 LF + 10%)"),
    ("wtrim", 19, "PC", "Gentek - White, 3-1/2 in. - 12 ft (205 LF + 10%)"),
    ("dtrim", 11, "PC", "Gentek - White, 3-1/2 in. - 12 ft (115 LF + 10%)"),
    ("drip", 8, "PC", "Aluminum - 10 ft (70 LF + 10%)"),
    ("freeze", 12, "PC", "Gentek - White - 12 ft (125 LF + 10%)"),
    ("jchan", 29, "PC", "Black - 12 ft (315 LF at wall + 10%)"),
    ("anails", 4, "BOX", "Colour-matched, 1 lb box - ~1,100 nails"),
    ("screws", 2, "BOX", "1 lb box - 28 soffit panels"),
]


def _job(**over):
    return request_from_template(HARDIE, dict(MEASURED), project="REF-SYN-HARDIE", supplier="Synthetic Supply",
                                 supplier_tag="SYNTHETIC", requested="October 29, 2026", **over)


def test_the_library_lists_the_hardie_template():
    assert {"key": HARDIE, "title": "Hardie vertical siding + aluminum soffit, fascia & trim", "trade": "Siding",
            "scope": "Siding / aluminum package"} in list_templates()


def test_the_hardie_template_reproduces_the_first_jobs_quantities_and_specs_exactly():
    request = _job()
    assert [(i["key"], i["qty"], i["unit"], i["spec"]) for i in request["items"]] == EXPECTED
    assert [g["label"] for g in request["groups"]] == ["Siding package", "Soffit, fascia & aluminum"]
    assert request["scope"] == "Siding / aluminum package"


def test_quantities_round_up_and_follow_the_measurements():
    q = quantities(load_template(HARDIE), dict(MEASURED, siding_sf=1745.5, soffit_sf=0))
    assert q["hpanel"] == 61 and q["soffit"] == 0 and q["screws"] == 0
    assert quantities(load_template(HARDIE), dict(MEASURED, siding_sf=3200))["hpanel"] == 110  # 3,520 / 32 exactly


def test_choices_change_the_colours_and_nothing_else():
    request = _job(choices={"siding_colour": "Iron Gray"})
    assert request["items"][0]["spec"] == "Cedarmill, Iron Gray - 4x8 sheet (1,750 SF + 10%)"
    assert [i["qty"] for i in request["items"]] == [e[1] for e in EXPECTED]
    with pytest.raises(SupplierPricingTemplateError):
        _job(choices={"price": "1"})


def test_a_missing_extra_or_bad_measurement_is_refused():
    for bad in ({k: v for k, v in MEASURED.items() if k != "drip_lf"}, dict(MEASURED, deck_sf=10),
                dict(MEASURED, drip_lf="lots"), dict(MEASURED, drip_lf=-1)):
        with pytest.raises(SupplierPricingTemplateError):
            quantities(load_template(HARDIE), bad)
    with pytest.raises(SupplierPricingTemplateError):
        load_template("../secrets")


def test_a_template_fills_the_approved_form_with_its_quantities():
    reader = PdfReader(BytesIO(render_supplier_pricing_request_form(_job())))
    fields = reader.get_fields()
    assert {k: str(fields[f"qty_{k}"].get("/V")) for k, *_ in EXPECTED} == {k: str(q) for k, q, *_ in EXPECTED}
    assert "HardiePanel vertical siding" in reader.pages[0].extract_text()


def test_templates_hold_no_prices_client_or_supplier():
    for path in LIBRARY.glob("*.json"):
        text = path.read_text().lower()
        for word in ("price\"", "cost", "$", "client", "supplier\""):
            assert word not in text, f"{path.name} holds {word}"
        assert json.loads(path.read_text())["key"] == path.stem
