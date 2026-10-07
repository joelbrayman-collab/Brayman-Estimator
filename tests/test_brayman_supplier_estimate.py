"""Supplier estimate request on the approved Brayman page."""

from __future__ import annotations

import inspect
from io import BytesIO

from pypdf import PdfReader

from app.models.canonical_material import CANONICAL_MATERIAL_SEED
from app.services.construction_model.material_readiness import (
    best_available_material_requirements,
)
from app.services import brayman_supplier_estimate as estimate_module
from app.services.brayman_supplier_estimate import (
    COMPANY,
    LEGAL,
    OFFICE,
    TITLE,
    bushel_supplier_estimate_request,
    job_supplier_estimate_request,
    render_supplier_estimate_request,
)
from tests.fixtures.construction_model.bushel_proving_fixture import (
    TREAD_BOARDS,
    VERANDA_KIT,
    proving_model,
)


def _bushel_pdf():
    model = proving_model()
    readiness = best_available_material_requirements(model, tuple(CANONICAL_MATERIAL_SEED))
    document = bushel_supplier_estimate_request(readiness, model)
    return document, render_supplier_estimate_request(**document)


def test_bushel_lines_keep_known_facts_and_do_not_price_them():
    document, _payload = _bushel_pdf()
    items = [row["item"] for row in document["rows"]]
    joined = " ".join(items)
    assert any(row["item"].startswith("Joists.") and "16 member stations" in row["item"] for row in document["rows"])
    assert any("10 member stations" in row["item"] and "Throat 5.0 in" in row["item"] for row in document["rows"])
    assert any("Stair width 10 ft" in row["item"] for row in document["rows"])
    assert any(f"CAL-LUM-5-4X6 — {TREAD_BOARDS}" in row["item"] for row in document["rows"])
    assert "Width 10.0 ft" in joined
    assert "Depth 3.0 ft" in joined
    assert "Height 12 in" in joined
    assert "15 locations" in joined
    assert VERANDA_KIT in joined
    assert "Clear opening 42 in" in joined
    assert all(row["qty"] == "TBD" for row in document["rows"])
    assert all("BRAYMAN TO CONFIRM QTY" in row["note"] for row in document["rows"])
    assert "798" not in joined
    assert "2×8" not in joined
    assert document["project_name"] == "Linda Bushel"
    assert document["supplier_name"] == "BMR Winchester"


def test_pdf_matches_the_brayman_page_and_the_fields_are_fillable():
    document, payload = _bushel_pdf()
    reader = PdfReader(BytesIO(payload))
    assert len(reader.pages) >= 1
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    assert COMPANY in text
    assert LEGAL in text
    assert OFFICE in text
    assert TITLE in text
    assert "12 D'Arcy's Way, Kemptville, ON" in text
    assert "Please return this completed estimate request" in text
    assert "CalibraytAI" not in text
    assert "CanonicalMaterial" not in text
    assert "MaterialRequirement" not in text
    assert "Cost Engine" not in text
    fields = reader.get_fields()
    assert fields["unit_price_01"].get("/V") in (None, "")
    assert fields["line_price_01"].get("/V") in (None, "")
    assert fields["sku_01"].get("/V") in (None, "")
    assert "BRAYMAN TO CONFIRM QTY" in fields["note_01"].get("/V")
    assert "bmr_contact" in fields
    assert "general_notes" in fields
    table_heights = []
    for page in reader.pages:
        width = float(page.mediabox.width)
        height = float(page.mediabox.height)
        assert width == 792
        assert height == 612
        rects = []
        for annot in page.get("/Annots") or []:
            obj = annot.get_object()
            name = str(obj.get("/T"))
            rect = [float(value) for value in obj["/Rect"]]
            assert rect[0] >= 28
            assert rect[1] >= 28
            assert rect[2] <= width - 28
            assert rect[3] <= height - 36
            assert rect[2] - rect[0] >= 40
            rects.append((name, rect))
            if name.startswith(("unit_price_", "line_price_", "sku_", "note_")):
                table_heights.append(round(rect[3] - rect[1], 2))
        for index, (name, rect) in enumerate(rects):
            for other_name, other in rects[index + 1:]:
                overlap_x = min(rect[2], other[2]) - max(rect[0], other[0])
                overlap_y = min(rect[3], other[3]) - max(rect[1], other[1])
                assert overlap_x <= 1 or overlap_y <= 1, (name, other_name)
    assert table_heights
    assert len(set(table_heights)) == 1
    source = inspect.getsource(estimate_module)
    assert "EstimateLineItem" not in source
    assert "EstimateCostingSnapshot" not in source
    assert len(document["rows"]) == 10


def test_the_page_can_carry_another_project():
    payload = render_supplier_estimate_request(
        project_name="Sample Project",
        project_address="1 Example Road",
        supplier_name="BMR Winchester",
        issued_on="7 October 2026",
        intro=("Please price the line below.",),
        rows=({"number": 1, "item": "One sample line.", "qty": "TBD", "note": "CONFIRM PRODUCT."},),
    )
    text = "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(payload)).pages)
    assert "Sample Project" in text
    assert "Linda Bushel" not in text
    assert TITLE in text


def test_a_job_fills_the_footer_and_leaves_price_blank():
    document = job_supplier_estimate_request(
        project_name="Harbour Shed",
        project_address="9 Mill Street, Merrickville, ON",
        supplier_name="East Yard Lumber",
        issued_on="7 October 2026",
        lines=({"item": "CAL-LUM-2X6-12 — 2x6 board. Unit EA.", "qty": "10", "note": ""},),
    )
    payload = render_supplier_estimate_request(**document)
    reader = PdfReader(BytesIO(payload))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    assert "Harbour Shed" in text
    assert "9 Mill Street, Merrickville, ON" in text
    assert "East Yard Lumber" in text
    assert "Linda Bushel" not in text
    assert "12 D'Arcy" not in text
    assert "Supplier contact" in text
    fields = reader.get_fields()
    assert fields["unit_price_01"].get("/V") in (None, "")
    assert fields["sku_01"].get("/V") in (None, "")
