"""Bushel job-specific supplier pricing request. Known facts stay known."""

from __future__ import annotations

import inspect
from io import BytesIO

from pypdf import PdfReader

from app.models.canonical_material import CANONICAL_MATERIAL_SEED
from app.services.construction_model.material_readiness import (
    best_available_material_requirements,
)
from app.services import supplier_pricing_request as request_module
from app.services import supplier_pricing_request_pdf as pdf_module
from app.services.supplier_pricing_request import (
    CONTRACTOR_INPUT_LABEL,
    PUBLIC_LIST_LABEL,
    PUBLIC_PRICE_NOT_AVAILABLE,
    SOURCE_GAP_LABEL,
    SUPPLIER_AVAILABILITY_LABEL,
    SUPPLIER_PRICING_LABEL,
    SUPPLIER_PRODUCT_LABEL,
    build_job_supplier_pricing_request,
)
from app.services.supplier_pricing_request_pdf import render_supplier_pricing_request_pdf
from tests.fixtures.construction_model.bushel_proving_fixture import (
    ADDRESS,
    TREAD_BOARDS,
    VERANDA_KIT,
    proving_model,
)


def _request(**overrides):
    model = proving_model()
    readiness = best_available_material_requirements(model, tuple(CANONICAL_MATERIAL_SEED))
    payload = {
        "project_name": "Linda Bushel",
        "address": ADDRESS,
        "supplier_name": "BMR Winchester",
        "issued_on": "7 Oct 2026",
        "model": model,
        "public_prices": None,
    }
    payload.update(overrides)
    return build_job_supplier_pricing_request(readiness, **payload), readiness


def _line(request, subject):
    matches = [line for line in request["lines"] if line["subject"] == subject]
    assert len(matches) == 1
    return matches[0]


def test_bushel_request_keeps_known_facts_and_leaves_the_rest_open():
    request, _readiness = _request()
    subjects = [line["subject"] for line in request["lines"]]
    assert subjects == [
        "joist",
        "stringer",
        "post",
        "beam",
        "decking",
        "tread-boards",
        "veranda-kit",
        "guard",
        "gate",
        "pier",
    ]
    assert "stated-stick" not in subjects

    joist = _line(request, "joist")
    assert joist["quantity"] == "16"
    assert joist["unit"] == "members"
    assert "not a purchase quantity" in joist["count_note"]
    assert "Material TBD" in joist["specification"]
    assert joist["sku"] is None
    assert joist["public_price_label"] == PUBLIC_PRICE_NOT_AVAILABLE
    assert CONTRACTOR_INPUT_LABEL in joist["statuses"]
    assert SUPPLIER_PRODUCT_LABEL in joist["statuses"]
    assert SUPPLIER_PRICING_LABEL in joist["statuses"]
    assert SUPPLIER_AVAILABILITY_LABEL in joist["statuses"]
    assert "number of joists" in joist["bmr_action"]
    assert "16" in joist["contractor_action"]
    assert joist["bmr_action"] != joist["contractor_action"]

    stringer = _line(request, "stringer")
    assert stringer["quantity"] == "10"
    assert "Throat 5.0 in" in stringer["specification"]
    assert "Stair width 10 ft" in stringer["specification"]
    assert "not a lumber purchase quantity" in stringer["specification"]

    decking = _line(request, "decking")
    assert decking["quantity"] == "1"
    assert "not a board quantity" in decking["count_note"]
    assert "Width 10.0 ft" in decking["specification"]
    assert "Depth 3.0 ft" in decking["specification"]
    assert "Walking surface height 12 in" in decking["specification"]

    tread = _line(request, "tread-boards")
    assert tread["canonical_material_code"] == "CAL-LUM-5-4X6"
    assert TREAD_BOARDS in tread["material"]
    assert tread["quantity"] == "TBD"
    assert "Tread count TBD" in tread["specification"]
    assert CONTRACTOR_INPUT_LABEL in tread["statuses"]
    assert SUPPLIER_PRODUCT_LABEL in tread["statuses"]
    assert SUPPLIER_PRICING_LABEL in tread["statuses"]

    pier = _line(request, "pier")
    assert pier["quantity"] == "15"
    assert pier["unit"] == "locations"
    assert "Shaft TBD" in pier["specification"]
    assert SOURCE_GAP_LABEL in pier["statuses"]
    assert SUPPLIER_PRODUCT_LABEL in pier["statuses"]

    veranda = _line(request, "veranda-kit")
    assert veranda["material"] == VERANDA_KIT
    assert veranda["canonical_material_code"] is None
    assert "not a generic lumber identity" in veranda["specification"]
    assert veranda["quantity"] == "TBD"

    gate = _line(request, "gate")
    assert "Clear opening 42 in" in gate["specification"]
    assert gate["quantity"] == "TBD"

    joined = " ".join(line["contractor_action"] for line in request["lines"])
    supplier = " ".join(line["bmr_action"] for line in request["lines"])
    assert "Confirm joist material" in joined
    assert "Confirm joist material" not in supplier
    assert all(line["sku"] is None for line in request["lines"])
    assert all(line["public_price_is_contractor_cost"] is False for line in request["lines"])
    assert "11" not in {line["quantity"] for line in request["lines"]}
    assert "20" not in {line["quantity"] for line in request["lines"]}
    assert "132" not in {line["quantity"] for line in request["lines"]}


def test_a_supplied_public_price_stays_labeled_public():
    request, _readiness = _request(
        public_prices={"CAL-LUM-5-4X6": {"amount": "12.50", "currency": "CAD", "unit": "EA"}}
    )
    tread = _line(request, "tread-boards")
    assert tread["public_price_label"].startswith(PUBLIC_LIST_LABEL)
    assert "12.50" in tread["public_price_label"]
    assert "not the contractor price" in tread["public_price_label"]
    assert _line(request, "joist")["public_price_label"] == PUBLIC_PRICE_NOT_AVAILABLE


def test_pdf_is_fillable_and_does_not_invent_a_commercial_record():
    request, _readiness = _request()
    payload = render_supplier_pricing_request_pdf(request)
    reader = PdfReader(BytesIO(payload))
    assert len(reader.pages) >= 3
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    assert "Linda Bushel" in text
    assert "12 D'Arcy's Way" in text
    assert "BMR Winchester" in text
    assert "CAL-LUM-5-4X6" in text
    assert TREAD_BOARDS in text
    assert VERANDA_KIT in text
    assert "16" in text
    assert "BRAYMAN INFORMATION REQUIRED" in text
    assert "Darcy does not answer" in text
    assert "PUBLIC PRICE: NOT AVAILABLE" in text
    assert "2×8" not in text
    assert "798" not in text
    fields = reader.get_fields()
    assert fields["joist_sku"].get("/V") in (None, "")
    assert fields["tread-boards_net_price"].get("/V") in (None, "")
    assert "account_standard_discount" in fields
    for page in reader.pages:
        width = float(page.mediabox.width)
        height = float(page.mediabox.height)
        for annot in page.get("/Annots") or []:
            obj = annot.get_object()
            rect = [float(value) for value in obj["/Rect"]]
            assert rect[0] >= 36
            assert rect[1] >= 28
            assert rect[2] <= width - 36
            assert rect[3] <= height - 36
            assert rect[2] - rect[0] >= 70
            assert rect[3] - rect[1] >= 14
    source = inspect.getsource(request_module) + inspect.getsource(pdf_module)
    assert "EstimateLineItem" not in source
    assert "EstimateCostingSnapshot" not in source
    assert "create_material_requirement" not in source
